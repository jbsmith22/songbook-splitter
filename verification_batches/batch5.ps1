# Batch 5 - 1923 PDFs
# Artists: Billy Joel, ProcessedSongs, _broadway Shows

Write-Host "=" * 80
Write-Host "Starting Batch 5"
Write-Host "PDFs: 1923"
Write-Host "Artists: 3"
Write-Host "=" * 80

# Change to parent directory where the Python scripts are
Set-Location ..

# Run verification
py run_verification_with_output.py verification_batches/batch5_files.txt

# Generate review page
py generate_review_page.py

# Rename output files to include batch number
Move-Item -Force verification_results/bedrock_results.json verification_results/batch5_results.json
Move-Item -Force verification_results/review_page.html verification_results/batch5_review.html

Write-Host ""
Write-Host "Batch 5 complete!"
Write-Host "Review at: verification_results/batch5_review.html"
Write-Host ""
