"""
ECS Task Entry Points - Entry points for containerized tasks.

Each entry point:
- Reads input from environment variables or stdin
- Executes the corresponding service
- Writes output to S3
- Handles cleanup

v3 changes:
- Artifacts write to ARTIFACTS_BUCKET (jsmith-artifacts) instead of OUTPUT_BUCKET
- Artifact paths use v3/{artist}/{book_name}/ instead of artifacts/{book_id}/
- Output paths use v3/ prefix
- Manifest generation removed (artifacts bucket holds all metadata)
"""

import json
import os
import sys
import logging
import tempfile
from pathlib import Path
import fitz  # PyMuPDF

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# v3 schema prefix for S3 path isolation
S3_SCHEMA_PREFIX = "v3"


def get_artifact_bucket():
    """Get the artifacts bucket name from environment."""
    return os.environ.get('ARTIFACTS_BUCKET', 'jsmith-artifacts')


def get_artifact_prefix(artist: str, book_name: str) -> str:
    """Build the v3 artifact prefix: v3/{artist}/{book_name}/"""
    from app.utils.sanitization import sanitize_artist_name, sanitize_book_name
    sanitized_artist = sanitize_artist_name(artist)
    sanitized_book = sanitize_book_name(book_name)
    return f"{S3_SCHEMA_PREFIX}/{sanitized_artist}/{sanitized_book}"


