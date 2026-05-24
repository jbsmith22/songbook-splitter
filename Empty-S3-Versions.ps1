<#
.SYNOPSIS
    Force-empty an S3 bucket of all object versions and delete markers,
    using server-side pagination to avoid huge JSON responses.

.DESCRIPTION
    Loops until list-object-versions returns no Versions and no DeleteMarkers.
    Uses --page-size 500 to keep each response small.
    Each batch is deleted via delete-objects.
    Safe to re-run.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Bucket,
    [string]$Region = 'us-east-1',
    [int]$PageSize = 500,
    [int]$MaxLoops = 1000
)

$ErrorActionPreference = 'Continue'
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

Write-Host ""
Write-Host "Emptying s3://$Bucket/ (all versions + delete markers)" -ForegroundColor Cyan
Write-Host ""

$totalDeleted = 0
$loopCount = 0

while ($loopCount -lt $MaxLoops) {
    $loopCount++
    
    # Get one page using server-side pagination - small response (~500 entries max)
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $jsonRaw = & aws s3api list-object-versions `
            --bucket $Bucket `
            --region $Region `
            --page-size $PageSize `
            --max-items $PageSize `
            --output json 2>$stderrFile
        $listExit = $LASTEXITCODE
    } finally {
        Remove-Item $stderrFile -ErrorAction SilentlyContinue
    }
    
    if ($listExit -ne 0) {
        Write-Host "  Error from list-object-versions (exit $listExit) - assuming bucket is empty" -ForegroundColor Yellow
        break
    }
    
    if (-not $jsonRaw -or $jsonRaw.Trim().Length -eq 0) {
        Write-Host "  Bucket is empty (no JSON response)" -ForegroundColor Green
        break
    }
    
    # Parse - if this fails, page-size is still too big somehow
    try {
        $page = $jsonRaw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        Write-Host "  JSON parse error on this page - retrying with smaller batch" -ForegroundColor Yellow
        Write-Host "  $_" -ForegroundColor Red
        Start-Sleep -Seconds 1
        continue
    }
    
    $hasVersions = $page.Versions -and $page.Versions.Count -gt 0
    $hasMarkers = $page.DeleteMarkers -and $page.DeleteMarkers.Count -gt 0
    
    if (-not $hasVersions -and -not $hasMarkers) {
        Write-Host "  No more versions or delete markers" -ForegroundColor Green
        break
    }
    
    # Build the deletion batch
    $toDelete = @()
    if ($hasVersions) {
        foreach ($v in $page.Versions) {
            $toDelete += @{ Key = $v.Key; VersionId = $v.VersionId }
        }
    }
    if ($hasMarkers) {
        foreach ($m in $page.DeleteMarkers) {
            $toDelete += @{ Key = $m.Key; VersionId = $m.VersionId }
        }
    }
    
    # delete-objects allows up to 1000 per call, our page is <=500 so one batch
    $payload = @{ Objects = $toDelete; Quiet = $true } | ConvertTo-Json -Depth 5 -Compress
    
    $tmpFile = [System.IO.Path]::GetTempFileName()
    try {
        # Use ASCII without BOM for the JSON payload (S3 API is picky)
        [System.IO.File]::WriteAllText($tmpFile, $payload, [System.Text.Encoding]::ASCII)
        
        $delStderr = [System.IO.Path]::GetTempFileName()
        try {
            & aws s3api delete-objects `
                --bucket $Bucket `
                --region $Region `
                --delete "file://$tmpFile" 2>$delStderr | Out-Null
            $delExit = $LASTEXITCODE
        } finally {
            Remove-Item $delStderr -ErrorAction SilentlyContinue
        }
        
        if ($delExit -eq 0) {
            $totalDeleted += $toDelete.Count
            Write-Host "  Loop $loopCount`: deleted $($toDelete.Count) items (total: $totalDeleted)" -ForegroundColor Gray
        } else {
            Write-Host "  Loop $loopCount`: delete-objects failed (exit $delExit)" -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    } finally {
        Remove-Item $tmpFile -ErrorAction SilentlyContinue
    }
}

if ($loopCount -ge $MaxLoops) {
    Write-Host ""
    Write-Host "WARNING: Hit MaxLoops=$MaxLoops cap. Bucket may still have content. Re-run if needed." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done. Total items deleted from $Bucket`: $totalDeleted" -ForegroundColor Green
Write-Host ""
