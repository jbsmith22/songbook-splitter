"""
Pipeline API Server - Local server to bridge viewer and AWS pipeline

Run this to enable reprocessing from the viewer:
    py scripts/pipeline_api_server.py

Then open the viewer and use the action buttons.
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import boto3
import json
import time
from pathlib import Path
import io
import fitz  # PyMuPDF

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from file:// protocol

# AWS clients
stepfunctions = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Configuration
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'


def clear_old_artifacts(book_id: str) -> int:
    """
    Clear old artifacts for a book before reprocessing.

    This ensures we don't use stale data from previous runs.
    Deletes all files in artifacts/{book_id}/ folder.

    Args:
        book_id: The book ID to clear artifacts for

    Returns:
        Number of objects deleted
    """
    artifacts_prefix = f"artifacts/{book_id}/"

    # List all objects with this prefix
    deleted_count = 0
    paginator = s3.get_paginator('list_objects_v2')

    try:
        for page in paginator.paginate(Bucket=BUCKET, Prefix=artifacts_prefix):
            if 'Contents' not in page:
                continue

            objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]

            if objects_to_delete:
                s3.delete_objects(
                    Bucket=BUCKET,
                    Delete={'Objects': objects_to_delete}
                )
                deleted_count += len(objects_to_delete)
                for obj in objects_to_delete:
                    print(f"  Deleted: {obj['Key']}")

    except Exception as e:
        print(f"Warning: Error clearing artifacts: {e}")

    return deleted_count


@app.route('/api/status/<book_id>', methods=['GET'])
def get_status(book_id):
    """Get processing status for a book"""
    try:
        # Check DynamoDB ledger
        response = TABLE.get_item(Key={'book_id': book_id})

        if 'Item' not in response:
            return jsonify({
                'status': 'not_found',
                'message': 'Book not in processing ledger'
            })

        item = response['Item']
        return jsonify({
            'status': 'found',
            'book_id': book_id,
            'processing_status': item.get('status'),  # Field is 'status' not 'processing_status'
            'source_pdf_uri': item.get('source_pdf_uri'),
            'local_output_path': item.get('local_output_path'),
            's3_output_path': item.get('s3_output_path'),
            'created_date': item.get('created_date'),
            'songs_extracted': item.get('songs_extracted', 0),
            'processing_duration': item.get('processing_duration_seconds', 0)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reprocess', methods=['POST'])
def trigger_reprocess():
    """Trigger reprocessing via Step Functions"""
    try:
        data = request.json
        book_id = data.get('book_id')
        source_pdf = data.get('source_pdf')
        force = data.get('force', False)  # Force reprocess even if already done

        if not book_id or not source_pdf:
            return jsonify({'status': 'error', 'message': 'book_id and source_pdf required'}), 400

        # Extract artist and book_name from source_pdf path
        # Format: "Artist/Artist - Book Name.pdf"
        path_parts = source_pdf.replace('\\', '/').split('/')
        if len(path_parts) >= 2:
            artist = path_parts[0]
            book_filename = path_parts[-1].replace('.pdf', '')
            # Extract book name from "Artist - Book Name" format
            if ' - ' in book_filename:
                book_name = book_filename.split(' - ', 1)[1]
            else:
                book_name = book_filename
        else:
            # Fallback
            artist = 'Unknown'
            book_name = source_pdf.replace('.pdf', '')

        # Ensure source PDF is uploaded to jsmith-input bucket
        # Source PDFs should be at s3://jsmith-input/<artist>/<artist> - <book>.pdf
        input_bucket = 'jsmith-input'
        s3_source_key = source_pdf  # e.g., "America/America - Greatest Hits _Book_.pdf"

        # Check if source PDF exists in jsmith-input
        try:
            s3.head_object(Bucket=input_bucket, Key=s3_source_key)
            print(f"✓ Source PDF already exists in s3://{input_bucket}/{s3_source_key}")
        except:
            # Source PDF not in S3 - upload from local SheetMusic folder
            local_source_path = Path('SheetMusic') / source_pdf
            if not local_source_path.exists():
                return jsonify({
                    'status': 'error',
                    'message': f'Source PDF not found locally: {local_source_path}'
                }), 404

            print(f"⬆️  Uploading source PDF to s3://{input_bucket}/{s3_source_key}")
            with open(local_source_path, 'rb') as f:
                s3.put_object(
                    Bucket=input_bucket,
                    Key=s3_source_key,
                    Body=f,
                    ContentType='application/pdf'
                )
            print(f"✓ Upload complete")

        # IMPORTANT: Clear old artifacts to prevent stale data
        if force:
            print(f"🧹 Clearing old artifacts for {book_id}...")
            artifacts_cleared = clear_old_artifacts(book_id)
            print(f"✓ Cleared {artifacts_cleared} old artifacts")

        # Check for manual splits
        manual_split_file = Path(f'data/manual_splits/{book_id}.json')
        use_manual_splits = manual_split_file.exists()

        # Prepare Step Functions input
        # Source PDFs are now in s3://jsmith-input/<artist>/<book>.pdf
        execution_input = {
            'book_id': book_id,
            'source_pdf_uri': f's3://{input_bucket}/{source_pdf}',
            'artist': artist,
            'book_name': book_name,
            'force_reprocess': force,
            'use_manual_splits': use_manual_splits,
            'manual_splits_path': f'data/manual_splits/{book_id}.json' if use_manual_splits else None
        }

        # Start execution
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f'reprocess-{book_id}-{int(time.time())}',
            input=json.dumps(execution_input)
        )

        return jsonify({
            'status': 'started',
            'execution_arn': response['executionArn'],
            'start_date': response['startDate'].isoformat(),
            'use_manual_splits': use_manual_splits
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/execution/<execution_arn>', methods=['GET'])
def get_execution_status(execution_arn):
    """Get Step Functions execution status"""
    try:
        response = stepfunctions.describe_execution(executionArn=execution_arn)

        return jsonify({
            'status': response['status'],
            'start_date': response['startDate'].isoformat(),
            'stop_date': response.get('stopDate', '').isoformat() if 'stopDate' in response else None,
            'input': json.loads(response['input']),
            'output': json.loads(response['output']) if 'output' in response else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/execution_progress/<path:execution_arn>', methods=['GET'])
def get_execution_progress(execution_arn):
    """Get detailed pipeline progress with step-by-step status"""
    try:
        # Get execution details
        exec_response = stepfunctions.describe_execution(executionArn=execution_arn)

        # Get execution history
        history_response = stepfunctions.get_execution_history(
            executionArn=execution_arn,
            maxResults=100,
            reverseOrder=True
        )

        # Define pipeline steps in order
        pipeline_steps = [
            'CheckAlreadyProcessed',
            'RecordProcessingStart',
            'TOCDiscovery',
            'TOCParsing',
            'ValidateTOC',
            'PageAnalysis',  # Added - runs after TOCParsing
            'PageMapping',
            'SongVerification',
            'ValidateVerification',
            'PDFSplitting',
            'ValidateOutput',
            'GenerateManifest',
            'RecordSuccess'
        ]

        # Parse history to determine step statuses
        step_status = {}
        current_step = None

        for event in history_response['events']:
            event_type = event['type']

            if event_type == 'TaskStateEntered' and 'stateEnteredEventDetails' in event:
                step_name = event['stateEnteredEventDetails']['name']
                if step_name in pipeline_steps:
                    step_status[step_name] = {
                        'status': 'running',
                        'start_time': event['timestamp'].isoformat()
                    }
                    current_step = step_name

            elif event_type == 'TaskStateExited' and 'stateExitedEventDetails' in event:
                step_name = event['stateExitedEventDetails']['name']
                if step_name in pipeline_steps and step_name in step_status:
                    step_status[step_name]['status'] = 'completed'
                    step_status[step_name]['end_time'] = event['timestamp'].isoformat()

            elif event_type == 'ChoiceStateEntered' and 'stateEnteredEventDetails' in event:
                step_name = event['stateEnteredEventDetails']['name']
                if step_name in pipeline_steps:
                    step_status[step_name] = {
                        'status': 'completed',
                        'start_time': event['timestamp'].isoformat(),
                        'end_time': event['timestamp'].isoformat()
                    }

        # Build step list with status
        steps = []
        for step_name in pipeline_steps:
            if step_name in step_status:
                steps.append({
                    'name': step_name,
                    'status': step_status[step_name]['status'],
                    'start_time': step_status[step_name].get('start_time'),
                    'end_time': step_status[step_name].get('end_time')
                })
            else:
                steps.append({
                    'name': step_name,
                    'status': 'pending',
                    'start_time': None,
                    'end_time': None
                })

        return jsonify({
            'execution_status': exec_response['status'],
            'start_date': exec_response['startDate'].isoformat(),
            'stop_date': exec_response.get('stopDate', '').isoformat() if 'stopDate' in exec_response else None,
            'current_step': current_step,
            'steps': steps,
            'input': json.loads(exec_response['input'])
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check_artifacts/<book_id>', methods=['GET'])
def check_artifacts(book_id):
    """Check which artifacts exist for a book"""
    try:
        artifacts = {}
        artifact_names = [
            'toc_discovery.json',
            'toc_parse.json',
            'page_mapping.json',
            'verified_songs.json',
            'output_files.json'
        ]

        for artifact in artifact_names:
            key = f'artifacts/{book_id}/{artifact}'
            try:
                s3.head_object(Bucket=BUCKET, Key=key)
                artifacts[artifact] = 'exists'
            except:
                artifacts[artifact] = 'missing'

        # Check manifest
        try:
            s3.head_object(Bucket=BUCKET, Key=f'output/{book_id}/manifest.json')
            artifacts['manifest.json'] = 'exists'
        except:
            artifacts['manifest.json'] = 'missing'

        return jsonify({
            'status': 'success',
            'book_id': book_id,
            'artifacts': artifacts
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/toc/<book_id>', methods=['GET'])
def get_toc(book_id):
    """Get TOC parse data from S3 artifacts"""
    try:
        key = f'artifacts/{book_id}/toc_parse.json'
        response = s3.get_object(Bucket=BUCKET, Key=key)
        toc_data = json.loads(response['Body'].read())
        return jsonify(toc_data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404

@app.route('/api/toc_discovery/<book_id>', methods=['GET'])
def get_toc_discovery(book_id):
    """Get raw TOC discovery data from S3 artifacts (includes OCR text)"""
    try:
        key = f'artifacts/{book_id}/toc_discovery.json'
        response = s3.get_object(Bucket=BUCKET, Key=key)
        discovery_data = json.loads(response['Body'].read())
        return jsonify(discovery_data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404


@app.route('/api/page_analysis/<book_id>', methods=['GET'])
def get_page_analysis(book_id):
    """Get comprehensive page analysis data from S3 artifacts.

    This contains pre-calculated:
    - Page offset (printed page vs PDF page)
    - Song boundaries with actual PDF page numbers
    - Per-page analysis (song titles, page numbers, content types)

    Generated during pipeline processing by the page_analyzer service.
    """
    try:
        key = f'artifacts/{book_id}/page_analysis.json'
        response = s3.get_object(Bucket=BUCKET, Key=key)
        analysis_data = json.loads(response['Body'].read())
        return jsonify(analysis_data)
    except s3.exceptions.NoSuchKey:
        return jsonify({'status': 'not_found', 'message': 'Page analysis not available - reprocess with latest pipeline'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404

@app.route('/api/page_mapping/<book_id>', methods=['GET'])
def get_page_mapping(book_id):
    """Get verified page mapping from S3 artifacts.

    This contains the VERIFIED song locations from the improved page mapper.
    Use this as the PRIMARY source for song positions - it has been validated
    with vision verification and is more accurate than page_analysis.songs.
    """
    try:
        key = f'artifacts/{book_id}/page_mapping.json'
        response = s3.get_object(Bucket=BUCKET, Key=key)
        mapping_data = json.loads(response['Body'].read())
        return jsonify(mapping_data)
    except s3.exceptions.NoSuchKey:
        return jsonify({'status': 'not_found', 'message': 'Page mapping not available'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404


@app.route('/api/detect_page_number/<book_id>/<int:pdf_page>', methods=['GET'])
def detect_page_number(book_id, pdf_page):
    """Use Claude vision to detect the printed page number (distinguishes from other numbers)"""
    import base64
    try:
        # Get source PDF
        response = TABLE.get_item(Key={'book_id': book_id})
        if 'Item' not in response or 'source_pdf_uri' not in response['Item']:
            return jsonify({'status': 'error', 'message': 'Book not found'}), 404

        source_pdf_uri = response['Item']['source_pdf_uri']
        parts = source_pdf_uri[5:].split('/', 1) if source_pdf_uri.startswith('s3://') else (None, None)
        if not parts[0]:
            return jsonify({'status': 'error', 'message': 'Invalid S3 URI'}), 400

        input_bucket, source_key = parts

        # Render page
        pdf_response = s3.get_object(Bucket=input_bucket, Key=source_key)
        pdf_bytes = pdf_response['Body'].read()
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')

        if pdf_page < 1 or pdf_page > len(doc):
            doc.close()
            return jsonify({'status': 'error', 'message': 'Invalid page'}), 400

        page = doc[pdf_page - 1]
        zoom = 150 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        doc.close()

        # Use Claude vision to identify page number with context
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        # Encode image to base64
        image_b64 = base64.b64encode(png_bytes).decode('utf-8')

        prompt = """Look at this sheet music page. What is the PRINTED PAGE NUMBER displayed on this page?

