"""
ECS Task Entry Points - Entry points for containerized tasks.

Each entry point:
- Reads input from environment variables or stdin
- Executes the corresponding service
- Writes output to S3
- Handles cleanup
"""

import json
import os
import sys
import logging
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def toc_discovery_task():
    """
    TOC Discovery ECS task entry point.
    
    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - OUTPUT_BUCKET: S3 bucket for output
    - MAX_PAGES: Maximum pages to scan (default: 20)
    """
    from app.services.toc_discovery import TOCDiscoveryService
    from app.utils.s3_utils import S3Utils
    
    logger.info("Starting TOC Discovery task")
    
    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    max_pages = int(os.environ.get('MAX_PAGES', '20'))
    
    if not all([book_id, source_pdf_uri, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    try:
        # Download PDF from S3
        s3_utils = S3Utils()
        bucket, key = parse_s3_uri(source_pdf_uri)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            s3_utils.download_file(bucket, key, pdf_path)
            
            # Run TOC discovery
            service = TOCDiscoveryService()
            result = service.discover_toc(pdf_path, max_pages)
            
            # Write result to S3
            output_key = f"artifacts/{book_id}/toc_discovery.json"
            result_json = json.dumps({
                'toc_pages': result.toc_pages,
                'extracted_text': result.extracted_text,
                'confidence_scores': result.confidence_scores
            })
            s3_utils.write_bytes(result_json.encode(), output_bucket, output_key)
            
            logger.info(f"TOC Discovery complete. Found {len(result.toc_pages)} pages")
            
            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'toc_pages': result.toc_pages,
                'output_uri': f"s3://{output_bucket}/{output_key}"
            }))
            
    except Exception as e:
        logger.error(f"TOC Discovery failed: {e}", exc_info=True)
        sys.exit(1)


