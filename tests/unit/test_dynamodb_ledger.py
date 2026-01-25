"""
Unit tests for DynamoDB ledger module.
"""

import pytest
import time
from app.utils.dynamodb_ledger import DynamoDBLedger, LedgerEntry, MockDynamoDB


class TestMockDynamoDB:
    """Test MockDynamoDB implementation."""
    
    def test_put_and_get_item(self):
        """Test storing and retrieving items."""
        mock_db = MockDynamoDB()
        
        item = {
            'book_id': 'test123',
            'status': 'processing',
            'artist': 'Test Artist'
        }
        
        mock_db.put_item('test-table', item)
        retrieved = mock_db.get_item('test-table', {'book_id': 'test123'})
        
        assert retrieved == item
        assert retrieved['status'] == 'processing'
    
    def test_get_nonexistent_item(self):
        """Test retrieving non-existent item."""
        mock_db = MockDynamoDB()
        
        retrieved = mock_db.get_item('test-table', {'book_id': 'nonexistent'})
        
        assert retrieved is None
    
    def test_query_with_filter(self):
        """Test querying items with filter."""
        mock_db = MockDynamoDB()
        
        # Add multiple items
        mock_db.put_item('test-table', {'book_id': '1', 'status': 'success'})
        mock_db.put_item('test-table', {'book_id': '2', 'status': 'failed'})
        mock_db.put_item('test-table', {'book_id': '3', 'status': 'success'})
        
        results = mock_db.query('test-table', '', filter_status='success')
        
        assert len(results) == 2
        assert all(item['status'] == 'success' for item in results)


