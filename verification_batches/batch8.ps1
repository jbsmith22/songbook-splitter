# Batch 8 - 624 PDFs
# Artists: Whitney Houston, Henri Mancini, Colbie Caillat, Fray, Led Zepplin...

Write-Host "=" * 80
Write-Host "Starting Batch 8"
Write-Host "PDFs: 624"
Write-Host "Artists: 59"
Write-Host "=" * 80

# Change to parent directory where the Python scripts are
Set-Location ..

# Run verification
py run_verification_with_output.py verification_batches/batch8_files.txt

# Generate review page
py generate_review_page.py

# Rename output files to include batch number
Move-Item -Force verification_results/bedrock_results.json verification_results/batch8_results.json
Move-Item -Force verification_results/review_page.html verification_results/batch8_review.html

Write-Host ""
Write-Host "Batch 8 complete!"
Write-Host "Review at: verification_results/batch8_review.html"
Write-Host ""
