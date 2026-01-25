# Requirements Document

## Introduction

The SheetMusic Book Splitter is an automated pipeline system that processes piano/vocal/guitar songbook PDFs stored in S3, extracts their Table of Contents, and splits them into individual per-song PDF files. The system must handle 500+ PDFs with minimal human intervention while maintaining cost controls, auditability, and production-grade reliability.

## Glossary

- **Pipeline**: The complete end-to-end automated workflow from PDF discovery to song extraction
- **TOC**: Table of Contents - a structured list of songs with page numbers found in songbooks
- **Textract**: AWS service for extracting text from document images
- **Bedrock**: AWS service providing access to Claude LLM for fallback parsing
- **Step_Functions**: AWS orchestration service managing pipeline workflow
- **Manifest**: JSON file documenting all outputs and metadata for a processed book
- **Page_Mapping**: The relationship between printed page numbers in TOC and actual PDF page indices
- **Song_Start_Verification**: Process of confirming a song begins on the expected page
- **Ingest_Service**: Component that discovers PDFs in S3 and initiates processing
- **TOC_Parser**: Component that extracts and structures TOC data from PDF pages
- **PDF_Splitter**: Component that creates individual song PDFs from page ranges
- **DynamoDB_Ledger**: Database tracking processing state and preventing duplicate work
- **CloudWatch**: AWS monitoring service for logs, metrics, and alarms
- **ECS_Fargate**: AWS container orchestration service for compute workloads
- **Various_Artists**: A songbook containing songs from multiple different artists

## Requirements

### Requirement 1: S3 Input and Output Management

**User Story:** As a system operator, I want the pipeline to automatically discover and process PDFs from S3, so that I can process large batches without manual file handling.

#### Acceptance Criteria

1. WHEN the Ingest_Service runs, THE Pipeline SHALL discover all PDF files matching the pattern `s3://<INPUT_BUCKET>/SheetMusic/<Artist>/books/*.pdf`
2. WHEN a PDF is processed, THE PDF_Splitter SHALL write output files to `s3://<OUTPUT_BUCKET>/SheetMusicOut/<ResolvedArtist>/books/<BookName>/<ResolvedArtist>-<SongTitle>.pdf`
3. WHEN generating output filenames, THE Pipeline SHALL sanitize filenames to be safe for both Windows filesystems and S3 (removing invalid characters, limiting length)
4. WHEN a book contains Various_Artists, THE Pipeline SHALL support per-song artist overrides in the output path
5. WHEN writing to S3, THE Pipeline SHALL preserve vector content from source PDFs where possible

### Requirement 2: TOC Discovery and Extraction

**User Story:** As a system operator, I want the pipeline to automatically find and extract Table of Contents data, so that song boundaries can be identified without manual annotation.

#### Acceptance Criteria

1. WHEN searching for TOC, THE Pipeline SHALL render the first N pages (configurable, default 20) as images
2. WHEN analyzing rendered pages, THE Textract SHALL extract text using DetectDocumentText API
3. WHEN scoring pages, THE TOC_Parser SHALL identify TOC-like pages based on patterns (page numbers, song titles, columnar layout)
4. WHEN a TOC is found, THE TOC_Parser SHALL extract a structured list containing song titles and printed page numbers
5. WHEN TOC extraction produces fewer than 10 entries (configurable threshold), THE Pipeline SHALL flag the book for review or apply fallback strategy

### Requirement 3: TOC Parsing with Fallback

**User Story:** As a system operator, I want robust TOC parsing that handles various formats, so that the pipeline works across diverse songbook layouts.

#### Acceptance Criteria

1. WHEN parsing TOC text, THE TOC_Parser SHALL attempt deterministic pattern matching first (regex-based extraction)
2. IF deterministic parsing fails or produces low-confidence results, THEN THE TOC_Parser SHALL invoke Bedrock Claude API as fallback
3. WHEN using Bedrock fallback, THE TOC_Parser SHALL provide extracted text and request structured JSON output
4. WHEN TOC parsing completes, THE Pipeline SHALL validate that extracted entries contain both song titles and page numbers
5. WHEN TOC extraction fails completely, THE Pipeline SHALL log failure details and skip the book with appropriate error status

### Requirement 4: Page Number Mapping

**User Story:** As a system operator, I want the pipeline to correctly map printed page numbers to PDF indices, so that songs are extracted from the correct locations.

#### Acceptance Criteria

