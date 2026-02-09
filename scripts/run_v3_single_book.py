"""
V3 Single-Book Pipeline Runner

Runs the full pipeline for a single book locally, calling AWS services
(S3, Bedrock, Textract) but orchestrating locally instead of via Step Functions.

Supports stop/start: checks for existing artifacts before each step and skips
completed steps. Use --force-step <name> to re-run a specific step.

Usage:
    python scripts/run_v3_single_book.py --artist "Billy Joel" --book "My Lives"
    python scripts/run_v3_single_book.py --artist "Billy Joel" --book "My Lives" --force-step toc_parser
    python scripts/run_v3_single_book.py --artist "Billy Joel" --book "My Lives" --dry-run
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import boto3

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.sanitization import sanitize_artist_name, sanitize_book_name

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('v3_runner')

# V3 constants
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_PREFIX = 'v3'
DYNAMODB_TABLE = 'jsmith-pipeline-ledger'

PIPELINE_STEPS = [
    'toc_discovery',
    'toc_parser',
    'page_analysis',
    'pdf_splitter',
]


def generate_book_id(s3_uri: str) -> str:
    return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]


def get_artifact_prefix(artist: str, book_name: str) -> str:
    sa = sanitize_artist_name(artist)
    sb = sanitize_book_name(book_name)
    return f"{S3_PREFIX}/{sa}/{sb}"


def check_artifact_exists(s3, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False
    except Exception:
        return False


def read_artifact_json(s3, bucket: str, key: str) -> dict:
    resp = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(resp['Body'].read().decode('utf-8'))


def write_artifact_json(s3, bucket: str, key: str, data: dict):
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2).encode('utf-8'),
        ContentType='application/json'
    )
    logger.info(f"  Wrote s3://{bucket}/{key}")


def utc_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sync_to_local(s3_client, artist: str, book_name: str, source_pdf_path: str = None):
    """Sync artifacts and output PDFs from S3 to local filesystem."""
    sa = sanitize_artist_name(artist)
    sb = sanitize_book_name(book_name)

    # 1. Sync artifacts: s3://jsmith-artifacts/v3/{Artist}/{Book}/ → SheetMusic_Artifacts/{Artist}/{Book}/
    artifacts_local = PROJECT_ROOT / 'SheetMusic_Artifacts' / sa / sb
    artifacts_local.mkdir(parents=True, exist_ok=True)
    artifacts_prefix = f"{S3_PREFIX}/{sa}/{sb}/"

    paginator = s3_client.get_paginator('list_objects_v2')
    count = 0
    for page in paginator.paginate(Bucket=ARTIFACTS_BUCKET, Prefix=artifacts_prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            filename = key.split('/')[-1]
            local_path = artifacts_local / filename
            s3_client.download_file(ARTIFACTS_BUCKET, key, str(local_path))
            count += 1
    logger.info(f"  Synced {count} artifacts → {artifacts_local}")

    # 2. Sync output PDFs: s3://jsmith-output/v3/{Artist}/{Book}/ → SheetMusic_Output/{Artist}/{Book}/
    output_local = PROJECT_ROOT / 'SheetMusic_Output' / sa / sb
    output_local.mkdir(parents=True, exist_ok=True)
    output_prefix = f"{S3_PREFIX}/{sa}/{sb}/"

    count = 0
    for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=output_prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            filename = key.split('/')[-1]
            if filename.endswith('.pdf'):
                local_path = output_local / filename
                s3_client.download_file(OUTPUT_BUCKET, key, str(local_path))
                count += 1
    logger.info(f"  Synced {count} song PDFs → {output_local}")

    # 3. Copy source songbook PDF to SheetMusic_Output/{Artist}/ level
    if source_pdf_path and os.path.exists(source_pdf_path):
        import shutil
        source_dest = PROJECT_ROOT / 'SheetMusic_Output' / sa / f"{sa} - {sb}.pdf"
        shutil.copy2(source_pdf_path, str(source_dest))
        logger.info(f"  Copied source PDF → {source_dest}")
    else:
        # Download from S3 input bucket
        s3_key = f"{S3_PREFIX}/{sa}/{sa} - {sb}.pdf"
        source_dest = PROJECT_ROOT / 'SheetMusic_Output' / sa / f"{sa} - {sb}.pdf"
        source_dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            s3_client.download_file(INPUT_BUCKET, s3_key, str(source_dest))
            logger.info(f"  Downloaded source PDF → {source_dest}")
        except Exception as e:
            logger.warning(f"  Could not download source PDF: {e}")


def dynamo_safe(obj):
    """Convert floats to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(round(obj, 2)))
    if isinstance(obj, dict):
        return {k: dynamo_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [dynamo_safe(v) for v in obj]
    return obj


def update_dynamo_step(table, book_id: str, step_name: str, step_data: dict,
                       current_step: str = None):
    ts = utc_now()
    step_data = dynamo_safe(step_data)
    update_expr = 'SET steps.#step = :step_data, updated_at = :now'
    names = {'#step': step_name}
    values = {':step_data': step_data, ':now': ts}

    if current_step:
        update_expr += ', current_step = :current_step'
        values[':current_step'] = current_step

    table.update_item(
        Key={'book_id': book_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values
    )


def run_toc_discovery(s3, pdf_path: str, book_id: str, artifact_prefix: str):
    """Step 1: Discover which pages contain the Table of Contents."""
    from app.services.toc_discovery import TOCDiscoveryService

    logger.info("Running TOC Discovery...")
    service = TOCDiscoveryService()
    result = service.discover_toc(pdf_path, max_pages=20)

    data = {
        'book_id': book_id,
        'toc_pages': result.toc_pages,
        'extracted_text': result.extracted_text,
        'confidence_scores': result.confidence_scores,
    }
    write_artifact_json(s3, ARTIFACTS_BUCKET, f"{artifact_prefix}/toc_discovery.json", data)

    logger.info(f"  TOC pages found: {result.toc_pages}")
    logger.info(f"  Confidence scores: {result.confidence_scores}")
    return data


def run_toc_parser(s3, pdf_path: str, book_id: str, artifact_prefix: str,
                   toc_discovery: dict):
    """Step 2: Parse TOC pages to extract song entries."""
    from app.services.bedrock_parser import BedrockParserService

    logger.info("Running TOC Parser...")
    toc_pages = toc_discovery.get('toc_pages', [])
    if not toc_pages:
        logger.warning("No TOC pages found - parser may not produce useful results")

    # Render TOC pages as PIL Images for vision parsing
    import fitz
    from PIL import Image
    import io

    doc = fitz.open(pdf_path)
    toc_images = []
    for page_num in toc_pages:
        if 0 <= page_num < len(doc):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            toc_images.append(img)
    doc.close()

    if not toc_images:
        logger.warning("No TOC page images rendered - trying first 5 pages as fallback")
        doc = fitz.open(pdf_path)
        for i in range(min(5, len(doc))):
            page = doc[i]
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            toc_images.append(img)
        doc.close()

    book_metadata = {
        'book_id': book_id,
        'toc_pages': toc_pages,
    }

    service = BedrockParserService()
    result = service.bedrock_vision_parse(toc_images, book_metadata)

    data = {
        'book_id': book_id,
        'entries': [
            {
                'song_title': e.song_title,
                'page_number': e.page_number,
                'artist': getattr(e, 'artist', ''),
                'confidence': getattr(e, 'confidence', 1.0),
            }
            for e in result.entries
        ],
        'parse_method': result.parse_method if hasattr(result, 'parse_method') else 'bedrock_vision',
        'raw_text': result.raw_text if hasattr(result, 'raw_text') else '',
    }
    write_artifact_json(s3, ARTIFACTS_BUCKET, f"{artifact_prefix}/toc_parse.json", data)

    logger.info(f"  Songs found: {len(data['entries'])}")
    for e in data['entries'][:5]:
        logger.info(f"    {e['page_number']:>4}  {e['song_title']}")
    if len(data['entries']) > 5:
        logger.info(f"    ... and {len(data['entries']) - 5} more")
    return data


def run_page_analysis(s3, pdf_path: str, book_id: str, source_pdf_uri: str,
                      artifact_prefix: str, toc_parse: dict, artist: str,
                      max_workers: int = 1):
    """Step 3: Holistic page analysis - analyzes every page, produces all downstream artifacts."""
    from app.services.holistic_page_analyzer import HolisticPageAnalyzer

    logger.info("Running Holistic Page Analysis...")
    logger.info(f"  (max_workers={max_workers}, analyzes every page)")

    toc_entries = toc_parse.get('entries', [])
    analyzer = HolisticPageAnalyzer(max_workers=max_workers)
    result = analyzer.analyze_book(
        pdf_path=pdf_path,
        book_id=book_id,
        source_pdf_uri=source_pdf_uri,
        toc_entries=toc_entries,
        artist=artist
    )

    # Save page_analysis.json (full analysis)
    result_dict = analyzer.to_dict(result)
    result_dict['book_id'] = book_id
    write_artifact_json(s3, ARTIFACTS_BUCKET, f"{artifact_prefix}/page_analysis.json", result_dict)

    # Save page_mapping.json (for compatibility)
    page_mapping = {
        'book_id': book_id,
        'offset': result.calculated_offset,
        'confidence': result.offset_confidence,
        'samples_verified': result.matched_song_count,
        'song_locations': [
            {
                'song_title': song.title,
                'printed_page': song.toc_page or song.start_pdf_page,
                'pdf_index': song.start_pdf_page - 1,
                'artist': song.artist
            }
            for song in result.songs
        ],
        'mapping_method': 'holistic_analysis'
    }
    write_artifact_json(s3, ARTIFACTS_BUCKET, f"{artifact_prefix}/page_mapping.json", page_mapping)

    # Save verified_songs.json (for PDF splitter)
    verified_songs = {
        'book_id': book_id,
        'verified_songs': [
            {
                'song_title': song.title,
                'start_page': song.start_pdf_page - 1,  # Convert 1-indexed to 0-indexed
                'end_page': song.end_pdf_page,           # 1-indexed inclusive == 0-indexed exclusive
                'artist': song.artist
            }
            for song in result.songs
        ]
    }
    write_artifact_json(s3, ARTIFACTS_BUCKET, f"{artifact_prefix}/verified_songs.json", verified_songs)

    logger.info(f"  TOC songs: {result.toc_song_count}")
    logger.info(f"  Detected: {result.detected_song_count}")
    logger.info(f"  Matched: {result.matched_song_count}")
    logger.info(f"  Offset: {result.calculated_offset} (confidence: {result.offset_confidence:.2f})")
    logger.info(f"  Final songs: {len(result.songs)}")

    if result.warnings:
        for w in result.warnings[:5]:
            logger.warning(f"  {w}")

    return verified_songs


def run_pdf_splitter(s3, pdf_path: str, book_id: str, artifact_prefix: str,
                     verified_songs: dict, artist: str, book_name: str):
    """Step 4: Split PDF into individual song files."""
    from app.services.pdf_splitter import PDFSplitterService
    from app.models import PageRange

    logger.info("Running PDF Splitter...")

    page_ranges = [
        PageRange(
            song_title=song['song_title'],
            start_page=song['start_page'],
            end_page=song['end_page'],
            artist=song.get('artist', artist)
        )
        for song in verified_songs.get('verified_songs', [])
    ]

    service = PDFSplitterService(output_bucket=OUTPUT_BUCKET)
    output_files = service.split_pdf(pdf_path, page_ranges, artist, book_name)

    # Write output_files.json to artifacts
    data = {
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
    }
    write_artifact_json(s3, ARTIFACTS_BUCKET, f"{artifact_prefix}/output_files.json", data)

    logger.info(f"  Created {len(output_files)} song PDFs")
    total_bytes = sum(f.file_size_bytes for f in output_files)
    logger.info(f"  Total output size: {total_bytes / 1024 / 1024:.1f} MB")
    return data


def main():
    parser = argparse.ArgumentParser(description='V3 Single-Book Pipeline Runner')
    parser.add_argument('--artist', required=True, help='Artist name')
    parser.add_argument('--book', required=True, help='Book name')
    parser.add_argument('--force-step', help='Force re-run of a specific step')
    parser.add_argument('--dry-run', action='store_true', help='Show what would run without executing')
    parser.add_argument('--max-workers', type=int, default=1,
                        help='Parallel Bedrock vision calls for page analysis (default: 1)')
    args = parser.parse_args()

    artist = args.artist
    book_name = args.book

    # Build paths
    s3_key = f"{S3_PREFIX}/{artist}/{artist} - {book_name}.pdf"
    source_pdf_uri = f"s3://{INPUT_BUCKET}/{s3_key}"
    book_id = generate_book_id(source_pdf_uri)
    artifact_prefix = get_artifact_prefix(artist, book_name)

    logger.info("=" * 70)
    logger.info("V3 SINGLE-BOOK PIPELINE RUNNER")
    logger.info("=" * 70)
    logger.info(f"  Artist:          {artist}")
    logger.info(f"  Book:            {book_name}")
    logger.info(f"  Book ID:         {book_id}")
    logger.info(f"  Source:          {source_pdf_uri}")
    logger.info(f"  Artifact prefix: {artifact_prefix}")
    logger.info("")

    # AWS clients
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)

    # Verify source PDF exists
    try:
        s3.head_object(Bucket=INPUT_BUCKET, Key=s3_key)
        logger.info(f"  Source PDF confirmed in S3")
    except Exception as e:
        logger.error(f"Source PDF not found at s3://{INPUT_BUCKET}/{s3_key}")
        logger.error(f"Upload first: aws s3 cp \"SheetMusic_Input/{artist}/{artist} - {book_name}.pdf\" \"s3://{INPUT_BUCKET}/{s3_key}\"")
        sys.exit(1)

    # Check which steps already have artifacts
    artifact_files = {
        'toc_discovery': f"{artifact_prefix}/toc_discovery.json",
        'toc_parser': f"{artifact_prefix}/toc_parse.json",
        'page_analysis': f"{artifact_prefix}/verified_songs.json",
        'pdf_splitter': f"{artifact_prefix}/output_files.json",
    }

    logger.info("Checking existing artifacts:")
    existing = {}
    for step, key in artifact_files.items():
        try:
            s3.head_object(Bucket=ARTIFACTS_BUCKET, Key=key)
            existing[step] = True
            logger.info(f"  {step:20s} -> EXISTS (will skip)")
        except Exception:
            existing[step] = False
            logger.info(f"  {step:20s} -> not found (will run)")

    # Apply force-step override
    if args.force_step:
        if args.force_step in existing:
            existing[args.force_step] = False
            logger.info(f"\n  --force-step: Will re-run {args.force_step}")
            # Also invalidate downstream steps
            found = False
            for step in PIPELINE_STEPS:
                if step == args.force_step:
                    found = True
                if found:
                    existing[step] = False
                    if step != args.force_step:
                        logger.info(f"  --force-step: Will also re-run downstream {step}")
        else:
            logger.error(f"Unknown step: {args.force_step}. Valid: {PIPELINE_STEPS}")
            sys.exit(1)

    if args.dry_run:
        logger.info("\n[DRY RUN] Would execute the following steps:")
        for step in PIPELINE_STEPS:
            action = "SKIP (artifact exists)" if existing.get(step) else "RUN"
            logger.info(f"  {step:20s} -> {action}")
        return

    # Initialize or update DynamoDB record
    now_iso = utc_now()
    try:
        resp = table.get_item(Key={'book_id': book_id})
        if 'Item' not in resp:
            logger.info("Creating DynamoDB ledger entry...")
            table.put_item(Item={
                'book_id': book_id,
                'artist': artist,
                'book_name': book_name,
                'pipeline_version': 'v3',
                'status': 'in_progress',
                'source_pdf_uri': source_pdf_uri,
                'current_step': 'toc_discovery',
                'created_at': now_iso,
                'updated_at': now_iso,
                'steps': {}
            })
        else:
            logger.info(f"DynamoDB entry exists (status: {resp['Item'].get('status')})")
            table.update_item(
                Key={'book_id': book_id},
                UpdateExpression='SET #status = :s, updated_at = :now',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':s': 'in_progress', ':now': now_iso}
            )
    except Exception as e:
        logger.warning(f"DynamoDB update failed (continuing anyway): {e}")

    # Download PDF once
    logger.info("\nDownloading source PDF...")
    temp_dir = tempfile.mkdtemp(prefix='v3_runner_')
    pdf_path = os.path.join(temp_dir, f"{artist} - {book_name}.pdf")
    s3.download_file(INPUT_BUCKET, s3_key, pdf_path)
    pdf_size = os.path.getsize(pdf_path)
    logger.info(f"  Downloaded {pdf_size / 1024 / 1024:.1f} MB to {pdf_path}")

    pipeline_start = time.time()

    try:
        # ---- Step 1: TOC Discovery ----
        if not existing.get('toc_discovery'):
            step_start = time.time()
            update_dynamo_step(table, book_id, 'toc_discovery',
                               {'status': 'in_progress', 'started_at': now_iso},
                               current_step='toc_discovery')
            toc_discovery = run_toc_discovery(s3, pdf_path, book_id, artifact_prefix)
            duration = time.time() - step_start
            update_dynamo_step(table, book_id, 'toc_discovery', {
                'status': 'success',
                'started_at': now_iso,
                'completed_at': utc_now(),
                'duration_sec': round(duration, 1),
                'toc_pages_found': len(toc_discovery.get('toc_pages', []))
            })
            logger.info(f"  TOC Discovery completed in {duration:.1f}s\n")
        else:
            logger.info("\nStep 1: TOC Discovery - SKIPPED (artifact exists)")
            toc_discovery = read_artifact_json(s3, ARTIFACTS_BUCKET,
                                               artifact_files['toc_discovery'])
            logger.info(f"  Loaded existing: {len(toc_discovery.get('toc_pages', []))} TOC pages\n")

        # ---- Step 2: TOC Parser ----
        if not existing.get('toc_parser'):
            step_start = time.time()
            now_iso2 = utc_now()
            update_dynamo_step(table, book_id, 'toc_parser',
                               {'status': 'in_progress', 'started_at': now_iso2},
                               current_step='toc_parser')
            toc_parse = run_toc_parser(s3, pdf_path, book_id, artifact_prefix, toc_discovery)
            duration = time.time() - step_start
            update_dynamo_step(table, book_id, 'toc_parser', {
                'status': 'success',
                'started_at': now_iso2,
                'completed_at': utc_now(),
                'duration_sec': round(duration, 1),
                'songs_found': len(toc_parse.get('entries', []))
            })
            logger.info(f"  TOC Parser completed in {duration:.1f}s\n")
        else:
            logger.info("Step 2: TOC Parser - SKIPPED (artifact exists)")
            toc_parse = read_artifact_json(s3, ARTIFACTS_BUCKET,
                                           artifact_files['toc_parser'])
            logger.info(f"  Loaded existing: {len(toc_parse.get('entries', []))} entries\n")

        # ---- Step 3: Page Analysis (Holistic) ----
        if not existing.get('page_analysis'):
            step_start = time.time()
            now_iso3 = utc_now()
            update_dynamo_step(table, book_id, 'page_analysis',
                               {'status': 'in_progress', 'started_at': now_iso3},
                               current_step='page_analysis')
            verified_songs = run_page_analysis(s3, pdf_path, book_id, source_pdf_uri,
                                               artifact_prefix, toc_parse, artist,
                                               max_workers=args.max_workers)
            duration = time.time() - step_start
            update_dynamo_step(table, book_id, 'page_analysis', {
                'status': 'success',
                'started_at': now_iso3,
                'completed_at': utc_now(),
                'duration_sec': round(duration, 1),
                'songs_found': len(verified_songs.get('verified_songs', []))
            })
            logger.info(f"  Page Analysis completed in {duration:.1f}s\n")
        else:
            logger.info("Step 3: Page Analysis - SKIPPED (artifact exists)")
            verified_songs = read_artifact_json(s3, ARTIFACTS_BUCKET,
                                                artifact_files['page_analysis'])
            logger.info(f"  Loaded existing: {len(verified_songs.get('verified_songs', []))} songs\n")

        # ---- Step 4: PDF Splitter ----
        if not existing.get('pdf_splitter'):
            step_start = time.time()
            now_iso4 = utc_now()
            update_dynamo_step(table, book_id, 'pdf_splitter',
                               {'status': 'in_progress', 'started_at': now_iso4},
                               current_step='pdf_splitter')
            output_data = run_pdf_splitter(s3, pdf_path, book_id, artifact_prefix,
                                           verified_songs, artist, book_name)
            duration = time.time() - step_start
            update_dynamo_step(table, book_id, 'pdf_splitter', {
                'status': 'success',
                'started_at': now_iso4,
                'completed_at': utc_now(),
                'duration_sec': round(duration, 1),
                'files_created': len(output_data.get('output_files', []))
            })
            logger.info(f"  PDF Splitter completed in {duration:.1f}s\n")
        else:
            logger.info("Step 4: PDF Splitter - SKIPPED (artifact exists)")
            output_data = read_artifact_json(s3, ARTIFACTS_BUCKET,
                                             artifact_files['pdf_splitter'])
            logger.info(f"  Loaded existing: {len(output_data.get('output_files', []))} files\n")

        # ---- Pipeline Complete ----
        total_duration = time.time() - pipeline_start
        songs_count = len(output_data.get('output_files', []))

        # Update DynamoDB final status
        final_now = utc_now()
        table.update_item(
            Key={'book_id': book_id},
            UpdateExpression='SET #status = :s, updated_at = :now, songs_extracted = :songs, total_duration_sec = :dur',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':s': 'success',
                ':now': final_now,
                ':songs': songs_count,
                ':dur': Decimal(str(round(total_duration, 1)))
            }
        )

        logger.info("=" * 70)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"  Book:     {artist} - {book_name}")
        logger.info(f"  Book ID:  {book_id}")
        logger.info(f"  Songs:    {songs_count}")
        logger.info(f"  Duration: {total_duration:.1f}s ({total_duration / 60:.1f} min)")
        logger.info(f"  Artifacts: s3://{ARTIFACTS_BUCKET}/{artifact_prefix}/")
        logger.info(f"  Output:    s3://{OUTPUT_BUCKET}/{S3_PREFIX}/")
        logger.info("")

        # ---- Sync to local filesystem ----
        logger.info("Syncing to local filesystem...")
        try:
            sync_to_local(s3, artist, book_name, source_pdf_path=pdf_path)
            logger.info("  Local sync complete.\n")
        except Exception as sync_err:
            logger.warning(f"  Local sync failed (non-fatal): {sync_err}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        # Record failure in DynamoDB
        try:
            fail_now = utc_now()
            table.update_item(
                Key={'book_id': book_id},
                UpdateExpression='SET #status = :s, updated_at = :now, error_message = :err',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':s': 'failed',
                    ':now': fail_now,
                    ':err': str(e)
                }
            )
        except Exception:
            pass
        sys.exit(1)
    finally:
        # Cleanup temp dir
        import shutil
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp dir: {temp_dir}")
        except Exception:
            pass


if __name__ == '__main__':
    main()
