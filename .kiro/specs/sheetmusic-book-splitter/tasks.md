# Implementation Plan: SheetMusic Book Splitter

## Overview

This implementation plan breaks down the SheetMusic Book Splitter system into discrete, incremental coding tasks. The system will be built in phases, starting with core functionality and progressing to full AWS integration. Each task builds on previous work, with checkpoints to ensure quality and allow for user feedback.

The implementation uses Python 3.12 with boto3 for AWS services, PyMuPDF for PDF manipulation, and Hypothesis for property-based testing. The architecture follows a modular design with clear separation between components.

## Tasks

- [x] 1. Project setup and core infrastructure
  - Create project structure: /app/, /infra/, /tests/, /docs/
  - Set up Python 3.12 virtual environment with dependencies (boto3, PyMuPDF, Hypothesis, pytest)
  - Create configuration module for environment variables and AWS settings
  - Set up logging infrastructure with structured JSON logging
  - _Requirements: 15.4_

- [x] 2. Implement filename sanitization utilities
  - [x] 2.1 Create sanitization module with functions for Windows and S3-safe filenames
    - Remove invalid characters: < > : " / \ | ? *
    - Handle Unicode normalization (NFC)
    - Limit length to 200 characters
    - _Requirements: 1.3, 6.4_
  
  - [ ]* 2.2 Write property test for filename sanitization
    - **Property 2: Output Path Format Compliance**
    - **Validates: Requirements 1.3, 6.4**

- [x] 3. Implement artist resolution and normalization
  - [x] 3.1 Create artist resolution module
    - Implement resolve_artist() function for Various Artists handling
    - Implement normalize_artist_name() function
    - Handle "featuring" notation and special characters
    - _Requirements: 1.4, 14.2, 14.3, 14.4, 14.5_
  
  - [ ]* 3.2 Write property tests for artist resolution
    - **Property 3: Artist Override Resolution**
    - **Property 27: Artist Name Normalization**
    - **Validates: Requirements 1.4, 14.2, 14.3, 14.4, 14.5_

- [x] 4. Implement data models
  - [x] 4.1 Create data model classes using Python dataclasses
    - TOCEntry, SongLocation, VerifiedSong, PageRange, OutputFile
    - TOCDiscoveryResult, TOCParseResult, PageMapping, Manifest
    - Include validation methods and serialization
    - _Requirements: 2.4, 3.4, 7.1_
  
  - [ ]* 4.2 Write unit tests for data model validation
    - Test required field validation
    - Test serialization/deserialization
    - _Requirements: 2.4, 3.4_

- [x] 5. Implement S3 utilities and PDF discovery
  - [x] 5.1 Create S3 utility module with local mode support
    - Implement list_pdfs() function with pattern matching
    - Support both S3 and local filesystem paths
    - Handle pagination for large S3 listings
    - _Requirements: 1.1, 11.2_
  
  - [ ]* 5.2 Write property test for S3 pattern matching
    - **Property 1: S3 Pattern Matching for PDF Discovery**
    - **Validates: Requirements 1.1**

- [x] 6. Implement DynamoDB ledger operations
  - [x] 6.1 Create DynamoDB ledger module
    - Implement check_already_processed() function
    - Implement record_processing_start() function
    - Implement record_processing_complete() function (success/failed/manual_review)
    - Support local mode with mock DynamoDB
    - _Requirements: 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 6.2 Write property tests for idempotency
    - **Property 20: Idempotent Processing**
    - **Property 21: Execution State Tracking**
    - **Validates: Requirements 9.2, 9.3, 9.4, 9.5**

