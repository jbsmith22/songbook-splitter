# Git Checkpoint Commit Script
# Commits all project files for checkpoint 2026-01-28

$ErrorActionPreference = "Stop"

Write-Host "=== Git Checkpoint Commit ===" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
    Write-Host ""
}

# Stage core application code
Write-Host "Staging application code..." -ForegroundColor Yellow
git add app/
git add lambda/
git add ecs/
git add tests/

# Stage infrastructure
Write-Host "Staging infrastructure..." -ForegroundColor Yellow
git add infra/
git add Dockerfile
git add requirements.txt

# Stage scripts
Write-Host "Staging scripts..." -ForegroundColor Yellow
git add *.ps1
git add *.py
git add local_runner.py

# Stage documentation
Write-Host "Staging documentation..." -ForegroundColor Yellow
git add README.md
git add START_HERE.md
git add PROJECT_CHECKPOINT_2026-01-28.md
git add PROJECT_STATUS_REPORT.md
git add PROJECT_CONTEXT.md
git add .kiro/specs/

# Stage inventory files
Write-Host "Staging inventory files..." -ForegroundColor Yellow
git add source-books-status-final.csv
git add processed-books-with-pdfs.csv

# Create .gitignore if it doesn't exist
if (-not (Test-Path ".gitignore")) {
    Write-Host "Creating .gitignore..." -ForegroundColor Yellow
    @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.pytest_cache/
.coverage
htmlcov/

# AWS
.aws/
*.zip
lambda-deployment.zip
lambda-package/

# Local data
SheetMusic/
ProcessedSongs/
test_output/
output/
temp_*/
*.pdf

# Logs
*.log

# Temporary files
temp-*.json
temp-*.txt
temp-*.csv

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Test artifacts
test-*.pdf
*-execution-*.json
*-execution-*.csv
"@ | Out-File -FilePath ".gitignore" -Encoding utf8
    git add .gitignore
    Write-Host "✅ .gitignore created" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Staged Files ===" -ForegroundColor Cyan
git status --short

Write-Host ""
Write-Host "=== Creating Commit ===" -ForegroundColor Cyan

$commitMessage = @"
Checkpoint 2026-01-28: 541/562 books processed (96.3% complete)

## Summary
- All AWS infrastructure deployed and operational
- 541 books successfully processed into individual songs
- 21 books remaining to process
- 244/245 unit tests passing (99.6%)
- Complete inventory reconciliation
- Updated documentation and specifications

## Statistics
- Total Source Books: 562
- Successfully Processed: 541 (96.3%)
- Remaining to Process: 21 (3.7%)
- Test Pass Rate: 99.6%

## Key Files
- PROJECT_CHECKPOINT_2026-01-28.md: Complete checkpoint document
- source-books-status-final.csv: Full inventory mapping
- processed-books-with-pdfs.csv: Successfully processed books

## Architecture
- 6-stage AWS Step Functions pipeline
- ECS Fargate for compute-intensive tasks
- Lambda for orchestration
- DynamoDB for state tracking
- S3 for input/output storage

## Next Steps
1. Process remaining 21 books
2. Final verification
3. Project completion
"@

git commit -m $commitMessage

Write-Host ""
Write-Host "✅ Commit created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To push to remote (if configured):" -ForegroundColor Yellow
Write-Host "  git remote add origin <repository-url>" -ForegroundColor Gray
Write-Host "  git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "=== Commit Complete ===" -ForegroundColor Cyan
