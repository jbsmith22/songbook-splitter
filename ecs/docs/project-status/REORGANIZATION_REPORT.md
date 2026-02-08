# Project Reorganization Report

**Date**: 2026-01-31 11:33:00

## Summary

- **Files/Directories Moved**: 513
- **Errors**: 0

## Moved Items (513)

### build/ (1 items)

- lambda-package/

### data/analysis/ (60 items)

- best_matches_analysis.csv
- case_mismatches.csv
- duplicate-folders.csv
- duplicate_output_folders.csv
- duplicates_different_counts.csv
- duplicates_identical_counts.csv
- exact_match_rename_plan.csv
- matches_confirmed.csv
- matches_need_review.csv
- missing-files-20260127-004224.csv
- missing-files-20260127-005802.csv
- missing-files-fresh-20260127-014156.csv
- missing-files-fresh-20260127-014231.csv
- missing-files-fresh-20260127-113716.csv
- missing-files-verified.csv
- missing_books_candidates.csv
- normalization_plan.csv
- normalization_plan_fixed.csv
- not-duplicates-different-content.csv
- reorganize-preview-20260127-010441.csv
- reorganize-preview-20260127-010919.csv
- retry-books-actual-s3-status.csv
- retry-books-s3-status-complete.csv
- retry-books-s3-status.csv
- retry-failed-books-batch5-20260128-010859.csv
- retry-failed-books-batch5-20260128-011427.csv
- retry-failed-books-batch5-20260128-011523.csv
- retry-failed-books-batch5-20260128-011650.csv
- s3_book_folders_inventory.csv
- s3_books_with_duplicates.csv
- s3_cleanup_plan.csv
- s3_consolidate_plan.csv
- s3_delete_plan.csv
- s3_flatten_plan.csv
- s3_flatten_plan_no_songs.csv
- s3_local_exact_matches.csv
- s3_local_exact_matches_v2.csv
- s3_local_matches.csv
- s3_local_matches_strict.csv
- s3_matches_by_name_similarity.csv
- s3_matches_confirmed.csv
- s3_matches_excellent.csv
- s3_matches_good.csv
- s3_matches_no_match.csv
- s3_matches_partial.csv
- s3_matches_perfect.csv
- s3_matches_poor.csv
- s3_output_folders_inventory.csv
- s3_output_structure_analysis.csv
- s3_rename_plan.csv
- songs-subfolder-files.csv
- source-books-status-final.csv
- source-books-status.csv
- structure_fix_plan.csv
- truly-missing-files.csv
- truly_unprocessed_pdfs.csv
- truly_unprocessed_pdfs_corrected.csv
- unique-to-songs-folder.csv
- unprocessed_pdfs.csv
- unprocessed_pdfs_verified.csv

### data/downloads/ (6 items)

- books-ready-to-download.csv
- books-with-multiple-folders.csv
- books-with-no-folders.csv
- files-to-download.csv
- found-missing-books.csv
- processed-books-with-pdfs.csv

### data/inventories/ (10 items)

- accurate-book-inventory.csv
- book-inventory-updated.csv
- book-inventory.csv
- reverse-inventory-all.csv
- reverse-inventory-unmatched.csv
- reverse-inventory-v2-all.csv
- s3_complete_inventory.csv
- simple-book-inventory.csv
- strict-inventory-matched.csv
- strict-inventory-unmatched.csv

### data/processing/ (20 items)

- book-processing-report.csv
- current-book-status.csv
- dynamodb_ledger_analysis.csv
- dynamodb_path_update_plan.csv
- dynamodb_sync_plan.csv
- failed-12-executions.csv
- failed-books-no-output.csv
- found-books-executions.csv
- ready_for_aws_processing.csv
- ready_for_aws_processing_remaining_19.csv
- ready_for_aws_processing_updated.csv
- remaining-19-executions.csv
- remaining-books-executions-corrected.csv
- remaining-books-executions.csv
- reprocess-13-executions-20260129-215848.csv
- reprocess-13-executions-20260129-215932.csv
- reprocess-13-failed-books-20260129-215015.csv
- reprocess-13-failed-books-20260129-215733.csv
- reprocess-13-failed-books-20260129-222000.csv
- retry-failed-books-executions.csv

