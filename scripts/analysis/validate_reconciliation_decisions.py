"""
Validate that reconciliation decisions are still valid and executable
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# AWS setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Paths
local_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')
archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')

# Load decisions
print("Loading reconciliation decisions...")
with open('reconciliation_decisions_2026-02-02_translated.json', 'r') as f:
    decisions_data = json.load(f)

decisions = decisions_data.get('decisions', {})
print(f"Found {len(decisions)} folders with decisions\n")

stats = defaultdict(int)
issues = []
valid_decisions = {}

for folder_key, folder_decision in decisions.items():
    local_path = folder_decision.get('local_path', '')
    s3_path = folder_decision.get('s3_path', '')
    file_decisions = folder_decision.get('fileDecisions', {})

    stats['total_folders'] += 1
    stats['total_files'] += len(file_decisions)

    # Check if folder is archived (shouldn't be in decisions if archived)
    local_folder = local_root / local_path
    archive_folder = archive_root / local_path

    if archive_folder.exists() and not local_folder.exists():
        issues.append({
            'folder': folder_key,
            'type': 'folder_archived',
            'message': f'Folder has been archived: {local_path}',
            'severity': 'error'
        })
        stats['folders_archived'] += 1
        continue

    if not local_folder.exists():
        issues.append({
            'folder': folder_key,
            'type': 'local_folder_missing',
            'message': f'Local folder does not exist: {local_path}',
            'severity': 'error'
        })
        stats['local_folder_missing'] += 1
        continue

    # Validate each file decision
    folder_valid = True
    validated_file_decisions = {}

    for filename, file_decision in file_decisions.items():
        action = file_decision.get('action', '')
        local_size = file_decision.get('local_size')
        s3_size = file_decision.get('s3_size')

        local_file = local_folder / filename
        s3_key = f"{s3_path}/{filename}"

        file_valid = True
        file_issues = []

        # Validate based on action type
        if action in ['copy-local-to-s3-overwrite', 'copy-local-to-s3']:
            # Local file must exist
            if not local_file.exists():
                file_issues.append(f"Local file missing: {filename}")
                file_valid = False
            else:
                # Check if size still matches
                actual_local_size = local_file.stat().st_size
                if local_size and actual_local_size != local_size:
                    file_issues.append(f"Local size changed: {filename} (expected {local_size}, actual {actual_local_size})")
                    # Update the size in decision
                    file_decision['local_size'] = actual_local_size
                    file_decision['size_changed'] = True

        elif action in ['copy-s3-to-local-overwrite', 'copy-s3-to-local']:
            # S3 file must exist
            try:
                response = s3_client.head_object(Bucket=bucket, Key=s3_key)
                actual_s3_size = response['ContentLength']
                if s3_size and actual_s3_size != s3_size:
                    file_issues.append(f"S3 size changed: {filename} (expected {s3_size}, actual {actual_s3_size})")
                    file_decision['s3_size'] = actual_s3_size
                    file_decision['size_changed'] = True
            except Exception as e:
                file_issues.append(f"S3 file missing: {filename}")
                file_valid = False

        elif action == 'delete-from-local':
            # File should exist locally to delete
            if not local_file.exists():
                file_issues.append(f"Local file already deleted: {filename}")
                # Not really an error, just skip
                file_decision['already_done'] = True

        elif action == 'delete-from-s3':
            # Check if S3 file exists
            try:
                s3_client.head_object(Bucket=bucket, Key=s3_key)
            except:
                file_issues.append(f"S3 file already deleted: {filename}")
                file_decision['already_done'] = True

        elif action == 'no-action':
            # Verify files match
            if local_file.exists():
                try:
                    response = s3_client.head_object(Bucket=bucket, Key=s3_key)
                    actual_s3_size = response['ContentLength']
                    actual_local_size = local_file.stat().st_size

                    if actual_local_size != actual_s3_size:
                        file_issues.append(f"Files no longer match: {filename} (local {actual_local_size}, S3 {actual_s3_size})")
                        file_valid = False
                except:
                    file_issues.append(f"S3 file missing for no-action: {filename}")
                    file_valid = False

        else:
            file_issues.append(f"Unknown action: {action}")
            file_valid = False

        if file_issues:
            issues.append({
                'folder': folder_key,
                'file': filename,
                'type': 'file_validation_issue',
                'issues': file_issues,
                'severity': 'error' if not file_valid else 'warning'
            })
            stats['file_issues'] += 1

        if file_valid or file_decision.get('already_done'):
            validated_file_decisions[filename] = file_decision
            stats['valid_files'] += 1
        else:
            stats['invalid_files'] += 1
            folder_valid = False

    # Keep folder if it has at least some valid decisions
    if validated_file_decisions:
        valid_decisions[folder_key] = {
            **folder_decision,
            'fileDecisions': validated_file_decisions
        }
        stats['valid_folders'] += 1
    else:
        stats['invalid_folders'] += 1

print(f"\n{'='*70}")
print("VALIDATION SUMMARY")
print(f"{'='*70}")
print(f"Total folders:              {stats['total_folders']}")
print(f"Valid folders:              {stats['valid_folders']}")
print(f"Invalid folders:            {stats['invalid_folders']}")
print(f"Folders archived:           {stats['folders_archived']}")
print(f"Local folder missing:       {stats['local_folder_missing']}")
print()
print(f"Total file decisions:       {stats['total_files']}")
print(f"Valid file decisions:       {stats['valid_files']}")
print(f"Invalid file decisions:     {stats['invalid_files']}")
print(f"File validation issues:     {stats['file_issues']}")

# Show issues by severity
errors = [i for i in issues if i.get('severity') == 'error']
warnings = [i for i in issues if i.get('severity') == 'warning']

if errors:
    print(f"\n{'='*70}")
    print(f"ERRORS ({len(errors)})")
    print(f"{'='*70}")
    for issue in errors[:20]:
        if issue['type'] == 'folder_archived':
            print(f"\n{issue['folder']}")
            print(f"  ERROR: {issue['message']}")
        elif issue['type'] == 'local_folder_missing':
            print(f"\n{issue['folder']}")
            print(f"  ERROR: {issue['message']}")
        elif issue['type'] == 'file_validation_issue':
            print(f"\n{issue['folder']} / {issue['file']}")
            for file_issue in issue['issues']:
                print(f"  ERROR: {file_issue}")
    if len(errors) > 20:
        print(f"\n  ... and {len(errors) - 20} more errors")

if warnings:
    print(f"\n{'='*70}")
    print(f"WARNINGS ({len(warnings)})")
    print(f"{'='*70}")
    for issue in warnings[:10]:
        if issue['type'] == 'file_validation_issue':
            print(f"\n{issue['folder']} / {issue['file']}")
            for file_issue in issue['issues']:
                print(f"  WARNING: {file_issue}")
    if len(warnings) > 10:
        print(f"\n  ... and {len(warnings) - 10} more warnings")

# Save validated decisions
if valid_decisions:
    output_file = 'reconciliation_decisions_2026-02-02_validated.json'
    with open(output_file, 'w') as f:
        json.dump({
            'validation_timestamp': '2026-02-02',
            'original_count': len(decisions),
            'validated_count': len(valid_decisions),
            'decisions': valid_decisions
        }, f, indent=2)

    print(f"\n{'='*70}")
    print("OUTPUT")
    print(f"{'='*70}")
    print(f"Validated decisions saved to: {output_file}")
    print(f"Original decisions: {len(decisions)}")
    print(f"Validated decisions: {len(valid_decisions)}")
    print(f"Removed: {len(decisions) - len(valid_decisions)}")

print("\nValidation complete!")