def toc_discovery_task():
    """
    TOC Discovery ECS task entry point.

    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - OUTPUT_BUCKET: S3 bucket for output
    - ARTIFACTS_BUCKET: S3 bucket for artifacts (v3)
    - ARTIST: Book artist (v3)
    - BOOK_NAME: Book name (v3)
    - MAX_PAGES: Maximum pages to scan (default: 20)
    """
    from app.services.toc_discovery import TOCDiscoveryService
    from app.utils.s3_utils import S3Utils

    logger.info("Starting TOC Discovery task")

    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    artist = os.environ.get('ARTIST', '')
    book_name = os.environ.get('BOOK_NAME', '')
    artifacts_bucket = get_artifact_bucket()
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

            # Write result to artifacts bucket with human-readable path
            artifact_prefix = get_artifact_prefix(artist, book_name)
            output_key = f"{artifact_prefix}/toc_discovery.json"
            result_json = json.dumps({
                'book_id': book_id,
                'toc_pages': result.toc_pages,
                'extracted_text': result.extracted_text,
                'confidence_scores': result.confidence_scores
            })
            s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

            logger.info(f"TOC Discovery complete. Found {len(result.toc_pages)} pages")

            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'toc_pages': result.toc_pages,
                'output_uri': f"s3://{artifacts_bucket}/{output_key}"
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
        
        # Get TOC page numbers
        toc_pages = toc_discovery_data.get('toc_pages', [])
        
        if not toc_pages:
            logger.error("No TOC pages identified")
            sys.exit(1)
        
        # Download the source PDF to render TOC pages
        source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
        if not source_pdf_uri:
            logger.error("SOURCE_PDF_URI environment variable not set")
            sys.exit(1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            bucket, key = parse_s3_uri(source_pdf_uri)
            s3_utils.download_file(bucket, key, pdf_path)
            
            # Render TOC pages as images
            import fitz
            from PIL import Image
            import io
            
            doc = fitz.open(pdf_path)
            toc_images = []
            
            for page_num in toc_pages:
                if page_num < len(doc):
                    page = doc[page_num]
                    mat = fitz.Matrix(150/72, 150/72)  # 150 DPI
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    toc_images.append(image)
                    logger.info(f"Rendered TOC page {page_num}")
            
            doc.close()
            
            if not toc_images:
                logger.error("No TOC images rendered")
                sys.exit(1)

            # Parse TOC using Bedrock vision
            from app.services.bedrock_parser import BedrockParserService
            bedrock_service = BedrockParserService()
            book_metadata = {'artist': artist, 'book_name': book_name}
            result = bedrock_service.bedrock_vision_parse(toc_images, book_metadata)

            # FALLBACK: If vision parsing failed, try text-based parsing using OCR text
            if not result.entries or len(result.entries) < 5:
                logger.warning(f"Vision parsing returned only {len(result.entries)} entries, trying text-based fallback")

                # Get extracted text from discovery results
                extracted_text = toc_discovery_data.get('extracted_text', {})
                if extracted_text:
                    # Combine text from all TOC pages
                    combined_text = '\n'.join(
                        extracted_text.get(str(page_num), '')
                        for page_num in toc_pages
                    )

                    if combined_text.strip():
                        logger.info(f"Attempting text-based parsing on {len(combined_text)} chars of OCR text")
                        from app.services.toc_parser import TOCParser
                        text_parser = TOCParser(use_bedrock_fallback=True)
                        text_result = text_parser.parse_toc(combined_text, book_metadata)

                        if text_result.entries and len(text_result.entries) > len(result.entries):
                            logger.info(f"Text-based parsing succeeded with {len(text_result.entries)} entries")
                            result = text_result

        # Write result to artifacts bucket
        artifacts_bucket = get_artifact_bucket()
        artifact_prefix = get_artifact_prefix(artist, book_name)
        output_key = f"{artifact_prefix}/toc_parse.json"
        result_json = json.dumps({
            'book_id': book_id,
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
        s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

        logger.info(f"TOC Parser complete. Parsed {len(result.entries)} entries")

        # Output result for Step Functions
        print(json.dumps({
            'book_id': book_id,
            'entry_count': len(result.entries),
            'extraction_method': result.extraction_method,
            'output_uri': f"s3://{artifacts_bucket}/{output_key}"
        }))
        
    except Exception as e:
        logger.error(f"TOC Parser failed: {e}", exc_info=True)
        sys.exit(1)


def song_verifier_task():
    """
    Song Verifier ECS task entry point.

    If HOLISTIC page_analysis.json exists with songs, just pass through.
    Otherwise uses SongVerifierService for legacy verification.

    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - PAGE_MAPPING_URI: S3 URI of page mapping JSON
    - OUTPUT_BUCKET: S3 bucket for output
    - ARTIFACTS_BUCKET: S3 bucket for artifacts (v3)
    - ARTIST: Book artist (v3)
    - BOOK_NAME: Book name (v3)
    """
    from app.utils.s3_utils import S3Utils

    logger.info("Starting Song Verifier task")

    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    page_mapping_uri = os.environ.get('PAGE_MAPPING_URI')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    artist = os.environ.get('ARTIST', '')
    book_name = os.environ.get('BOOK_NAME', '')
    artifacts_bucket = get_artifact_bucket()

    if not all([book_id, source_pdf_uri, page_mapping_uri, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    try:
        s3_utils = S3Utils()
        artifact_prefix = get_artifact_prefix(artist, book_name)

        # Check if holistic page_analysis.json exists with songs
        page_analysis = None
        try:
            page_analysis_json = s3_utils.read_bytes(
                artifacts_bucket,
                f"{artifact_prefix}/page_analysis.json"
            ).decode('utf-8')
            page_analysis = json.loads(page_analysis_json)
        except Exception as e:
            logger.info(f"No page_analysis.json found: {e}")

        # If holistic analysis exists with songs, just pass through
        if page_analysis and len(page_analysis.get('songs', [])) > 0:
            logger.info(f"HOLISTIC analysis found with {len(page_analysis['songs'])} songs - passing through")

            # Build verified_songs.json from holistic analysis (don't re-verify)
            output_key = f"{artifact_prefix}/verified_songs.json"
            result_json = json.dumps({
                'verified_songs': [
                    {
                        'song_title': song['title'],
                        'start_page': song['start_pdf_page'] - 1,  # 0-indexed
                        'end_page': song['end_pdf_page'] - 1,  # 0-indexed
                        'artist': song.get('artist', '')
                    }
                    for song in page_analysis['songs']
                ]
            }, indent=2)
            s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

            logger.info(f"Song Verifier complete. Passed through {len(page_analysis['songs'])} songs from holistic analysis")

            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'verified_count': len(page_analysis['songs']),
                'verification_method': 'holistic_passthrough',
                'output_uri': f"s3://{artifacts_bucket}/{output_key}"
            }))
            return

        # Legacy fallback: use SongVerifierService
        logger.info("No holistic analysis - using legacy song verifier")
        from app.services.song_verifier import SongVerifierService
        from app.models import SongLocation

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
                    printed_page=entry['printed_page'],
                    pdf_index=entry['pdf_index'],
                    artist=entry.get('artist', '')
                )
                for entry in page_mapping_data.get('song_locations', [])
            ]

            # Filter out songs with invalid PDF indices
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()

            valid_song_locations = [
                loc for loc in song_locations
                if 0 <= loc.pdf_index < total_pages
            ]

            if len(valid_song_locations) < len(song_locations):
                logger.warning(f"Filtered out {len(song_locations) - len(valid_song_locations)} songs with invalid PDF indices (PDF has {total_pages} pages)")

            logger.info(f"Verifying {len(valid_song_locations)} song start pages")

            # Run verification
            service = SongVerifierService()
            verified_songs = service.verify_song_starts(pdf_path, valid_song_locations)

            # Filter to only verified songs
            verified_only = [v for v in verified_songs if v.verified]

            # Calculate page ranges
            page_ranges = service.adjust_page_ranges(verified_only, total_pages)

            # Write result to artifacts bucket
            output_key = f"{artifact_prefix}/verified_songs.json"
            result_json = json.dumps({
                'book_id': book_id,
                'verified_songs': [
                    {
                        'song_title': pr.song_title,
                        'start_page': pr.start_page,
                        'end_page': pr.end_page,
                        'artist': pr.artist
                    }
                    for pr in page_ranges
                ]
            })
            s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

            logger.info(f"Song Verifier complete. Verified {len(verified_only)}/{len(valid_song_locations)} songs successfully")

            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'verified_count': len(verified_only),
                'output_uri': f"s3://{artifacts_bucket}/{output_key}"
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
            
            # Write output files list to artifacts bucket
            artifacts_bucket = get_artifact_bucket()
            artifact_prefix = get_artifact_prefix(artist, book_name)
            output_key = f"{artifact_prefix}/output_files.json"
            result_json = json.dumps({
                'book_id': book_id,
                'output_files': [
                    {
                        'song_title': f.song_title,
                        'artist': f.artist,
                        'output_uri': f.output_uri,
                        'file_size_bytes': f.file_size_bytes,
                        'page_range': f.page_range
                    }
                    for f in output_files
                ]
            })
            s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

            logger.info(f"PDF Splitter complete. Created {len(output_files)} files")

            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'files_created': len(output_files),
                'output_uri': f"s3://{artifacts_bucket}/{output_key}"
            }))
            
    except Exception as e:
        logger.error(f"PDF Splitter failed: {e}", exc_info=True)
        sys.exit(1)