### data/reconciliation/ (8 items)

- book_reconciliation.csv
- book_reconciliation_complete.csv
- book_reconciliation_fixed.csv
- book_reconciliation_validated.csv
- book_reconciliation_verified.csv
- input_output_comparison.csv
- input_output_comparison_smart.csv
- path_mapping.csv

### docs/analysis/ (28 items)

- 10_EXTRA_FOLDERS_ANALYSIS.md
- AWS_PIPELINE_SUCCESS.md
- AWS_PIPELINE_TEST_RESULTS.md
- CORRECTED_ANALYSIS.md
- CORRECTED_FINAL_SUMMARY.md
- DEPLOYMENT_FIX_SUMMARY.md
- DEPLOYMENT_SUMMARY.md
- DUPLICATE_OUTPUTS_SUMMARY.md
- FINAL_INPUT_OUTPUT_SUMMARY.md
- FINAL_MATCHING_SUMMARY.md
- FINAL_TUNING_SUMMARY.md
- FIX_SUMMARY.md
- INPUT_OUTPUT_ANALYSIS.md
- INVENTORY_RECONCILIATION_SUMMARY.md
- MATCH_REVIEW_SUMMARY.md
- NO_MATCH_BOOKS_ANALYSIS.md
- OUTPUT_BUCKET_ANALYSIS.md
- PAGE_MAPPING_ANALYSIS.md
- PIPELINE_SUCCESS.md
- ROOT_CAUSE_ANALYSIS.md
- S3_BROWSER_PATH_FIX_SUMMARY.md
- S3_INPUT_BUCKET_ANALYSIS.md
- S3_WITHOUT_LOCAL_SUMMARY.md
- TASK_2.1_SUMMARY.md
- TASK_3.1_SUMMARY.md
- TASK_4.1_SUMMARY.md
- VERIFICATION_TUNING_SUMMARY.md
- VERIFICATION_WORKFLOW_SUMMARY.md

### docs/deployment/ (3 items)

- COMPLETE_PIPELINE_DEPLOYMENT.md
- DEPLOYMENT_PLAN.md
- DEPLOYMENT_STATUS.md

### docs/design/ (5 items)

- AWS_VERIFICATION_PLAN.md
- BATCH_VERIFICATION_WORKFLOW.md
- CORRECT_ALGORITHM.md
- PDF_SPLIT_VERIFICATION_DESIGN.md
- PNG_PRERENDER_IMPLEMENTATION.md

### docs/issues-resolved/ (10 items)

- ALGORITHM_FIX_APPLIED.md
- ARTIST_NAME_FIX.md
- CASE_MISMATCH_FIX_COMPLETE.md
- CURRENT_ISSUES.md
- DYNAMODB_SYNC_COMPLETE.md
- EMPTY_FOLDERS_RESOLVED.md
- EXACT_MATCH_COMPLETE.md
- NORMALIZATION_VERIFICATION_COMPLETE.md
- PROCESS_REMAINING_20_FIXED.md
- S3_INPUT_BUCKET_CLEANUP_COMPLETE.md

### docs/operations/ (8 items)

- AUTO_SPLIT_GUIDE.md
- BATCH_PROCESSING_README.md
- BOOK_REVIEW_README.md
- BULK_SPLIT_OPERATIONS_GUIDE.md
- DEPLOYMENT_COMPLETE.md
- READY_TO_TEST.md
- READ_ME_FIRST.md
- VERIFICATION_REVIEW_GUIDE.md

### docs/plans/ (2 items)

- REMAINING_19_BOOKS_PLAN.md
- kiro_sheetmusic_splitter_plan.md

### docs/project-status/ (7 items)

- CURRENT_STATUS_2026-01-30.md
- INVENTORY_STATUS.md
- PROJECT_CHECKPOINT_2026-01-28.md
- PROJECT_CHECKPOINT_2026-01-29.md
- PROJECT_STATUS_DENSE.md
- PROJECT_STATUS_REPORT.md
- SESSION_SUMMARY.md

### docs/s3/ (6 items)

