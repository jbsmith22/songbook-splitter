# Sync Original Structure to Match My Organization
# Run this script in C:\Work\AWSMusic to reorganize to match D:\Work\songbook-splitter

# Base directory - UPDATE THIS to point to the original location
$BASE_DIR = "C:\Work\AWSMusic"

function Move-WithMkdir {
    param(
        [string]$Source,
        [string]$Target
    )

    $sourcePath = Join-Path $BASE_DIR $Source
    $targetPath = Join-Path $BASE_DIR $Target

    if (-not (Test-Path $sourcePath)) {
        Write-Host "  SKIP (not found): $Source" -ForegroundColor Yellow
        return $false
    }

    # Create parent directory
    $targetParent = Split-Path $targetPath -Parent
    if (-not (Test-Path $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }

    # Move
    try {
        Move-Item -Path $sourcePath -Destination $targetPath -Force
        Write-Host "  Moved: $Source -> $Target" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "  ERROR: $Source -> $Target : $_" -ForegroundColor Red
        return $false
    }
}

function Main {
    Write-Host "======================================================================"
    Write-Host "REORGANIZATION: Match D:\Work\songbook-splitter Structure"
    Write-Host "======================================================================"
    Write-Host ""
    Write-Host "Base directory: $BASE_DIR"
    Write-Host ""

    if (-not (Test-Path $BASE_DIR)) {
        Write-Host "ERROR: Directory $BASE_DIR does not exist!" -ForegroundColor Red
        Write-Host "Please update BASE_DIR in the script to point to your original location."
        return
    }

    Write-Host "This will reorganize the structure to match the new organization."
    $response = Read-Host "Press Enter to continue (Ctrl+C to cancel)"

    $movesCount = 0

    # 1. Move working directories from data/ to root
    Write-Host ""
    Write-Host "1. Moving working directories from data/ to root:"

    $workingDirs = @(
        @("data\ProcessedSongs", "ProcessedSongs"),
        @("data\SheetMusic", "SheetMusic"),
        @("data\SheetMusicIndividualSheets", "SheetMusicIndividualSheets"),
        @("data\output", "output"),
        @("data\temp_anthology_output", "temp_anthology_output"),
        @("data\temp_anthology_pages", "temp_anthology_pages"),
        @("data\toc_cache", "toc_cache"),
        @("data\verification_batches", "verification_batches")
    )

    foreach ($move in $workingDirs) {
        if (Move-WithMkdir -Source $move[0] -Target $move[1]) {
            $movesCount++
        }
    }

    # 2. Move build artifacts to build/ directory
    Write-Host ""
    Write-Host "2. Moving build artifacts to build/ directory:"

    $buildArtifacts = @(
        @("lambda-deployment.zip", "build\lambda-deployment.zip"),
        @("lambda-package", "build\lambda-package")
    )

    foreach ($move in $buildArtifacts) {
        if (Move-WithMkdir -Source $move[0] -Target $move[1]) {
            $movesCount++
        }
    }

    # 3. Move verification_results to web/verification/
    Write-Host ""
    Write-Host "3. Moving verification results to web/verification/:"

    $verificationMoves = @(
        @("data\verification_results", "web\verification\verification_results")
    )

    foreach ($move in $verificationMoves) {
        if (Move-WithMkdir -Source $move[0] -Target $move[1]) {
            $movesCount++
        }
    }

    # 4. Create data/downloads if it doesn't exist
    Write-Host ""
    Write-Host "4. Creating additional subdirectories:"

    $additionalDirs = @(
        "data\downloads"
    )

    foreach ($dir in $additionalDirs) {
        $fullPath = Join-Path $BASE_DIR $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Host "  Created: $dir" -ForegroundColor Green
        }
    }

    # 5. Ensure all subdirectory structure exists
    Write-Host ""
    Write-Host "5. Ensuring all subdirectory structure exists:"

    $allDirs = @(
        # data subdirectories
        "data\analysis",
        "data\backups",
        "data\comparisons",
        "data\downloads",
        "data\execution",
        "data\inventories",
        "data\misc",
        "data\processing",
        "data\reconciliation",
        "data\samples",

        # docs subdirectories
        "docs\analysis",
        "docs\archive",
        "docs\comparisons",
        "docs\deployment",
        "docs\design",
        "docs\issues-resolved",
        "docs\operations",
        "docs\plans",
        "docs\project-status",
        "docs\s3",
        "docs\summaries",
        "docs\updates",

        # scripts subdirectories
        "scripts\aws",
        "scripts\aws\downloading",
        "scripts\aws\monitoring",
        "scripts\aws\processing",
        "scripts\s3",
        "scripts\analysis",
        "scripts\local",
        "scripts\testing",
        "scripts\utilities",
        "scripts\one-off",

        # logs subdirectories
        "logs\processing",
        "logs\reorganization",
        "logs\testing",
        "logs\misc",

        # web subdirectories
        "web\s3-browser",
        "web\verification",
        "web\viewers",

        # tests
        "tests\fixtures",

        # build
        "build"
    )

    foreach ($dir in $allDirs) {
        $fullPath = Join-Path $BASE_DIR $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Host "  Created: $dir" -ForegroundColor Green
        }
    }

    # Summary
    Write-Host ""
    Write-Host "======================================================================"
    Write-Host "REORGANIZATION COMPLETE"
    Write-Host "======================================================================"
    Write-Host ""
    Write-Host "Major moves completed: $movesCount"
    Write-Host ""
    Write-Host "Your structure now matches D:\Work\songbook-splitter:"
    Write-Host "  - Working directories moved from data/ to root"
    Write-Host "  - Build artifacts moved to build/"
    Write-Host "  - Verification results moved to web/verification/"
    Write-Host "  - All subdirectory structure created"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Verify the reorganization with a folder comparison tool"
    Write-Host "  2. Run 'git status' to see the changes"
    Write-Host "  3. If satisfied, commit the changes"
}

# Run main function
Main
