"""
Pipeline API Server - Local server to bridge viewer and AWS pipeline

Run this to enable reprocessing from the viewer:
    py scripts/pipeline_api_server.py

Then open the viewer and use the action buttons.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import time
from pathlib import Path

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

        # Check for manual splits
        manual_split_file = Path(f'data/manual_splits/{book_id}.json')
        use_manual_splits = manual_split_file.exists()

        # Prepare Step Functions input
        execution_input = {
            'book_id': book_id,
            'source_pdf_uri': f's3://{BUCKET}/SheetMusic/{source_pdf}',
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
    print()
    print('Open the provenance viewer to use action buttons')
    print('='*80)

    # Create manual_splits directory if it doesn't exist
    Path('data/manual_splits').mkdir(parents=True, exist_ok=True)

    app.run(host='0.0.0.0', port=5000, debug=True)