- S3_BUCKET_USAGE_DEFINITIVE.md
- S3_MATCHING_RESULTS.md
- S3_OUTPUT_BUCKET_DECISION.md
- S3_OUTPUT_BUCKET_STRUCTURE_ISSUES.md
- S3_SYNC_PLAN_FINAL.md
- S3_SYNC_STATUS.md

### logs/processing/ (22 items)

- download-all-songs-20260126-023112.log
- download-all-songs-20260126-105333.log
- download-all-songs-20260126-160741.log
- download-missing-20260127-013916.log
- download-missing-20260127-014336.log
- download-missing-songs-20260126-210044.log
- download-missing-songs-20260126-210121.log
- download-missing-songs-20260126-210301.log
- download-missing-songs-20260127-003625.log
- download-sanitized-20260127-113921.log
- master-process-20260126-023108.log
- master-process-20260126-023341.log
- master-process-20260126-023436.log
- master-process-20260126-023531.log
- master-process-20260126-023653.log
- process-all-books-20260126-023108.log
- process-all-books-20260126-023341.log
- process-all-books-20260126-023436.log
- process-all-books-20260126-023531.log
- process-all-books-20260126-023653.log
- process-all-books-20260126-135558.log
- process-all-books-20260126-140853.log

### logs/reorganization/ (15 items)

- fresh-comparison-20260127-014156.log
- fresh-comparison-20260127-014231.log
- fresh-comparison-20260127-113716.log
- rename-s3-boto3-20260127-114424.log
- rename-s3-boto3-20260127-114628.log
- rename-s3-download-20260127-114228.log
- reorganize-20260127-010430.log
- reorganize-20260127-010908.log
- reorganize-20260127-010922.log
- reorganize-20260127-012030.log
- reorganize-20260127-012139.log
- reorganize-20260127-012301.log
- reorganize-s3-20260127-012817.log
- reorganize-s3-20260127-012839.log
- reorganize-s3-20260127-012958.log

### logs/testing/ (4 items)

- mamas-papas-test.log
- pdf_verification.log
- prerender.log
- test_run.log

### scripts/analysis/ (73 items)

- analyze_all_batches.py
- analyze_all_pages.py
- analyze_duplicates.py
- analyze_dynamodb_ledger.py
- analyze_feedback.py
- analyze_gaps_from_cache.py
- analyze_output_bucket_needs.py
- analyze_page_gaps.py
- analyze_page_gaps_local.py
- analyze_processed_folders.py
- analyze_s3_duplicates.py
- analyze_s3_output_structure.py
- analyze_s3_structure.py
- analyze_toc_and_pages.py
- build-accurate-inventory-fixed.ps1
- build-accurate-inventory-v2.ps1
- build-accurate-inventory.ps1
- build-simple-inventory.ps1
- check-execution-details.ps1
- check-missing-books.ps1
- check-s3-output-availability.ps1
- compare_input_output_counts.py
- compare_input_output_smart.py
- compare_sources.py
- estimate-disk-space.ps1
- find-artist-prefix-duplicates.ps1
- find-duplicate-folders.ps1
- find-missing-books.ps1
- find_best_matches.py
- find_duplicate_folder_names.py
- find_duplicate_outputs.py
- find_missing_books.py
- find_missing_folders.py
- find_s3_folders.py
- find_s3_without_local.py
- find_truly_unprocessed.py
- find_truly_unprocessed_corrected.py
- find_unprocessed_pdfs.py
- gather-system-info.ps1
- generate-book-report.ps1
- identify-batch-scripts.ps1
- identify-failed-books.ps1
- identify_extracted_pdfs.py
- problem-books-report.ps1
- reconcile_books.py
- reverse-inventory-v2.ps1
- reverse-inventory.ps1
- strict-1to1-inventory.ps1
- validate_complete_csv.py
- validate_complete_inventory.py
- validate_complete_inventory_simple.py
- validate_complete_inventory_v2.py
- validate_current_state.py
- validate_exact_inventory.py
- validate_using_normalization_plan.py
- verify_book_counts.py
- verify_correct_mapping.py
- verify_dynamodb_sync.py
- verify_exact_match.py
- verify_exact_match_v2.py
- verify_extracted_pdfs.py
- verify_final_mapping.py
- verify_final_results.py
- verify_index_3.py
- verify_new_pdfs.py
- verify_paths.py
- verify_pdf_splits.py
- verify_perfect_matches.py
- verify_post_normalization_mapping.py
- verify_results.py
- verify_s3_input_bucket.py
- verify_truly_unprocessed.py
- verify_with_vision.py