The page number is usually shown in one of the corners or at the top/bottom center of the page.
It's distinct from other numbers on the page like:
- Chord numbers (like D9/6, Em, etc.)
- Measure numbers
- Fingering numbers
- Time signatures

Please respond ONLY with the page number as a single integer, or "NONE" if no page number is visible.
Examples: "9", "23", "156", "NONE"

Your response:"""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "temperature": 0,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        }

        bedrock_response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )

        response_body = json.loads(bedrock_response['body'].read())
        page_number_str = response_body['content'][0]['text'].strip()

        # Parse response
        if page_number_str == "NONE" or not page_number_str.isdigit():
            return jsonify({'status': 'not_found', 'pdf_page': pdf_page})

        printed_page = int(page_number_str)
        return jsonify({
            'status': 'success',
            'pdf_page': pdf_page,
            'printed_page': printed_page,
            'offset': printed_page - pdf_page
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/calibrate_offset/<book_id>', methods=['GET'])
def calibrate_offset(book_id):
    """
    Smart offset calibration using song titles from TOC.

    Uses PyMuPDF positional text extraction to find song titles at the TOP of pages
    (where titles appear) vs lyrics in the middle. Also checks font size - titles are larger.
    """
    import re
    try:
        # Get TOC data first
        toc_key = f'artifacts/{book_id}/toc_parse.json'
        try:
            toc_response = s3.get_object(Bucket=BUCKET, Key=toc_key)
            toc_data = json.loads(toc_response['Body'].read())
            toc_entries = toc_data.get('entries', [])
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Could not load TOC: {str(e)}'}), 404

        if not toc_entries:
            return jsonify({'status': 'error', 'message': 'No TOC entries found'}), 404

        # Sort by page number and get the first few songs to try
        sorted_entries = sorted(toc_entries, key=lambda x: x.get('page_number', 999))

        # Get source PDF
        response = TABLE.get_item(Key={'book_id': book_id})
        if 'Item' not in response or 'source_pdf_uri' not in response['Item']:
            return jsonify({'status': 'error', 'message': 'Book not found in ledger'}), 404

        source_pdf_uri = response['Item']['source_pdf_uri']
        parts = source_pdf_uri[5:].split('/', 1) if source_pdf_uri.startswith('s3://') else (None, None)
        if not parts[0]:
            return jsonify({'status': 'error', 'message': 'Invalid S3 URI'}), 400

        input_bucket, source_key = parts

        # Download PDF
        pdf_response = s3.get_object(Bucket=input_bucket, Key=source_key)
        pdf_bytes = pdf_response['Body'].read()
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        total_pages = len(doc)

        print(f"PDF has {total_pages} pages")

        # Try to find the first few songs to calibrate
        songs_to_try = sorted_entries[:5]  # Try first 5 songs

        found_calibrations = []

        for song_entry in songs_to_try:
            song_title = song_entry['song_title']
            printed_page = song_entry['page_number']

            # Create search patterns - handle variations
            title_clean = re.sub(r'[^\w\s]', '', song_title).strip()
            title_words = [w for w in title_clean.upper().split() if len(w) > 2]

            if not title_words:
                continue

            print(f"\nLooking for '{song_title}' (printed page {printed_page})...")
            print(f"  Key words: {title_words}")

            # Search through PDF pages
            max_pages_to_scan = min(40, total_pages)

            for pdf_page_idx in range(max_pages_to_scan):
                page = doc[pdf_page_idx]
                page_height = page.rect.height

                # Get text with position and font info using "dict" mode
                text_dict = page.get_text("dict")

                # Look for title in the TOP 25% of the page with larger font
                title_found_at_top = False
                title_font_size = 0

                for block in text_dict.get("blocks", []):
                    if block.get("type") != 0:  # Skip non-text blocks
                        continue

                    for line in block.get("lines", []):
                        # Get line's vertical position (y0 is top of line)
                        line_y = line.get("bbox", [0, 0, 0, 0])[1]
                        is_in_top_quarter = line_y < page_height * 0.25

                        # Get text and font size from spans
                        line_text = ""
                        max_font_size = 0

                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                            font_size = span.get("size", 0)
                            if font_size > max_font_size:
                                max_font_size = font_size

                        line_text_upper = line_text.upper()

                        # Check if title words are in this line
                        words_in_line = sum(1 for word in title_words if word in line_text_upper)
                        match_ratio = words_in_line / len(title_words)

                        # Title criteria:
                        # 1. Most/all key words present
                        # 2. In top 25% of page OR has large font (>12pt typically for titles)
                        # 3. Larger fonts get priority
                        is_title_sized = max_font_size >= 12

                        if match_ratio >= 0.7 and (is_in_top_quarter or is_title_sized):
                            if max_font_size > title_font_size:
                                title_found_at_top = True
                                title_font_size = max_font_size
                                print(f"    Page {pdf_page_idx + 1}: Found '{line_text.strip()}' at y={line_y:.0f} ({line_y/page_height*100:.0f}% down), font={max_font_size:.1f}pt")

                if title_found_at_top:
                    pdf_page = pdf_page_idx + 1  # Convert to 1-indexed
                    offset = printed_page - pdf_page

                    print(f"  => MATCHED on PDF page {pdf_page} (font size {title_font_size:.1f}pt)")

                    found_calibrations.append({
                        'song_title': song_title,
                        'printed_page': printed_page,
                        'pdf_page': pdf_page,
                        'offset': offset,
                        'font_size': title_font_size
                    })
                    break

        doc.close()

        if not found_calibrations:
            return jsonify({
                'status': 'not_found',
                'message': 'Could not find any song titles in PDF (checked top of pages for title-sized text)',
                'songs_tried': [s['song_title'] for s in songs_to_try]
            }), 404

        # Calculate consensus offset (most common)
        offsets = [c['offset'] for c in found_calibrations]
        from collections import Counter
        offset_counts = Counter(offsets)
        consensus_offset = offset_counts.most_common(1)[0][0]

        # Use the first song that matches the consensus offset for reporting
        primary = next((c for c in found_calibrations if c['offset'] == consensus_offset), found_calibrations[0])

        print(f"\n=== CALIBRATION RESULT ===")
        print(f"Consensus offset: {consensus_offset}")
        print(f"Based on {len(found_calibrations)} song matches:")
        for c in found_calibrations:
            marker = "***" if c['offset'] == consensus_offset else ""
            print(f"  {marker} '{c['song_title']}': printed {c['printed_page']} = PDF {c['pdf_page']} (offset {c['offset']}, {c['font_size']:.1f}pt)")

        return jsonify({
            'status': 'success',
            'offset': consensus_offset,
            'calibration_method': 'positional_text',
            'song_title': primary['song_title'],
            'printed_page': primary['printed_page'],
            'pdf_page': primary['pdf_page'],
            'total_pdf_pages': total_pages,
            'calibration_points': found_calibrations
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/render_page/<book_id>/<int:page_num>', methods=['GET'])
def render_page(book_id, page_num):
    """Render a specific page from a source PDF as PNG"""
    try:
        # Get the source PDF path from book_id
        # Book ID format: "Artist___Book_Name" (underscores)
        # Need to find the actual PDF in jsmith-input bucket

        # First, try to get the source PDF path from DynamoDB ledger
        try:
            response = TABLE.get_item(Key={'book_id': book_id})
            if 'Item' in response and 'source_pdf_uri' in response['Item']:
                source_pdf_uri = response['Item']['source_pdf_uri']
                # Extract S3 key from URI (format: s3://bucket/key)
                if source_pdf_uri.startswith('s3://'):
                    parts = source_pdf_uri[5:].split('/', 1)
                    if len(parts) == 2:
                        input_bucket, source_key = parts
                    else:
                        return jsonify({'status': 'error', 'message': 'Invalid S3 URI format'}), 400
                else:
                    return jsonify({'status': 'error', 'message': 'Invalid source_pdf_uri'}), 400
            else:
                return jsonify({'status': 'error', 'message': 'Book not found in ledger'}), 404
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error accessing ledger: {str(e)}'}), 500

        # Download PDF from S3 to memory
        pdf_response = s3.get_object(Bucket=input_bucket, Key=source_key)
        pdf_bytes = pdf_response['Body'].read()

        # Open PDF with PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')

        # Check page number validity
        if page_num < 1 or page_num > len(doc):
            doc.close()
            return jsonify({'status': 'error', 'message': f'Invalid page number. PDF has {len(doc)} pages'}), 400

        # Render page (page_num is 1-indexed, but fitz is 0-indexed)
        page = doc[page_num - 1]

        # Check for size parameter (for thumbnails)
        size_param = request.args.get('size', 'normal')
        if size_param == 'small':
            # Render at lower resolution for thumbnails
            zoom = 72 / 72  # 72 DPI for small thumbnails
        else:
            # Render at 150 DPI for good quality but reasonable size
            zoom = 150 / 72

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PNG in memory
        png_bytes = pix.tobytes("png")
        doc.close()

        # Return PNG image
        return send_file(
            io.BytesIO(png_bytes),
            mimetype='image/png',
            as_attachment=False
        )

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/manual_split/<book_id>', methods=['GET', 'POST'])
def manual_split(book_id):
    """Get or save manual split points"""
    manual_split_file = Path(f'data/manual_splits/{book_id}.json')

    if request.method == 'GET':
        if manual_split_file.exists():
            with open(manual_split_file, 'r') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({'status': 'not_found'})

    elif request.method == 'POST':
        # Save manual split points
        data = request.json
        manual_split_file.parent.mkdir(parents=True, exist_ok=True)

        with open(manual_split_file, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({'status': 'saved', 'path': str(manual_split_file)})

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'pipeline-api'})

if __name__ == '__main__':
    print('='*80)
    print('Pipeline API Server')
    print('='*80)
    print('Starting server on http://localhost:5000')
    print()
    print('Endpoints:')
    print('  GET  /api/health')
    print('  GET  /api/status/<book_id>')
    print('  POST /api/reprocess')
    print('  GET  /api/execution/<execution_arn>')
    print('  GET  /api/check_artifacts/<book_id>')
    print('  GET/POST /api/manual_split/<book_id>')
    print('  GET  /api/calibrate_offset/<book_id> - Auto-calibrate page offset')
    print('  GET  /api/page_analysis/<book_id> - Get pre-computed page analysis')
    print('  GET  /api/render_page/<book_id>/<page_num> - Render PDF page')
    print()
    print('Open the provenance viewer to use action buttons')
    print('='*80)

    # Create manual_splits directory if it doesn't exist
    Path('data/manual_splits').mkdir(parents=True, exist_ok=True)

    app.run(host='0.0.0.0', port=5000, debug=True)