def toc_parser_task():
    """
    TOC Parser ECS task entry point.
    
    Environment variables:
    - BOOK_ID: Unique book identifier
    - TOC_DISCOVERY_URI: S3 URI of TOC discovery JSON
    - ARTIST: Book artist
    - BOOK_NAME: Book name
    - OUTPUT_BUCKET: S3 bucket for output
    """
    from app.services.toc_parser import TOCParser
    from app.utils.s3_utils import S3Utils
    
    logger.info("Starting TOC Parser task")
    
    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    toc_discovery_uri = os.environ.get('TOC_DISCOVERY_URI')
    artist = os.environ.get('ARTIST')
    book_name = os.environ.get('BOOK_NAME')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    
    if not all([book_id, toc_discovery_uri, artist, book_name, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    try:
        s3_utils = S3Utils()
        
        # Download TOC discovery results
        bucket, key = parse_s3_uri(toc_discovery_uri)
        toc_discovery_json = s3_utils.read_bytes(bucket, key).decode('utf-8')
        toc_discovery_data = json.loads(toc_discovery_json)
        
        # Extract TOC text from discovery results
        toc_text = '\n'.join(toc_discovery_data.get('extracted_text', {}).values())
        
        # Parse TOC
        parser = TOCParser()
        book_metadata = {'artist': artist, 'book_name': book_name}
        result = parser.parse_toc(toc_text, book_metadata)
        
        # Write result to S3
        output_key = f"artifacts/{book_id}/toc_parse.json"
        result_json = json.dumps({
            'entries': [
                {
                    'song_title': e.song_title,
                    'page_number': e.page_number,
                    'artist': e.artist,
                    'confidence': e.confidence
                }
                for e in result.entries
            ],
            'extraction_method': result.extraction_method,
            'confidence': result.confidence,
            'artist_overrides': result.artist_overrides
        })
        s3_utils.write_bytes(result_json.encode(), output_bucket, output_key)
        
        logger.info(f"TOC Parser complete. Parsed {len(result.entries)} entries")
        
        # Output result for Step Functions
        print(json.dumps({
            'book_id': book_id,
            'entry_count': len(result.entries),
            'extraction_method': result.extraction_method,
            'output_uri': f"s3://{output_bucket}/{output_key}"
        }))
        
    except Exception as e:
        logger.error(f"TOC Parser failed: {e}", exc_info=True)
        sys.exit(1)


def song_verifier_task():
    """
    Song Verifier ECS task entry point.
    
    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - PAGE_MAPPING_URI: S3 URI of page mapping JSON
    - OUTPUT_BUCKET: S3 bucket for output
    """
    from app.services.song_verifier import SongVerifierService
    from app.utils.s3_utils import S3Utils
    from app.models import SongLocation
    
    logger.info("Starting Song Verifier task")
    
    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    page_mapping_uri = os.environ.get('PAGE_MAPPING_URI')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    
    if not all([book_id, source_pdf_uri, page_mapping_uri, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    try:
        s3_utils = S3Utils()
        
        # Download PDF and page mapping
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            bucket, key = parse_s3_uri(source_pdf_uri)
            s3_utils.download_file(bucket, key, pdf_path)
            
            # Load page mapping
            bucket, key = parse_s3_uri(page_mapping_uri)
            page_mapping_json = s3_utils.read_bytes(bucket, key).decode('utf-8')
            page_mapping_data = json.loads(page_mapping_json)
            
            # Convert to SongLocation objects
            song_locations = [
                SongLocation(
                    song_title=entry['song_title'],
                    toc_page_number=entry['toc_page_number'],
                    pdf_page_number=entry['pdf_page_number'],
                    artist=entry.get('artist', '')
                )
                for entry in page_mapping_data.get('mappings', [])
            ]
            
            # Run verification
            service = SongVerifierService()
            verified_songs = service.verify_song_starts(pdf_path, song_locations)
            
            # Write result to S3
            output_key = f"artifacts/{book_id}/verified_songs.json"
            result_json = json.dumps({
                'verified_songs': [
                    {
                        'song_title': v.song_title,
                        'start_page': v.start_page,
                        'end_page': v.end_page,
                        'artist': v.artist,
                        'verification_confidence': v.verification_confidence,
                        'verification_method': v.verification_method
                    }
                    for v in verified_songs
                ]
            })
            s3_utils.write_bytes(result_json.encode(), output_bucket, output_key)
            
            logger.info(f"Song Verifier complete. Verified {len(verified_songs)} songs")
            
            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'verified_count': len(verified_songs),
                'output_uri': f"s3://{output_bucket}/{output_key}"
            }))
            
    except Exception as e:
        logger.error(f"Song Verifier failed: {e}", exc_info=True)
        sys.exit(1)


def pdf_splitter_task():
    """
    PDF Splitter ECS task entry point.
    
    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - VERIFIED_SONGS_URI: S3 URI of verified songs JSON
    - OUTPUT_BUCKET: S3 bucket for output
    - ARTIST: Book artist
    - BOOK_NAME: Book name
    """
    from app.services.pdf_splitter import PDFSplitterService
    from app.utils.s3_utils import S3Utils
    from app.models import PageRange
    
    logger.info("Starting PDF Splitter task")
    
    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    verified_songs_uri = os.environ.get('VERIFIED_SONGS_URI')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    artist = os.environ.get('ARTIST')
    book_name = os.environ.get('BOOK_NAME')
    
    if not all([book_id, source_pdf_uri, verified_songs_uri, output_bucket, artist, book_name]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    try:
        s3_utils = S3Utils()
        
        # Download PDF and verified songs
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            bucket, key = parse_s3_uri(source_pdf_uri)
            s3_utils.download_file(bucket, key, pdf_path)
            
            # Load verified songs
            bucket, key = parse_s3_uri(verified_songs_uri)
            verified_songs_json = s3_utils.read_bytes(bucket, key).decode('utf-8')
            verified_songs_data = json.loads(verified_songs_json)
            
            # Convert to PageRange objects
            page_ranges = [
                PageRange(
                    song_title=song['song_title'],
                    start_page=song['start_page'],
                    end_page=song['end_page'],
                    artist=song.get('artist', artist)
                )
                for song in verified_songs_data.get('verified_songs', [])
            ]
            
            # Run splitting
            service = PDFSplitterService(output_bucket=output_bucket)
            output_files = service.split_pdf(pdf_path, page_ranges, artist, book_name)
            
            # Write output files list to S3
            output_key = f"artifacts/{book_id}/output_files.json"
            result_json = json.dumps({
                'output_files': [
                    {
                        'song_title': f.song_title,
                        's3_uri': f.s3_uri,
                        'local_path': f.local_path,
                        'file_size_bytes': f.file_size_bytes,
                        'page_count': f.page_count
                    }
                    for f in output_files
                ]
            })
            s3_utils.write_bytes(result_json.encode(), output_bucket, output_key)
            
            logger.info(f"PDF Splitter complete. Created {len(output_files)} files")
            
            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'files_created': len(output_files),
                'output_uri': f"s3://{output_bucket}/{output_key}"
            }))
            
    except Exception as e:
        logger.error(f"PDF Splitter failed: {e}", exc_info=True)
        sys.exit(1)


