# Run all verification batches sequentially
# Total batches: 8

$batches = @(
    "batch1.ps1",
    "batch2.ps1",
    "batch3.ps1",
    "batch4.ps1",
    "batch5.ps1",
    "batch6.ps1",
    "batch7.ps1",
    "batch8.ps1"
)

foreach ($batch in $batches) {
    Write-Host ""
    Write-Host "=" * 80
    Write-Host "Running $batch"
    Write-Host "=" * 80
    Write-Host ""
    
    & ".\$batch"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error running $batch - stopping"
        exit 1
    }
}

Write-Host ""
Write-Host "=" * 80
Write-Host "All batches complete!"
Write-Host "=" * 80
Write-Host ""
Write-Host "Review pages:"
Write-Host "  Batch 1: verification_results/batch1_review.html"
Write-Host "  Batch 2: verification_results/batch2_review.html"
Write-Host "  Batch 3: verification_results/batch3_review.html"
Write-Host "  Batch 4: verification_results/batch4_review.html"
Write-Host "  Batch 5: verification_results/batch5_review.html"
Write-Host "  Batch 6: verification_results/batch6_review.html"
Write-Host "  Batch 7: verification_results/batch7_review.html"
Write-Host "  Batch 8: verification_results/batch8_review.html"
