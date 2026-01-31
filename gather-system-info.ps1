# Gather system information for PDF verification setup

Write-Host "=== System Information for PDF Verification ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check Ollama installation and models
Write-Host "1. Ollama Installation:" -ForegroundColor Yellow
try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "   Ollama Version: $ollamaVersion" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "   Installed Models:" -ForegroundColor Yellow
    ollama list
} catch {
    Write-Host "   Ollama not found or not in PATH" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. Ollama Service Status:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   Ollama is running on http://localhost:11434" -ForegroundColor Green
} catch {
    Write-Host "   Ollama is NOT running on http://localhost:11434" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. ProcessedSongs Directory:" -ForegroundColor Yellow
$processedPath = "C:\Work\AWSMusic\ProcessedSongs"
if (Test-Path $processedPath) {
    Write-Host "   Path exists: $processedPath" -ForegroundColor Green
    
    # Count total PDFs
    Write-Host "   Counting PDF files (this may take a moment)..." -ForegroundColor Gray
    $pdfCount = (Get-ChildItem -Path $processedPath -Filter "*.pdf" -Recurse -File).Count
    Write-Host "   Total PDF files: $pdfCount" -ForegroundColor Green
    
    # Count artists
    $artistCount = (Get-ChildItem -Path $processedPath -Directory).Count
    Write-Host "   Total artist folders: $artistCount" -ForegroundColor Green
} else {
    Write-Host "   Path does NOT exist: $processedPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Python Installation:" -ForegroundColor Yellow
try {
    $pythonVersion = py --version 2>&1
    Write-Host "   Python Version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   Python (py) not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "5. Required Python Packages:" -ForegroundColor Yellow
$packages = @("pymupdf", "pillow", "requests")
foreach ($pkg in $packages) {
    try {
        $installed = py -m pip show $pkg 2>&1 | Select-String "Version:"
        if ($installed) {
            Write-Host "   $pkg : $installed" -ForegroundColor Green
        } else {
            Write-Host "   $pkg : NOT INSTALLED" -ForegroundColor Red
        }
    } catch {
        Write-Host "   $pkg : NOT INSTALLED" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "6. System Resources:" -ForegroundColor Yellow
$cpu = Get-WmiObject Win32_Processor | Select-Object -First 1
Write-Host "   CPU: $($cpu.Name)" -ForegroundColor Green
Write-Host "   CPU Cores: $($cpu.NumberOfCores)" -ForegroundColor Green
Write-Host "   CPU Logical Processors: $($cpu.NumberOfLogicalProcessors)" -ForegroundColor Green

$ram = Get-WmiObject Win32_ComputerSystem
$ramGB = [math]::Round($ram.TotalPhysicalMemory / 1GB, 2)
Write-Host "   RAM: $ramGB GB" -ForegroundColor Green

Write-Host ""
Write-Host "7. Disk Space (C: drive):" -ForegroundColor Yellow
$disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
$totalGB = [math]::Round($disk.Size / 1GB, 2)
Write-Host "   Free Space: $freeGB GB / $totalGB GB" -ForegroundColor Green

Write-Host ""
Write-Host "=== Information Gathering Complete ===" -ForegroundColor Cyan