- [x] 7. Checkpoint - Core utilities complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement TOC discovery service
  - [x] 8.1 Create TOC discovery module
    - Implement render_pages() function using PyMuPDF
    - Implement extract_text_textract() function with retry logic
    - Support mock Textract for local mode
    - _Requirements: 2.1, 2.2, 11.4, 13.1_
  
  - [x] 8.2 Implement TOC scoring algorithm
    - Implement score_toc_likelihood() function
    - Use heuristics: page numbers, columnar layout, keywords
    - Implement select_toc_pages() function
    - _Requirements: 2.3_
  
  - [ ]* 8.3 Write property test for TOC scoring
    - **Property 5: TOC Page Scoring Accuracy**
    - **Validates: Requirements 2.3**
  
  - [ ]* 8.4 Write unit tests for TOC discovery
    - Test with sample PDFs (clear TOC, no TOC, weird fonts)
    - Test Textract retry logic
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 9. Implement deterministic TOC parser
  - [x] 9.1 Create TOC parser module with regex patterns
    - Implement deterministic_parse() function with multiple patterns
    - Handle various TOC formats (dots, columns, artist attribution)
    - Extract per-song artist information for Various Artists
    - _Requirements: 3.1, 14.1_
  
  - [x] 9.2 Implement TOC entry validation
    - Implement validate_toc_entries() function
    - Check minimum entry count threshold
    - Validate structure (title + page number)
    - _Requirements: 2.4, 3.4_
  
  - [ ]* 9.3 Write property tests for TOC parsing
    - **Property 6: TOC Entry Structure Completeness**
    - **Property 28: Various Artists Detection and Extraction**
    - **Validates: Requirements 2.4, 3.4, 14.1**

- [x] 10. Implement Bedrock fallback parser
  - [x] 10.1 Create Bedrock integration module
    - Implement bedrock_fallback_parse() function
    - Construct prompt with TOC text and book metadata
    - Parse JSON response into TOCEntry objects
    - Support mock Bedrock for local mode
    - _Requirements: 3.2, 3.3, 11.5_
  
  - [x] 10.2 Implement token limiting
    - Truncate input text to 4000 tokens max
    - Set max_tokens=2000 in API request
    - _Requirements: 8.4_
  
  - [ ]* 10.3 Write property tests for parser fallback
    - **Property 7: Deterministic Parser Priority**
    - **Property 18: Bedrock Token Limiting**
    - **Validates: Requirements 3.1, 3.2, 8.4**

- [ ] 11. Checkpoint - TOC extraction complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement page mapping service
  - [x] 12.1 Create page mapper module
    - Implement sample_entries() function (first, middle, last)
    - Implement verify_page_match() function with fuzzy matching
    - Implement calculate_offset() function with consistency validation
    - Implement apply_mapping() function
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 12.2 Write property tests for page mapping
    - **Property 8: Page Mapping Sample Size**
    - **Property 9: Title Verification Accuracy**
    - **Property 10: Offset Model Consistency**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ] 13. Implement song verification service
  - [x] 13.1 Create song verifier module with staff line detection
    - Implement check_staff_lines() function using OpenCV or image processing
    - Implement check_title_match() function with fuzzy matching
    - Implement search_nearby_pages() function (±N pages)
    - Implement adjust_page_ranges() function
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 13.2 Write property tests for verification
    - **Property 11: Song Start Search Range**
    - **Property 12: Page Adjustment Logging**
    - **Property 13: Page Range Calculation**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
  
  - [ ]* 13.3 Write unit tests for staff line detection
    - Test with pages containing and not containing staff lines
    - Test edge cases (partial staff lines, non-music content)
    - _Requirements: 5.1_

- [ ] 14. Implement PDF splitting service
  - [x] 14.1 Create PDF splitter module
    - Implement extract_page_range() function using PyMuPDF
    - Implement split_pdf() function with error handling per song
    - Implement write_to_s3() function (or local filesystem)
    - Ensure vector content preservation (no re-rendering)
    - _Requirements: 6.1, 6.2, 6.3, 6.5_
  
  - [ ]* 14.2 Write property tests for PDF splitting
    - **Property 4: Vector Content Preservation**
    - **Property 14: Extraction Error Resilience**
    - **Validates: Requirements 6.3, 6.5**
  
  - [ ]* 14.3 Write unit tests for page range extraction
    - Test single-page and multi-page songs
    - Test last song (extends to end of PDF)
    - _Requirements: 6.1_

