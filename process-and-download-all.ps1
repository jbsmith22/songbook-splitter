# Master Script - Process All Books and Download Results
# This script runs the full pipeline: upload PDFs, process them, and download results

param(
    [string]$SheetMusicDir = ".\SheetMusic",
    [string]$OutputDir = ".\ProcessedSongs",
    [int]$MaxConcurrent = 20,
    [switch]$ProcessOnly,
    [switch]$DownloadOnly,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$logFile = "master-process-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

function Wait-ForExecutions {
    param($StateMachineArn, $Region)
    
    Write-Log "Waiting for all executions to complete..." -Color Cyan
    
    $checkInterval = 60  # Check every minute
    $lastCount = -1
    
    while ($true) {
        $running = aws stepfunctions list-executions `
            --state-machine-arn $StateMachineArn `
            --status-filter RUNNING `
            --region $Region `
            --query "executions[].executionArn" `
            --output json 2>$null | ConvertFrom-Json
        
        $runningCount = if ($running) { $running.Count } else { 0 }
        
        if ($runningCount -ne $lastCount) {
            Write-Log "  Running executions: $runningCount" -Color Yellow
            $lastCount = $runningCount
        }
        
        if ($runningCount -eq 0) {
            Write-Log "All executions complete!" -Color Green
            break
        }
        
        Start-Sleep -Seconds $checkInterval
    }
}

function Get-ExecutionStats {
    param($StateMachineArn, $Region)
    
    Write-Log "Gathering execution statistics..." -Color Cyan
    
    # Get executions from last 24 hours
    $succeeded = aws stepfunctions list-executions `
        --state-machine-arn $StateMachineArn `
        --status-filter SUCCEEDED `
        --region $Region `
        --max-results 1000 `
        --query "executions[].executionArn" `
        --output json 2>$null | ConvertFrom-Json
    
    $failed = aws stepfunctions list-executions `
        --state-machine-arn $StateMachineArn `
        --status-filter FAILED `
        --region $Region `
        --max-results 1000 `
        --query "executions[].executionArn" `
        --output json 2>$null | ConvertFrom-Json
    
    $succeededCount = if ($succeeded) { $succeeded.Count } else { 0 }
    $failedCount = if ($failed) { $failed.Count } else { 0 }
    
    Write-Log "  Succeeded: $succeededCount" -Color Green
    Write-Log "  Failed: $failedCount" -Color $(if ($failedCount -gt 0) { "Red" } else { "Gray" })
    
    return @{
        Succeeded = $succeededCount
        Failed = $failedCount
    }
}

# Main execution
Write-Log "=== Master Processing Script ===" -Color Cyan
Write-Log "Sheet Music Directory: $SheetMusicDir"
Write-Log "Output Directory: $OutputDir"
Write-Log "Max Concurrent: $MaxConcurrent"
if ($DryRun) {
    Write-Log "DRY RUN MODE" -Color Yellow
}
Write-Log ""

$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$region = "us-east-1"

# Phase 1: Process books (upload and submit executions)
if (-not $DownloadOnly) {
    Write-Log "=== PHASE 1: Processing Books ===" -Color Cyan
    Write-Log ""
    
    if ($DryRun) {
        & .\process-all-books.ps1 -SheetMusicDir $SheetMusicDir -MaxConcurrent $MaxConcurrent -DryRun
    } else {
        & .\process-all-books.ps1 -SheetMusicDir $SheetMusicDir -MaxConcurrent $MaxConcurrent
    }
    
    Write-Log ""
    Write-Log "Processing phase complete" -Color Green
    Write-Log ""
    
    if (-not $ProcessOnly -and -not $DryRun) {
        # Wait for all executions to complete
        Wait-ForExecutions -StateMachineArn $stateMachineArn -Region $region
        Write-Log ""
        
        # Show statistics
        $stats = Get-ExecutionStats -StateMachineArn $stateMachineArn -Region $region
        Write-Log ""
    }
}

# Phase 2: Download results
if (-not $ProcessOnly) {
    Write-Log "=== PHASE 2: Downloading Results ===" -Color Cyan
    Write-Log ""
    
    if ($DryRun) {
        & .\download-all-songs.ps1 -LocalOutputDir $OutputDir -SkipExisting -DryRun
    } else {
        & .\download-all-songs.ps1 -LocalOutputDir $OutputDir -SkipExisting
    }
    
    Write-Log ""
    Write-Log "Download phase complete" -Color Green
    Write-Log ""
}

# Final summary
Write-Log "=== ALL OPERATIONS COMPLETE ===" -Color Cyan
Write-Log "Master log file: $logFile" -Color Green
Write-Log ""
Write-Log "To view processed songs:" -Color Cyan
Write-Log "  explorer $OutputDir" -Color Yellow
Write-Log ""
Write-Log "To check for failed executions:" -Color Cyan
Write-Log "  aws stepfunctions list-executions --state-machine-arn $stateMachineArn --status-filter FAILED --region $region" -Color Yellow