class TestDynamoDBLedger:
    """Test DynamoDBLedger in local mode."""
    
    @pytest.fixture
    def ledger(self):
        """Create DynamoDB ledger in local mode."""
        return DynamoDBLedger(local_mode=True)
    
    def test_generate_book_id(self, ledger):
        """Test book ID generation."""
        s3_uri = 's3://bucket/SheetMusic/Artist/books/Book.pdf'
        book_id = ledger.generate_book_id(s3_uri)
        
        # Should be consistent
        assert book_id == ledger.generate_book_id(s3_uri)
        
        # Should be 16 characters (truncated SHA256)
        assert len(book_id) == 16
        
        # Different URIs should produce different IDs
        other_uri = 's3://bucket/SheetMusic/Artist/books/Other.pdf'
        assert book_id != ledger.generate_book_id(other_uri)
    
    def test_record_processing_start(self, ledger):
        """Test recording processing start."""
        s3_uri = 's3://bucket/SheetMusic/Beatles/books/AbbeyRoad.pdf'
        
        book_id = ledger.record_processing_start(
            source_pdf_uri=s3_uri,
            artist='Beatles',
            book_name='Abbey Road',
            execution_arn='arn:aws:states:us-east-1:123456789012:execution:test'
        )
        
        assert book_id is not None
        assert len(book_id) == 16
        
        # Verify entry was created
        entry = ledger.get_entry(book_id)
        assert entry is not None
        assert entry['status'] == 'processing'
        assert entry['artist'] == 'Beatles'
        assert entry['book_name'] == 'Abbey Road'
        assert entry['source_pdf_uri'] == s3_uri
    
    def test_check_already_processed_false(self, ledger):
        """Test checking unprocessed book."""
        book_id = 'nonexistent123'
        
        result = ledger.check_already_processed(book_id)
        
        assert result is False
    
    def test_check_already_processed_true(self, ledger):
        """Test checking successfully processed book."""
        s3_uri = 's3://bucket/SheetMusic/Beatles/books/AbbeyRoad.pdf'
        
        # Record start
        book_id = ledger.record_processing_start(
            source_pdf_uri=s3_uri,
            artist='Beatles',
            book_name='Abbey Road'
        )
        
        # Record success
        ledger.record_processing_complete(
            book_id=book_id,
            status='success',
            songs_extracted=12
        )
        
        # Check if processed
        result = ledger.check_already_processed(book_id)
        
        assert result is True
    
    def test_check_already_processed_failed(self, ledger):
        """Test checking failed book (should return False to allow retry)."""
        s3_uri = 's3://bucket/SheetMusic/Beatles/books/AbbeyRoad.pdf'
        
        # Record start
        book_id = ledger.record_processing_start(
            source_pdf_uri=s3_uri,
            artist='Beatles',
            book_name='Abbey Road'
        )
        
        # Record failure
        ledger.record_processing_complete(
            book_id=book_id,
            status='failed',
            error_message='Test error'
        )
        
        # Check if processed (should be False to allow retry)
        result = ledger.check_already_processed(book_id)
        
        assert result is False
    
    def test_record_processing_complete_success(self, ledger):
        """Test recording successful completion."""
        s3_uri = 's3://bucket/SheetMusic/Beatles/books/AbbeyRoad.pdf'
        
        # Record start
        book_id = ledger.record_processing_start(
            source_pdf_uri=s3_uri,
            artist='Beatles',
            book_name='Abbey Road'
        )
        
        # Record success
        ledger.record_processing_complete(
            book_id=book_id,
            status='success',
            manifest_uri='s3://bucket/output/manifest.json',
            songs_extracted=12,
            processing_duration_seconds=245.5,
            cost_usd=0.15
        )
        
        # Verify entry
        entry = ledger.get_entry(book_id)
        assert entry['status'] == 'success'
        assert entry['manifest_uri'] == 's3://bucket/output/manifest.json'
        assert entry['songs_extracted'] == 12
        assert entry['processing_duration_seconds'] == 245.5
        assert entry['cost_usd'] == 0.15
    
    def test_record_processing_complete_failed(self, ledger):
        """Test recording failed completion."""
        s3_uri = 's3://bucket/SheetMusic/Beatles/books/AbbeyRoad.pdf'
        
        # Record start
        book_id = ledger.record_processing_start(
            source_pdf_uri=s3_uri,
            artist='Beatles',
            book_name='Abbey Road'
        )
        
        # Record failure
        ledger.record_processing_complete(
            book_id=book_id,
            status='failed',
            error_message='TOC extraction failed'
        )
        
        # Verify entry
        entry = ledger.get_entry(book_id)
        assert entry['status'] == 'failed'
        assert entry['error_message'] == 'TOC extraction failed'
    
    def test_record_processing_complete_manual_review(self, ledger):
        """Test recording manual review status."""
        s3_uri = 's3://bucket/SheetMusic/Beatles/books/AbbeyRoad.pdf'
        
        # Record start
        book_id = ledger.record_processing_start(
            source_pdf_uri=s3_uri,
            artist='Beatles',
            book_name='Abbey Road'
        )
        
        # Record manual review
        ledger.record_processing_complete(
            book_id=book_id,
            status='manual_review',
            songs_extracted=8,
            error_message='Only 8 of 12 songs extracted'
        )
        
        # Verify entry
        entry = ledger.get_entry(book_id)
        assert entry['status'] == 'manual_review'
        assert entry['songs_extracted'] == 8
    
    def test_record_processing_complete_invalid_status(self, ledger):
        """Test recording with invalid status."""
        s3_uri = 's3://bucket/SheetMusic/Beatles/books/AbbeyRoad.pdf'
        
        book_id = ledger.record_processing_start(
            source_pdf_uri=s3_uri,
            artist='Beatles',
            book_name='Abbey Road'
        )
        
        with pytest.raises(ValueError, match='Invalid status'):
            ledger.record_processing_complete(
                book_id=book_id,
                status='invalid_status'
            )
    
    def test_query_by_status(self, ledger):
        """Test querying entries by status."""
        # Create multiple entries
        for i in range(3):
            s3_uri = f's3://bucket/SheetMusic/Artist/books/Book{i}.pdf'
            book_id = ledger.record_processing_start(
                source_pdf_uri=s3_uri,
                artist='Artist',
                book_name=f'Book{i}'
            )
            
            status = 'success' if i < 2 else 'failed'
            ledger.record_processing_complete(
                book_id=book_id,
                status=status
            )
        
        # Query successful entries
        success_entries = ledger.query_by_status('success')
        assert len(success_entries) == 2
        
        # Query failed entries
        failed_entries = ledger.query_by_status('failed')
        assert len(failed_entries) == 1


class TestLedgerEntry:
    """Test LedgerEntry dataclass."""
    
    def test_ledger_entry_creation(self):
        """Test creating LedgerEntry instance."""
        entry = LedgerEntry(
            book_id='test123',
            processing_timestamp=int(time.time()),
            status='processing',
            source_pdf_uri='s3://bucket/test.pdf',
            artist='Test Artist',
            book_name='Test Book'
        )
        
        assert entry.book_id == 'test123'
        assert entry.status == 'processing'
        assert entry.artist == 'Test Artist'
    
    def test_ledger_entry_with_optional_fields(self):
        """Test LedgerEntry with optional fields."""
        entry = LedgerEntry(
            book_id='test123',
            processing_timestamp=int(time.time()),
            status='success',
            source_pdf_uri='s3://bucket/test.pdf',
            artist='Test Artist',
            book_name='Test Book',
            manifest_uri='s3://bucket/manifest.json',
            songs_extracted=10,
            processing_duration_seconds=120.5,
            cost_usd=0.25
        )
        
        assert entry.manifest_uri == 's3://bucket/manifest.json'
        assert entry.songs_extracted == 10
        assert entry.processing_duration_seconds == 120.5
        assert entry.cost_usd == 0.25
