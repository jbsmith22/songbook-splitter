# Check Ollama performance and GPU usage

Write-Host "Checking Ollama GPU usage..." -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is using GPU
Write-Host "GPU Status:" -ForegroundColor Yellow
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

Write-Host ""
Write-Host "Ollama Process:" -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*ollama*"} | Select-Object ProcessName, CPU, WorkingSet64, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet64/1MB,2)}}

Write-Host ""
Write-Host "Testing Ollama response time..." -ForegroundColor Yellow
$start = Get-Date

# Simple test without image
$response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body (@{
    model = "llama3.2-vision:11b"
    prompt = "Say hello"
    stream = $false
} | ConvertTo-Json) -ContentType "application/json"

$elapsed = (Get-Date) - $start
Write-Host "Simple prompt response time: $($elapsed.TotalSeconds) seconds" -ForegroundColor Green