def page_mapper_task():
    """
    Page Mapper ECS task entry point.

    If HOLISTIC page_analysis.json exists with songs, just pass through.
    Otherwise uses ImprovedPageMapperService for legacy fallback.

    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - TOC_PARSE_URI: S3 URI of TOC parse JSON
    - OUTPUT_BUCKET: S3 bucket for output
    - ARTIST: Book-level artist (performer)
    - BOOK_NAME: Book name
    """
    from app.utils.s3_utils import S3Utils

    logger.info("Starting Page Mapper task")

    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    toc_parse_uri = os.environ.get('TOC_PARSE_URI')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    book_artist = os.environ.get('ARTIST', '')
    book_name = os.environ.get('BOOK_NAME', '')

    if not all([book_id, source_pdf_uri, toc_parse_uri, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    try:
        s3_utils = S3Utils()
        artifacts_bucket = get_artifact_bucket()
        artifact_prefix = get_artifact_prefix(book_artist, book_name)

        # Check if holistic page_analysis.json exists with songs
        page_analysis = None
        try:
            page_analysis_json = s3_utils.read_bytes(
                artifacts_bucket,
                f"{artifact_prefix}/page_analysis.json"
            ).decode('utf-8')
            page_analysis = json.loads(page_analysis_json)
        except Exception as e:
            logger.info(f"No page_analysis.json found: {e}")

        # If holistic analysis exists with songs, just pass through
        if page_analysis and len(page_analysis.get('songs', [])) > 0:
            logger.info(f"HOLISTIC analysis found with {len(page_analysis['songs'])} songs - passing through")

            # Build page_mapping.json from holistic analysis (don't re-verify)
            output_key = f"{artifact_prefix}/page_mapping.json"
            result_json = json.dumps({
                'offset': page_analysis.get('calculated_offset', 0),
                'confidence': page_analysis.get('offset_confidence', 1.0),
                'samples_verified': page_analysis.get('matched_song_count', 0),
                'song_locations': [
                    {
                        'song_title': song['title'],
                        'printed_page': song.get('toc_page') or song['start_pdf_page'],
                        'pdf_index': song['start_pdf_page'] - 1,
                        'artist': song.get('artist', '')
                    }
                    for song in page_analysis['songs']
                ],
                'mapping_method': 'holistic_passthrough'
            }, indent=2)
            s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

            logger.info(f"Page Mapper complete. Passed through {len(page_analysis['songs'])} songs from holistic analysis")

            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'songs_mapped': len(page_analysis['songs']),
                'mapping_method': 'holistic_passthrough',
                'output_uri': f"s3://{artifacts_bucket}/{output_key}"
            }))
            return

        # Legacy fallback: use ImprovedPageMapperService
        logger.info("No holistic analysis - using legacy page mapper")
        from app.services.improved_page_mapper import ImprovedPageMapperService
        from app.models import TOCEntry

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            bucket, key = parse_s3_uri(source_pdf_uri)
            s3_utils.download_file(bucket, key, pdf_path)

            # Load TOC parse results
            bucket, key = parse_s3_uri(toc_parse_uri)
            toc_parse_json = s3_utils.read_bytes(bucket, key).decode('utf-8')
            toc_parse_data = json.loads(toc_parse_json)

            toc_entries = [
                TOCEntry(
                    song_title=entry['song_title'],
                    page_number=entry['page_number'],
                    artist=entry.get('artist', ''),
                    confidence=entry.get('confidence', 1.0)
                )
                for entry in toc_parse_data.get('entries', [])
            ]

            service = ImprovedPageMapperService()
            page_mapping = service.build_page_mapping_fallback(
                pdf_path=pdf_path,
                toc_entries=toc_entries,
                book_artist=book_artist,
                book_name=book_name
            )

            output_key = f"{artifact_prefix}/page_mapping.json"
            result_json = json.dumps({
                'book_id': book_id,
                'offset': page_mapping.offset,
                'confidence': page_mapping.confidence,
                'samples_verified': page_mapping.samples_verified,
                'song_locations': [
                    {
                        'song_title': loc.song_title,
                        'printed_page': loc.printed_page,
                        'pdf_index': loc.pdf_index,
                        'artist': loc.artist
                    }
                    for loc in page_mapping.song_locations
                ],
                'mapping_method': 'legacy_fallback'
            })
            s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

            logger.info(f"Page Mapper complete. Mapped {len(page_mapping.song_locations)} songs")
            logger.info(f"Confidence: {page_mapping.confidence:.2%}")

            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'mapped_count': len(page_mapping.song_locations),
                'offset': page_mapping.offset,
                'confidence': page_mapping.confidence,
                'mapping_method': 'page_analysis' if page_analysis else 'fallback',
                'output_uri': f"s3://{artifacts_bucket}/{output_key}"
            }))

    except Exception as e:
        logger.error(f"Page Mapper failed: {e}", exc_info=True)
        sys.exit(1)