- [ ] 15. Checkpoint - Core processing pipeline complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement manifest generator
  - [x] 16.1 Create manifest generator module
    - Implement generate_manifest() function
    - Aggregate data from all pipeline stages
    - Calculate success metrics and quality scores
    - Include cost estimates
    - _Requirements: 7.1, 7.3, 7.5_
  
  - [x] 16.2 Implement manifest persistence
    - Implement write_manifest_to_s3() function
    - Write to output directory alongside song PDFs
    - _Requirements: 7.5_
  
  - [ ]* 16.3 Write property tests for manifest
    - **Property 15: Manifest Completeness**
    - **Property 16: Intermediate Artifact Persistence**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.5**

- [x] 17. Implement error handling and retry logic
  - [x] 17.1 Create error handling utilities
    - Implement retry decorator with exponential backoff
    - Implement error context capture function
    - Implement graceful degradation patterns
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [ ]* 17.2 Write property tests for error handling
    - **Property 17: Error Context Logging**
    - **Property 24: AWS API Retry with Exponential Backoff**
    - **Property 25: Low Confidence Handling**
    - **Property 26: Multiple Extraction Strategy Fallback**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5**

- [ ] 18. Implement quality gate enforcement
  - [x] 18.1 Create quality gate module
    - Implement check_toc_quality_gate() function (≥10 entries)
    - Implement check_verification_quality_gate() function (≥95% success)
    - Implement check_output_quality_gate() function (≥90% success)
    - Return status: "success", "failed", or "manual_review"
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 18.2 Write property tests for quality gates
    - **Property 22: Output Success Rate Quality Gate**
    - **Property 23: Verification Success Rate Quality Gate**
    - **Validates: Requirements 10.2, 10.3, 10.4, 10.5**

- [x] 19. Implement CloudWatch metrics and logging
  - [x] 19.1 Create CloudWatch utilities module
    - Implement emit_metric() function for custom metrics
    - Implement structured_log() function with correlation IDs
    - Track: books processed, songs extracted, costs, errors
    - Support local mode (log to console instead of CloudWatch)
    - _Requirements: 8.1, 15.1, 15.2, 15.4_
  
  - [ ]* 19.2 Write property tests for metrics and logging
    - **Property 19: Cost Metrics Emission**
    - **Property 29: Structured Logging with Correlation**
    - **Validates: Requirements 8.1, 8.5, 15.1, 15.2, 15.4**

- [ ] 20. Checkpoint - All core modules complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 21. Implement Ingest Service (Lambda)
  - [x] 21.1 Create Lambda handler for PDF discovery
    - Implement lambda_handler() function
    - Call discover_pdfs() to scan S3
    - Call check_already_processed() for idempotency
    - Call start_step_function() for each new book
    - _Requirements: 1.1, 9.1, 9.2, 9.3_
  
  - [ ]* 21.2 Write integration tests for Ingest Service
    - Test with mock S3 and DynamoDB
    - Test idempotency behavior
    - _Requirements: 1.1, 9.1, 9.2, 9.3_

- [x] 22. Implement ECS task definitions
  - [x] 22.1 Create Dockerfile for ECS tasks
    - Base image: Python 3.12
    - Install dependencies: boto3, PyMuPDF, OpenCV, poppler, qpdf
    - Copy application code
    - Set entrypoint for task execution
    - _Requirements: 12.1, 12.3_
  
  - [x] 22.2 Create ECS task entry points
    - TOC Discovery task entry point
    - TOC Parser task entry point
    - Song Verifier task entry point
    - PDF Splitter task entry point
    - _Requirements: 12.1_
  
  - [ ]* 22.3 Write unit tests for task entry points
    - Test with mock AWS services
    - Test error handling and cleanup
    - _Requirements: 12.5_