1. WHEN building Page_Mapping, THE Pipeline SHALL sample multiple TOC entries (at least 3, configurable)
2. WHEN sampling entries, THE Pipeline SHALL extract text from the expected PDF page and verify it matches the song title
3. WHEN calculating offset, THE Pipeline SHALL fit a model (linear offset: PDF_index = printed_page + offset) based on verified samples
4. WHEN the offset model is established, THE Pipeline SHALL apply it to all TOC entries to determine PDF page indices
5. WHEN offset calculation fails or produces inconsistent results, THE Pipeline SHALL flag the book for manual review

### Requirement 5: Song Start Verification

**User Story:** As a system operator, I want the pipeline to verify song starting pages, so that extraction errors are detected and corrected automatically.

#### Acceptance Criteria

1. WHEN verifying a song start, THE Song_Start_Verification SHALL check for presence of musical staff lines on the expected page
2. WHEN verifying a song start, THE Song_Start_Verification SHALL extract text and check for title matching (fuzzy match with configurable threshold)
3. IF verification fails on the expected page, THEN THE Song_Start_Verification SHALL search ±N pages (configurable, default ±3) for the correct start
4. WHEN a corrected page is found, THE Pipeline SHALL update the page mapping and log the adjustment
5. WHEN verification fails after searching ±N pages, THE Pipeline SHALL log the failure and either skip the song or use the original page with a warning flag

### Requirement 6: PDF Splitting and Output Generation

**User Story:** As a system operator, I want the pipeline to create individual song PDFs with correct page ranges, so that each song is available as a standalone file.

#### Acceptance Criteria

1. WHEN determining page ranges, THE PDF_Splitter SHALL use the verified start page of each song and end before the next song's start page
2. WHEN splitting PDFs, THE PDF_Splitter SHALL use PyMuPDF or equivalent library to extract page ranges without re-rendering
3. WHEN creating output PDFs, THE PDF_Splitter SHALL preserve vector graphics, fonts, and formatting from the source
4. WHEN writing output files, THE PDF_Splitter SHALL generate filenames in the format `<ResolvedArtist>-<SongTitle>.pdf` with sanitized characters
5. WHEN a song extraction fails, THE Pipeline SHALL log the error and continue processing remaining songs

### Requirement 7: Manifest and Auditability

**User Story:** As a system operator, I want detailed manifests and intermediate artifacts saved, so that I can audit results and debug failures.

#### Acceptance Criteria

1. WHEN processing completes for a book, THE Pipeline SHALL generate a manifest.json file containing metadata, TOC entries, page mappings, and output file paths
2. WHEN processing a book, THE Pipeline SHALL save intermediate artifacts (rendered TOC pages, extracted text, Textract responses) to S3
3. WHEN writing manifest.json, THE Pipeline SHALL include timestamps, processing duration, confidence scores, and any warnings or adjustments
4. WHEN a processing step fails, THE Pipeline SHALL log detailed error information to CloudWatch with context for debugging
5. WHEN manifest.json is written, THE Pipeline SHALL store it in the same S3 output directory as the song PDFs

### Requirement 8: Cost Control and Guardrails

**User Story:** As a system operator, I want cost controls and monitoring, so that processing 500 PDFs stays within the $1,000 budget.

#### Acceptance Criteria

1. WHEN processing books, THE Pipeline SHALL track AWS service costs (Textract, Bedrock, compute) via CloudWatch metrics
2. WHEN cost thresholds are approached (configurable percentage of budget), THE Pipeline SHALL trigger CloudWatch alarms
3. WHEN alarms trigger, THE Pipeline SHALL notify operators via SNS or equivalent mechanism
4. WHEN Bedrock fallback is used, THE Pipeline SHALL limit token usage per request (configurable maximum)
5. WHEN processing a batch, THE Pipeline SHALL provide cost estimates before execution and actual costs after completion

### Requirement 9: Orchestration and State Management

**User Story:** As a system operator, I want reliable orchestration with state tracking, so that processing is resumable and idempotent.

#### Acceptance Criteria

1. WHEN a book is discovered, THE Ingest_Service SHALL create a Step_Functions execution for that book
2. WHEN a Step_Functions execution starts, THE Pipeline SHALL check DynamoDB_Ledger to determine if the book was already processed
3. IF a book was already successfully processed, THEN THE Pipeline SHALL skip reprocessing (idempotent behavior)
4. WHEN a Step_Functions execution fails, THE Pipeline SHALL record the failure state in DynamoDB_Ledger with error details
5. WHEN resuming processing, THE Pipeline SHALL allow reprocessing of failed books while skipping successful ones

### Requirement 10: Quality Gates and Success Metrics