def page_mapper_task():
    """
    Page Mapper ECS task entry point.
    
    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - TOC_PARSE_URI: S3 URI of TOC parse JSON
    - OUTPUT_BUCKET: S3 bucket for output
    """
    from app.services.page_mapper import PageMapperService
    from app.utils.s3_utils import S3Utils
    from app.models import TOCEntry
    
    logger.info("Starting Page Mapper task")
    
    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    toc_parse_uri = os.environ.get('TOC_PARSE_URI')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    
    if not all([book_id, source_pdf_uri, toc_parse_uri, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    try:
        s3_utils = S3Utils()
        
        # Download PDF and TOC parse results
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            bucket, key = parse_s3_uri(source_pdf_uri)
            s3_utils.download_file(bucket, key, pdf_path)
            
            # Load TOC parse results
            bucket, key = parse_s3_uri(toc_parse_uri)
            toc_parse_json = s3_utils.read_bytes(bucket, key).decode('utf-8')
            toc_parse_data = json.loads(toc_parse_json)
            
            # Convert to TOCEntry objects
            toc_entries = [
                TOCEntry(
                    song_title=entry['song_title'],
                    page_number=entry['page_number'],
                    artist=entry.get('artist', ''),
                    confidence=entry.get('confidence', 1.0)
                )
                for entry in toc_parse_data.get('entries', [])
            ]
            
            # Run page mapping
            service = PageMapperService()
            page_mapping = service.map_toc_to_pdf_pages(pdf_path, toc_entries)
            
            # Write result to S3
            output_key = f"artifacts/{book_id}/page_mapping.json"
            result_json = json.dumps({
                'mappings': [
                    {
                        'song_title': m.song_title,
                        'toc_page_number': m.toc_page_number,
                        'pdf_page_number': m.pdf_page_number,
                        'confidence': m.confidence,
                        'artist': m.artist
                    }
                    for m in page_mapping.mappings
                ],
                'unmapped_songs': page_mapping.unmapped_songs,
                'mapping_method': page_mapping.mapping_method
            })
            s3_utils.write_bytes(result_json.encode(), output_bucket, output_key)
            
            logger.info(f"Page Mapper complete. Mapped {len(page_mapping.mappings)} songs")
            
            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'mapped_count': len(page_mapping.mappings),
                'unmapped_count': len(page_mapping.unmapped_songs),
                'output_uri': f"s3://{output_bucket}/{output_key}"
            }))
            
    except Exception as e:
        logger.error(f"Page Mapper failed: {e}", exc_info=True)
        sys.exit(1)


def manifest_generator_task():
    """
    Manifest Generator ECS task entry point.
    
    Environment variables:
    - BOOK_ID: Unique book identifier
    - ARTIST: Book artist
    - BOOK_NAME: Book name
    - OUTPUT_BUCKET: S3 bucket for output
    """
    from app.services.manifest_generator import ManifestGeneratorService
    from app.utils.s3_utils import S3Utils
    
    logger.info("Starting Manifest Generator task")
    
    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    artist = os.environ.get('ARTIST')
    book_name = os.environ.get('BOOK_NAME')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    
    if not all([book_id, artist, book_name, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    try:
        s3_utils = S3Utils()
        
        # Load all artifacts from S3
        artifacts_prefix = f"artifacts/{book_id}/"
        
        # Download TOC discovery
        toc_discovery_json = s3_utils.read_bytes(output_bucket, f"{artifacts_prefix}toc_discovery.json").decode('utf-8')
        toc_discovery_data = json.loads(toc_discovery_json)
        
        # Download TOC parse
        toc_parse_json = s3_utils.read_bytes(output_bucket, f"{artifacts_prefix}toc_parse.json").decode('utf-8')
        toc_parse_data = json.loads(toc_parse_json)
        
        # Download page mapping
        page_mapping_json = s3_utils.read_bytes(output_bucket, f"{artifacts_prefix}page_mapping.json").decode('utf-8')
        page_mapping_data = json.loads(page_mapping_json)
        
        # Download output files
        output_files_json = s3_utils.read_bytes(output_bucket, f"{artifacts_prefix}output_files.json").decode('utf-8')
        output_files_data = json.loads(output_files_json)
        
        # Generate manifest
        service = ManifestGeneratorService()
        manifest = service.generate_manifest(
            book_id=book_id,
            artist=artist,
            book_name=book_name,
            toc_discovery_data=toc_discovery_data,
            toc_parse_data=toc_parse_data,
            page_mapping_data=page_mapping_data,
            output_files_data=output_files_data
        )
        
        # Write manifest to S3
        output_key = f"output/{book_id}/manifest.json"
        manifest_json = json.dumps(manifest.__dict__, indent=2, default=str)
        s3_utils.write_bytes(manifest_json.encode(), output_bucket, output_key)
        
        logger.info(f"Manifest Generator complete. Created manifest for {len(output_files_data.get('output_files', []))} files")
        
        # Output result for Step Functions
        print(json.dumps({
            'book_id': book_id,
            'manifest_uri': f"s3://{output_bucket}/{output_key}",
            'songs_extracted': len(output_files_data.get('output_files', []))
        }))
        
    except Exception as e:
        logger.error(f"Manifest Generator failed: {e}", exc_info=True)
        sys.exit(1)


def parse_s3_uri(s3_uri: str) -> tuple:
    """Parse S3 URI into bucket and key."""
    if not s3_uri.startswith('s3://'):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
    
    parts = s3_uri[5:].split('/', 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ''
    
    return bucket, key


# Entry point dispatcher
if __name__ == '__main__':
    task_type = os.environ.get('TASK_TYPE')
    
    if task_type == 'toc_discovery':
        toc_discovery_task()
    elif task_type == 'toc_parser':
        toc_parser_task()
    elif task_type == 'page_mapper':
        page_mapper_task()
    elif task_type == 'song_verifier':
        song_verifier_task()
    elif task_type == 'pdf_splitter':
        pdf_splitter_task()
    elif task_type == 'manifest_generator':
        manifest_generator_task()
    else:
        logger.error(f"Unknown task type: {task_type}")
        sys.exit(1)