def page_analysis_task():
    """
    Page Analysis ECS task entry point.

    Uses HOLISTIC page analysis:
    1. Full scan of every page
    2. Match TOC entries to detected song starts
    3. Offset fallback for unmatched songs
    4. Assign all pages to songs

    Environment variables:
    - BOOK_ID: Unique book identifier
    - SOURCE_PDF_URI: S3 URI of source PDF
    - ARTIST: Book artist
    - BOOK_NAME: Book name
    - OUTPUT_BUCKET: S3 bucket for output
    """
    from app.services.holistic_page_analyzer import HolisticPageAnalyzer
    from app.utils.s3_utils import S3Utils

    logger.info("Starting Page Analysis task (HOLISTIC VERSION)")

    # Get input from environment
    book_id = os.environ.get('BOOK_ID')
    source_pdf_uri = os.environ.get('SOURCE_PDF_URI')
    artist = os.environ.get('ARTIST', '')
    book_name = os.environ.get('BOOK_NAME', '')
    output_bucket = os.environ.get('OUTPUT_BUCKET')

    if not all([book_id, source_pdf_uri, output_bucket]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    try:
        s3_utils = S3Utils()
        artifacts_bucket = get_artifact_bucket()
        artifact_prefix = get_artifact_prefix(artist, book_name)

        # Load TOC parse results to get song titles
        toc_entries = []
        try:
            toc_parse_json = s3_utils.read_bytes(
                artifacts_bucket,
                f"{artifact_prefix}/toc_parse.json"
            ).decode('utf-8')
            toc_parse_data = json.loads(toc_parse_json)
            toc_entries = toc_parse_data.get('entries', [])
            logger.info(f"Loaded {len(toc_entries)} TOC entries")
        except Exception as e:
            logger.warning(f"Could not load TOC entries: {e}")

        # Download PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, 'input.pdf')
            bucket, key = parse_s3_uri(source_pdf_uri)
            s3_utils.download_file(bucket, key, pdf_path)

            # Run HOLISTIC page analysis
            analyzer = HolisticPageAnalyzer()
            result = analyzer.analyze_book(
                pdf_path=pdf_path,
                book_id=book_id,
                source_pdf_uri=source_pdf_uri,
                toc_entries=toc_entries,
                artist=artist
            )

            # Save page_analysis.json (full analysis) to artifacts bucket
            result_dict = analyzer.to_dict(result)
            result_dict['book_id'] = book_id
            output_key = f"{artifact_prefix}/page_analysis.json"
            result_json = json.dumps(result_dict, indent=2)
            s3_utils.write_bytes(result_json.encode(), artifacts_bucket, output_key)

            # Also save page_mapping.json (for compatibility with downstream tasks)
            page_mapping = {
                'book_id': book_id,
                'offset': result.calculated_offset,
                'confidence': result.offset_confidence,
                'samples_verified': result.matched_song_count,
                'song_locations': [
                    {
                        'song_title': song.title,
                        'printed_page': song.toc_page or song.start_pdf_page,
                        'pdf_index': song.start_pdf_page - 1,  # 0-indexed for downstream
                        'artist': song.artist
                    }
                    for song in result.songs
                ],
                'mapping_method': 'holistic_analysis'
            }
            mapping_key = f"{artifact_prefix}/page_mapping.json"
            s3_utils.write_bytes(json.dumps(page_mapping, indent=2).encode(), artifacts_bucket, mapping_key)

            # Also save verified_songs.json (for PDF splitter)
            verified_songs = {
                'book_id': book_id,
                'verified_songs': [
                    {
                        'song_title': song.title,
                        'start_page': song.start_pdf_page - 1,  # Convert 1-indexed to 0-indexed
                        'end_page': song.end_pdf_page,  # 1-indexed inclusive == 0-indexed exclusive
                        'artist': song.artist
                    }
                    for song in result.songs
                ]
            }
            verified_key = f"{artifact_prefix}/verified_songs.json"
            s3_utils.write_bytes(json.dumps(verified_songs, indent=2).encode(), artifacts_bucket, verified_key)

            logger.info(f"Holistic Analysis complete:")
            logger.info(f"  TOC songs: {result.toc_song_count}")
            logger.info(f"  Detected: {result.detected_song_count}")
            logger.info(f"  Matched: {result.matched_song_count}")
            logger.info(f"  Offset: {result.calculated_offset} (confidence: {result.offset_confidence:.2f})")

            if result.warnings:
                for w in result.warnings[:5]:
                    logger.warning(f"  {w}")

            # Output result for Step Functions
            print(json.dumps({
                'book_id': book_id,
                'page_offset': result.calculated_offset,
                'offset_consistent': result.offset_confidence > 0.9,
                'songs_found': len(result.songs),
                'pages_analyzed': result.total_pages,
                'toc_songs': result.toc_song_count,
                'matched_songs': result.matched_song_count,
                'output_uri': f"s3://{artifacts_bucket}/{output_key}"
            }))

    except Exception as e:
        logger.error(f"Page Analysis failed: {e}", exc_info=True)
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
    elif task_type == 'page_analysis':
        page_analysis_task()
    elif task_type == 'page_mapper':
        page_mapper_task()
    elif task_type == 'song_verifier':
        song_verifier_task()
    elif task_type == 'pdf_splitter':
        pdf_splitter_task()
    else:
        logger.error(f"Unknown task type: {task_type}")
        sys.exit(1)