### scripts/aws/ (7 items)

- cleanup.ps1
- deploy-docker.ps1
- deploy-lambda.ps1
- deploy.ps1
- register-all-tasks.ps1
- register-ecs-tasks-simple.ps1
- register-ecs-tasks.ps1

### scripts/aws/downloading/ (18 items)

- download-18-books-from-s3.ps1
- download-7-successful.ps1
- download-all-songs.ps1
- download-and-integrate-11-books.ps1
- download-and-integrate-missing.ps1
- download-and-integrate-new-books.ps1
- download-billy-joel-results.ps1
- download-completed-books.ps1
- download-missing-songs.ps1
- download-new-billy-joel.ps1
- download-remaining-19-results.ps1
- download-remaining-19-simple.ps1
- download-remaining-20-results.ps1
- download-remaining-books.ps1
- download-special-chars.ps1
- download-successful-books.ps1
- download-with-s3-search.ps1
- download-with-sanitized-names.ps1

### scripts/aws/monitoring/ (23 items)

- monitor-13-reprocessed.ps1
- monitor-all-executions.ps1
- monitor-all-new-executions.ps1
- monitor-all-running.ps1
- monitor-billy-joel-retry.ps1
- monitor-billy-joel.ps1
- monitor-corrected-executions.ps1
- monitor-current-execution.ps1
- monitor-docker-and-launch.ps1
- monitor-execution.ps1
- monitor-failed-12.ps1
- monitor-great-bands-70s.ps1
- monitor-remaining-19.ps1
- monitor-remaining-20.ps1
- monitor-remaining-books.ps1
- monitor-test-execution-v2.ps1
- monitor-test-execution.ps1
- monitor-various-artists-final.ps1
- monitor-various-artists-v2.ps1
- monitor-various-artists-v3.ps1
- monitor-various-artists-v4.ps1
- monitor-various-artists.ps1
- monitor-vol2.ps1

### scripts/aws/processing/ (19 items)

- process-12-failed-books.ps1
- process-all-books.ps1
- process-and-download-all.ps1
- process-billy-joel-missing.ps1
- process-failed-books-fixed.ps1
- process-found-books-from-csv.ps1
- process-found-books.ps1
- process-one-book.ps1
- process-remaining-19-books.ps1
- process-remaining-20-books-fixed.ps1
- process-remaining-20-books.ps1
- process-remaining-books-corrected.ps1
- process-remaining-books.ps1
- reprocess-12-missing.ps1
- reprocess-13-failed-books.ps1
- reprocess-13-failed-simple.ps1
- reprocess-13-working.ps1
- reprocess-books.ps1
- retry-failed-books-batched.ps1

### scripts/local/ (3 items)

- fix-artist-names-in-filenames.ps1
- reorganize-local-files.ps1
- restore-billy-joel-structure.ps1

### scripts/one-off/ (119 items)

