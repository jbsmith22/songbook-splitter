"""
Unit tests for S3 utilities module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from app.utils.s3_utils import S3Utils, S3Object


class TestS3UtilsLocalMode:
    """Test S3Utils in local mode."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def sample_structure(self, temp_dir):
        """Create sample directory structure with PDFs."""
        base = Path(temp_dir)
        
        # Create structure: SheetMusic/<Artist>/books/*.pdf
        artists = ['Beatles', 'Elvis', 'Various Artists']
        for artist in artists:
            artist_path = base / 'SheetMusic' / artist / 'books'
            artist_path.mkdir(parents=True, exist_ok=True)
            
            # Create sample PDF files
            (artist_path / f'{artist}_Book1.pdf').write_text('fake pdf content')
            (artist_path / f'{artist}_Book2.pdf').write_text('fake pdf content')
        
        # Create some non-matching files
        (base / 'SheetMusic' / 'Beatles' / 'not_in_books.pdf').write_text('fake pdf')
        other_dir = base / 'Other'
        other_dir.mkdir(parents=True, exist_ok=True)
        (other_dir / 'file.pdf').write_text('fake pdf')
        
        return base
    
    def test_list_pdfs_local_mode(self, sample_structure):
        """Test listing PDFs in local mode."""
        s3_utils = S3Utils(local_mode=True, local_base_path=str(sample_structure))
        pdfs = s3_utils.list_pdfs(bucket='local', prefix='SheetMusic/')
        
        # Should find 6 PDFs (3 artists × 2 books)
        assert len(pdfs) == 6
        
        # Check structure
        for pdf in pdfs:
            assert pdf.bucket == 'local'
            assert pdf.artist in ['Beatles', 'Elvis', 'Various Artists']
            assert pdf.book_name.endswith('_Book1') or pdf.book_name.endswith('_Book2')
            assert pdf.size > 0
    
    def test_list_pdfs_pattern_matching(self, sample_structure):
        """Test pattern matching for PDF discovery."""
        s3_utils = S3Utils(local_mode=True, local_base_path=str(sample_structure))
        pdfs = s3_utils.list_pdfs(bucket='local', prefix='SheetMusic/')
        
        # All PDFs should match the pattern
        for pdf in pdfs:
            assert 'SheetMusic/' in pdf.key
            assert '/books/' in pdf.key
            assert pdf.key.endswith('.pdf')
    
    def test_list_pdfs_empty_directory(self, temp_dir):
        """Test listing PDFs from empty directory."""
        s3_utils = S3Utils(local_mode=True, local_base_path=temp_dir)
        pdfs = s3_utils.list_pdfs(bucket='local', prefix='SheetMusic/')
        
        assert len(pdfs) == 0
    
    def test_download_file_local_mode(self, sample_structure, temp_dir):
        """Test downloading (copying) file in local mode."""
        s3_utils = S3Utils(local_mode=True, local_base_path=str(sample_structure))
        
        source_key = 'SheetMusic/Beatles/books/Beatles_Book1.pdf'
        dest_path = Path(temp_dir) / 'downloaded.pdf'
        
        result = s3_utils.download_file('local', source_key, str(dest_path))
        
        assert Path(result).exists()
        assert Path(result).read_text() == 'fake pdf content'
    
    def test_upload_file_local_mode(self, sample_structure, temp_dir):
        """Test uploading (copying) file in local mode."""
        # Create output directory
        output_dir = Path(temp_dir) / 'output'
        output_dir.mkdir(exist_ok=True)
        
        s3_utils = S3Utils(local_mode=True, local_base_path=str(sample_structure))
        
        # Create a test file
        test_file = Path(temp_dir) / 'test.pdf'
        test_file.write_text('test content')
        
        result = s3_utils.upload_file(str(test_file), 'local', 'output/test.pdf')
        
        assert Path(result).exists()
    
    def test_write_bytes_local_mode(self, sample_structure):
        """Test writing bytes directly in local mode."""
        s3_utils = S3Utils(local_mode=True, local_base_path=str(sample_structure))
        
        test_data = b'test binary data'
        result = s3_utils.write_bytes(test_data, 'local', 'output/test.bin')
        
        assert Path(result).exists()
        assert Path(result).read_bytes() == test_data


class TestS3Object:
    """Test S3Object dataclass."""
    
    def test_s3_object_creation(self):
        """Test creating S3Object instance."""
        obj = S3Object(
            bucket='test-bucket',
            key='SheetMusic/Beatles/books/Abbey_Road.pdf',
            artist='Beatles',
            book_name='Abbey_Road',
            size=1024,
            last_modified='2024-01-01T00:00:00'
        )
        
        assert obj.bucket == 'test-bucket'
        assert obj.artist == 'Beatles'
        assert obj.book_name == 'Abbey_Road'
        assert obj.size == 1024
    
    def test_s3_object_defaults(self):
        """Test S3Object with default values."""
        obj = S3Object(
            bucket='test-bucket',
            key='test.pdf',
            artist='Artist',
            book_name='Book'
        )
        
        assert obj.size == 0
        assert obj.last_modified is None
