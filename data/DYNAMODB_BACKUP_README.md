# DynamoDB Backup and Restore

## Backup Information

**Date**: February 14, 2026
**Table**: `jsmith-pipeline-ledger`
**Records**: 399 books
**File**: `dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json`
**Size**: 1.6 MB

## Backup Contents

The backup contains complete processing records for 399 books across 121 artists:
- Book metadata (artist, book_name, book_id)
- Processing status and timestamps
- Step-by-step execution data (toc_discovery, toc_parse, page_analysis, page_mapping, pdf_splitter)
- Song counts and page counts
- S3 URIs for source PDFs
- Processing duration and performance metrics

## Creating a New Backup

```bash
# Export current table to JSON
aws dynamodb scan --table-name jsmith-pipeline-ledger --output json > data/dynamodb_backup_jsmith-pipeline-ledger_$(date +%Y-%m-%d).json

# Verify backup
python -c "import json; data=json.load(open('data/dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json')); print(f'Records: {len(data[\"Items\"])}')"
```

## Restoring from Backup

### Option 1: Restore Individual Items (Recommended)

Use the AWS CLI to put individual items back into the table:

```bash
# Extract and restore each item
python scripts/restore_dynamodb.py --backup-file data/dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json --table jsmith-pipeline-ledger
```

### Option 2: Batch Write (For complete table restoration)

```bash
# Create restore script
python <<'EOF'
import json
import boto3
from decimal import Decimal

# Load backup
with open('data/dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json', 'r') as f:
    backup = json.load(f)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-pipeline-ledger')

# Convert numbers to Decimal for DynamoDB
def convert_decimals(obj):
    if isinstance(obj, dict):
        if 'N' in obj:
            return Decimal(obj['N'])
        elif 'S' in obj:
            return obj['S']
        elif 'M' in obj:
            return {k: convert_decimals(v) for k, v in obj['M'].items()}
        elif 'L' in obj:
            return [convert_decimals(item) for item in obj['L']]
        else:
            return {k: convert_decimals(v) for k, v in obj.items()}
    return obj

# Restore items in batches of 25 (DynamoDB limit)
items = [convert_decimals(item) for item in backup['Items']]
for i in range(0, len(items), 25):
    batch = items[i:i+25]
    with table.batch_writer() as writer:
        for item in batch:
            writer.put_item(Item=item)
    print(f'Restored {min(i+25, len(items))}/{len(items)} items')
EOF
```

### Option 3: Create New Table from Backup

```bash
# 1. Create new table with same schema
aws dynamodb create-table \
    --table-name jsmith-pipeline-ledger-restored \
    --attribute-definitions \
        AttributeName=book_id,AttributeType=S \
    --key-schema \
        AttributeName=book_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# 2. Wait for table to be active
aws dynamodb wait table-exists --table-name jsmith-pipeline-ledger-restored

# 3. Restore data using Option 2 script above (change table name)
```

## Verify Restoration

```bash
# Count items in restored table
aws dynamodb scan --table-name jsmith-pipeline-ledger --select COUNT

# Compare with backup
python -c "import json; data=json.load(open('data/dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json')); print(f'Backup records: {len(data[\"Items\"])}')"
```

## Backup Schedule Recommendation

Create regular backups:
- **Daily**: During active processing phases
- **Weekly**: During maintenance phases
- **Before major changes**: Always backup before pipeline updates

Store backups in multiple locations:
- Local: `data/` directory
- S3: `s3://jsmith-backups/dynamodb/`
- External: Copy to external backup system

## Table Schema

**Primary Key**: `book_id` (String, Hash Key)

**Attributes**:
- `artist` (String): Artist name
- `book_name` (String): Book title
- `status` (String): Processing status (success, failed, in_progress)
- `pipeline_version` (String): Pipeline version (v3)
- `songs_extracted` (Number): Total songs extracted
- `total_pages` (Number): Total pages in book
- `source_pdf_uri` (String): S3 URI of input PDF
- `created_at` (String): ISO timestamp
- `updated_at` (String): ISO timestamp
- `steps` (Map): Detailed step execution data
  - `toc_discovery` (Map)
  - `toc_parse` (Map)
  - `page_analysis` (Map)
  - `page_mapping` (Map)
  - `pdf_splitter` (Map)

## Notes

- The backup is in native DynamoDB JSON format (type descriptors like `{"S": "value"}`, `{"N": "123"}`)
- Numbers are stored as strings in DynamoDB format and must be converted to Python `Decimal` type for restoration
- The table uses on-demand billing mode (no provisioned capacity required)
- All timestamps are in ISO 8601 UTC format
