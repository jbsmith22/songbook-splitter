# Batch 4 - 1564 PDFs
# Artists: Beatles

Write-Host "=" * 80
Write-Host "Starting Batch 4"
Write-Host "PDFs: 1564"
Write-Host "Artists: 1"
Write-Host "=" * 80

# Change to parent directory where the Python scripts are
Set-Location ..

# Run verification
py run_verification_with_output.py verification_batches/batch4_files.txt

# Generate review page
py generate_review_page.py

# Rename output files to include batch number
Move-Item -Force verification_results/bedrock_results.json verification_results/batch4_results.json
Move-Item -Force verification_results/review_page.html verification_results/batch4_review.html

Write-Host ""
Write-Host "Batch 4 complete!"
Write-Host "Review at: verification_results/batch4_review.html"
Write-Host ""
