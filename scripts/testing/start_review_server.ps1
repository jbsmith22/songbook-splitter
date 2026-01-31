# Start the split detection server for auto-detection feature

Write-Host "Starting Split Detection Server..." -ForegroundColor Green
Write-Host ""
Write-Host "This server enables the 'Auto-detect Songs' feature in the review interface."
Write-Host "Keep this window open while reviewing PDFs."
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

# Check if Flask is installed
$flaskInstalled = py -c "import flask" 2>$null
$corsInstalled = py -c "import flask_cors" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing required packages (Flask and Flask-CORS)..." -ForegroundColor Yellow
    py -m pip install flask flask-cors
    Write-Host ""
}

# Start server
py split_detection_server.py