**User Story:** As a system operator, I want quality gates that prevent bad outputs, so that only valid song PDFs are produced.

#### Acceptance Criteria

1. WHEN TOC extraction completes, THE Pipeline SHALL verify that at least 10 entries (configurable) were extracted
2. WHEN processing completes, THE Pipeline SHALL verify that at least 90% (configurable) of TOC entries produced output PDFs
3. WHEN song start verification runs, THE Pipeline SHALL achieve at least 95% (configurable) success rate for correct page detection
4. WHEN quality gates fail, THE Pipeline SHALL mark the book as requiring manual review in DynamoDB_Ledger
5. WHEN a book fails quality gates, THE Pipeline SHALL not write partial outputs unless explicitly configured to do so

### Requirement 11: Local Development and Testing

**User Story:** As a developer, I want to run the pipeline locally with mocked AWS services, so that I can develop and test without incurring AWS costs.

#### Acceptance Criteria

1. WHEN running in local mode, THE Pipeline SHALL support a dry-run flag that mocks AWS API calls
2. WHEN running locally, THE Pipeline SHALL read PDFs from local filesystem instead of S3
3. WHEN running locally, THE Pipeline SHALL write outputs to local filesystem instead of S3
4. WHEN mocking Textract, THE Pipeline SHALL use local OCR or pre-recorded responses
5. WHEN mocking Bedrock, THE Pipeline SHALL use local LLM or pre-recorded responses

### Requirement 12: Compute Environment

**User Story:** As a system operator, I want flexible compute options, so that the pipeline can run efficiently on AWS infrastructure.

#### Acceptance Criteria

1. WHERE ECS_Fargate is used, THE Pipeline SHALL run as containerized tasks with configurable CPU and memory
2. WHERE Lambda is used, THE Pipeline SHALL handle Lambda timeout limits (15 minutes) by breaking work into smaller chunks
3. WHEN deploying containers, THE Pipeline SHALL use Python 3.12 base images with required dependencies (boto3, PyMuPDF, poppler, qpdf)
4. WHEN scaling compute, THE Pipeline SHALL support parallel processing of multiple books via Step_Functions concurrency controls
5. WHEN compute tasks complete, THE Pipeline SHALL clean up temporary files and release resources

### Requirement 13: Error Handling and Robustness

**User Story:** As a system operator, I want robust error handling, so that transient failures don't cause complete pipeline failures.

#### Acceptance Criteria

1. WHEN AWS API calls fail with transient errors, THE Pipeline SHALL retry with exponential backoff (configurable retry count)
2. WHEN processing encounters corrupt PDFs, THE Pipeline SHALL log the error and skip to the next book
3. WHEN Textract returns low-confidence text, THE Pipeline SHALL flag pages for review but continue processing
4. WHEN handling weird fonts or mixed content, THE TOC_Parser SHALL apply multiple extraction strategies before failing
5. WHEN unexpected errors occur, THE Pipeline SHALL capture full stack traces and context in CloudWatch logs

### Requirement 14: Various Artists Support

**User Story:** As a system operator, I want intelligent handling of Various Artists compilations, so that each song is attributed to the correct artist.

#### Acceptance Criteria

1. WHEN a book is identified as Various_Artists, THE TOC_Parser SHALL attempt to extract per-song artist information from TOC entries
2. WHEN per-song artist information is available, THE Pipeline SHALL use it in output paths and filenames
3. WHEN per-song artist information is not available, THE Pipeline SHALL use "Various Artists" as the artist name
4. WHEN resolving artist names, THE Pipeline SHALL normalize artist names (remove special characters, handle "featuring" notation)
5. WHEN artist information is ambiguous, THE Pipeline SHALL log a warning and use the book-level artist as fallback

### Requirement 15: Monitoring and Observability

**User Story:** As a system operator, I want comprehensive monitoring, so that I can track pipeline health and performance.

#### Acceptance Criteria

1. WHEN processing books, THE Pipeline SHALL emit CloudWatch metrics for: books processed, songs extracted, TOC success rate, verification success rate
2. WHEN processing completes, THE Pipeline SHALL emit CloudWatch metrics for: processing duration, cost per book, error counts
3. WHEN critical errors occur, THE Pipeline SHALL trigger CloudWatch alarms with appropriate severity levels
4. WHEN viewing logs, THE Pipeline SHALL use structured logging (JSON format) with correlation IDs for tracing executions
5. WHEN monitoring dashboards are viewed, THE Pipeline SHALL provide real-time visibility into processing status and bottlenecks
