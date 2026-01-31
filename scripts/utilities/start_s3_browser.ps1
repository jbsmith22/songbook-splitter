# Start S3 Browser Server
Write-Host "🚀 Starting S3 Browser Server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Features:" -ForegroundColor Yellow
Write-Host "  📁 Browse S3 folder structure"
Write-Host "  🗑️  Delete files and folders"
Write-Host "  📊 Compare two folders byte-by-byte"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

py s3_browser_server.py
