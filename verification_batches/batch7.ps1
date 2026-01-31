# Batch 7 - 1993 PDFs
# Artists: Crowded House, Toto, Frank Zappa, George Michael, Dire Straits...

Write-Host "=" * 80
Write-Host "Starting Batch 7"
Write-Host "PDFs: 1993"
Write-Host "Artists: 47"
Write-Host "=" * 80

# Change to parent directory where the Python scripts are
Set-Location ..

# Run verification
py run_verification_with_output.py verification_batches/batch7_files.txt

# Generate review page
py generate_review_page.py

# Rename output files to include batch number
Move-Item -Force verification_results/bedrock_results.json verification_results/batch7_results.json
Move-Item -Force verification_results/review_page.html verification_results/batch7_review.html

Write-Host ""
Write-Host "Batch 7 complete!"
Write-Host "Review at: verification_results/batch7_review.html"
Write-Host ""
