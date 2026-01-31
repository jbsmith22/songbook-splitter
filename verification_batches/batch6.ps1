# Batch 6 - 1931 PDFs
# Artists: Genesis, Journey, Paul Mccartney, Neil Young, Carole King...

Write-Host "=" * 80
Write-Host "Starting Batch 6"
Write-Host "PDFs: 1931"
Write-Host "Artists: 13"
Write-Host "=" * 80

# Change to parent directory where the Python scripts are
Set-Location ..

# Run verification
py run_verification_with_output.py verification_batches/batch6_files.txt

# Generate review page
py generate_review_page.py

# Rename output files to include batch number
Move-Item -Force verification_results/bedrock_results.json verification_results/batch6_results.json
Move-Item -Force verification_results/review_page.html verification_results/batch6_review.html

Write-Host ""
Write-Host "Batch 6 complete!"
Write-Host "Review at: verification_results/batch6_review.html"
Write-Host ""