- add_missing_folders.py
- backup_dynamodb_final.py
- build_complete_lineage.py
- build_page_lineage.py
- check_10_extras.py
- check_book_count.py
- check_crosby.py
- check_empty_folders_in_s3.py
- check_extracted_pdfs.py
- check_feedback.py
- check_first_pages.py
- check_folder_count.py
- check_matching_failures.py
- check_missing_folders.py
- check_page_3.py
- check_pages_47_55.py
- check_pdf.py
- check_remaining_unnormalized.py
- check_s3_structure.py
- check_source_pdf.py
- check_specific_match.py
- check_until_the_night.py
- check_what_vision_sees.py
- correct_mapping.py
- count-songs-subfolder.py
- count_actual_books.py
- count_source_books.py
- create_exact_match_plan.py
- create_s3_cleanup_plan.py
- create_s3_sync_plan.py
- create_structure_fix_plan.py
- create_verification_batches.py
- debug_bedrock_responses.py
- debug_every_breath.py
- debug_folder_count.py
- debug_ollama_response.py
- debug_page_mapping.py
- debug_verification.py
- delete_9_extra_folders.py
- delete_empty_folders.py
- detailed_count.py
- diagnose_conflicts.py
- download-missing-files.py
- download_all_tocs.py
- download_empty_folders.py
- download_partial_missing_files.py
- execute_exact_match_renames.py
- execute_normalization.py
- execute_splits.py
- execute_structure_fix.py
- export_fuzzy_matches.py
- extract-first-pages.py
- extract_page_info.py
- filter_batch1_results.py
- final_mapping_report.py
- final_verification.py
- final_verification_v2.py
- find-missing-files.py
- find-truly-missing.py
- fix_case_mismatches.py
- fix_case_mismatches_v2.py
- fix_case_only_renames.py
- fix_duplicate_names.py
- fix_folder_columns.py
- fix_html_paths.py
- fix_oversized_images.py
- fix_remaining_case_mismatches.py
- fix_remaining_pdfs.py
- flatten_all_s3_structure.py
- flatten_s3_no_songs_folder.py
- fuzzy_match_books.py
- generate-book-inventory.py
- generate_complete_viewer.py
- generate_lineage_viewer.py
- generate_normalization_plan.py
- generate_random_sample.py
- generate_review_page.py
- generate_review_page_grouped.py
- investigate_extra_outputs.py
- list_s3_book_folders.py
- list_s3_output_folders.py
- local_runner.py
- match_by_folder_name_similarity.py
- match_exact_files.py
- match_exact_files_v2.py
- match_s3_to_local.py
- match_s3_to_local_strict.py
- migrate_dynamodb_with_history.py
- normalization_summary.py
- prerender_all_pages.py
- process-billy-joel-missing.py
- process_all_billy_joel.ps1
- rebuild_ledger_with_mapping.py
- rename-s3-with-boto3.py
- render-first-pages.py
- render_and_test.py
- review_matches.py
- run_verification_with_output.py
- show_updated_results.py
- show_weak_matches.py
- split_detection_server.py
- subscribe-alerts.ps1
- summarize_matches.py
- sync-from-s3-proper-structure.ps1
- sync_dynamodb_from_csv.py
- test-one-book.ps1
- test-pipeline.ps1
- track_verification_progress.py
- update-ecs-task-images.ps1
- update-task-definitions.ps1
- update_dynamodb_paths_only.py
- update_ready_for_aws.py
- update_remaining_books.py
- upload-and-process-remaining-books.ps1
- verify-artist-prefix-duplicates.ps1
- verify-duplicates.py
- verify-s3-structure.py
- verify-s3-vs-local.py
- watch-page-mapper-logs.ps1

### scripts/s3/ (15 items)

- build_s3_delete_browser.py
- build_s3_interactive_browser.py
- build_s3_interactive_browser_fixed.py
- build_s3_interactive_browser_new.py
- build_s3_inventory.py
- build_s3_tree_browser.py
- compare-s3-local-fresh.ps1
- compare-s3-local.ps1
- consolidate_duplicate_book_folders.py
- execute_consolidation.py
- fix_bread_structure.py
- rename-in-s3-and-download.ps1
- render_s3_tree_html.py
- reorganize-s3-bucket.ps1
- s3_browser_server.py

### scripts/testing/ (9 items)

- check_ollama_performance.ps1
- start_review_server.ps1
- test_bedrock_verification.py
- test_correct_offset.py
- test_image_formats.py
- test_known_errors.py
- test_parsing.py
- test_specific_pdfs.py
- test_verification_setup.py

### scripts/utilities/ (4 items)

- get-missing-files-csv.ps1
- git-checkpoint-commit.ps1
- kill-old-batch-scripts.ps1
- start_s3_browser.ps1

### web/s3-browser/ (5 items)

- s3_bucket_browser.html
- s3_bucket_browser_interactive.html
- s3_tree_view.html
- test_bulk_buttons.html
- test_buttons.html

### web/verification/ (1 items)

- verification_results/

### web/viewers/ (2 items)

- book_lineage_viewer.html
- complete_lineage_viewer.html