- [x] 23. Implement Step Functions state machine
  - [x] 23.1 Create Step Functions definition (JSON or CDK)
    - Define all states: CheckAlreadyProcessed, TOCDiscovery, TOCParsing, etc.
    - Configure retry logic with exponential backoff
    - Configure error handling and catch blocks
    - Add quality gate validation states
    - _Requirements: 9.1, 13.1_
  
  - [x] 23.2 Create Lambda functions for state machine integration
    - check-processed Lambda
    - record-start Lambda
    - record-success Lambda
    - record-failure Lambda
    - record-manual-review Lambda
    - _Requirements: 9.2, 9.4_

- [ ] 24. Implement infrastructure as code
  - [x] 24.1 Create CloudFormation or CDK stack
    - Define S3 buckets (input, output, artifacts)
    - Define DynamoDB table (ledger)
    - Define ECS cluster and task definitions
    - Define Lambda functions
    - Define Step Functions state machine
    - Define IAM roles and policies
    - _Requirements: All infrastructure requirements_
  
  - [x] 24.2 Create CloudWatch alarms
    - Cost threshold alarms
    - Error rate alarms
    - Processing failure alarms
    - Configure SNS notifications
    - _Requirements: 8.2, 8.3, 15.3_
  
  - [ ]* 24.3 Write property tests for alarm configuration
    - **Property 30: Alarm Triggering on Critical Errors**
    - **Validates: Requirements 15.3**

- [ ] 25. Implement local development mode
  - [x] 25.1 Create local runner script
    - Support --dry-run flag
    - Use local filesystem instead of S3
    - Use mock AWS services (Textract, Bedrock, DynamoDB)
    - Process single PDF for testing
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ]* 25.2 Write integration tests for local mode
    - Test end-to-end processing with sample PDF
    - Verify no AWS API calls are made
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 26. Checkpoint - Full system integration complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 27. Implement compute resource management
  - [ ] 27.1 Add temporary file cleanup
    - Implement cleanup_temp_files() function
    - Call at end of each ECS task
    - Handle cleanup on error conditions
    - _Requirements: 12.5_
  
  - [ ] 27.2 Add Lambda timeout handling
    - Chunk work for Lambda functions
    - Ensure work completes within 15-minute limit
    - _Requirements: 12.2_
  
  - [ ]* 27.3 Write property tests for resource management
    - **Property 31: Temporary File Cleanup**
    - **Property 32: Lambda Timeout Handling**
    - **Validates: Requirements 12.2, 12.5**

- [ ] 28. Implement parallel processing support
  - [ ] 28.1 Configure Step Functions concurrency
    - Set maximum concurrent executions
    - Implement throttling to stay within AWS limits
    - _Requirements: 12.4_
  
  - [ ]* 28.2 Write property test for parallel processing
    - **Property 33: Parallel Processing Support**
    - **Validates: Requirements 12.4**

- [ ] 29. Create end-to-end integration tests
  - [ ]* 29.1 Write end-to-end test with sample PDFs
    - Test complete pipeline from discovery to output
    - Use LocalStack or mocked AWS services
    - Verify manifest generation and quality gates
    - _Requirements: All requirements_
  
  - [ ]* 29.2 Write test for Various Artists handling
    - Test per-song artist override logic
    - Verify output paths use correct artists
    - _Requirements: 1.4, 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 30. Create documentation
  - [ ] 30.1 Write README.md
    - Project overview and architecture
    - Setup instructions (local and AWS)
    - Configuration options
    - Usage examples
  
  - [ ] 30.2 Write deployment guide
    - AWS prerequisites
    - Infrastructure deployment steps
    - Cost estimation and monitoring
    - Troubleshooting guide
  
  - [ ] 30.3 Write operator runbook
    - How to trigger processing
    - How to monitor progress
    - How to handle manual review cases
    - How to debug failures

- [ ] 31. Final checkpoint - System ready for deployment
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and allow for user feedback
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and integration points
- The implementation follows a bottom-up approach: utilities → core modules → services → orchestration
- Local mode support enables development and testing without AWS costs
- Infrastructure as code ensures reproducible deployments
