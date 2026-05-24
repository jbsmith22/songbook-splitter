# Capture the 3 ECS task families that the previous run got wrong
[CmdletBinding()]
param(
    [string]$RestoreDir = 'S:\aiwork\songbook-splitter\AWS_Restoration',
    [string]$Region = 'us-east-1',
    [string]$Timestamp = '20260524-000428'
)

$ErrorActionPreference = 'Continue'
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-AwsSilent {
    param([string[]]$AwsArgs)
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $output = & aws @AwsArgs 2>$stderrFile
        $script:lastAwsExit = $LASTEXITCODE
        return ($output | Out-String)
    } finally {
        Remove-Item $stderrFile -ErrorAction SilentlyContinue
    }
}

$tdDir = Join-Path $RestoreDir "ecs_task_definitions_$Timestamp"
if (-not (Test-Path $tdDir)) { New-Item -ItemType Directory -Path $tdDir -Force | Out-Null }

# The actual families (from register-all-tasks.ps1, not what my script assumed)
$families = @(
    'jsmith-sheetmusic-splitter-page-mapper',
    'jsmith-sheetmusic-splitter-song-verifier',
    'jsmith-sheetmusic-splitter-manifest-generator'
)

Write-Host "Capturing the 3 task families missed in the previous run..." -ForegroundColor Cyan
$captured = 0
foreach ($f in $families) {
    Write-Host "  -> $f" -ForegroundColor White
    $tdFile = Join-Path $tdDir "$f.json"
    $tdData = Invoke-AwsSilent (@('ecs', 'describe-task-definition', '--task-definition', $f, '--region', $Region))
    if ($script:lastAwsExit -eq 0) {
        $tdData | Out-File -FilePath $tdFile -Encoding utf8
        $parsed = $tdData | ConvertFrom-Json
        $rev = $parsed.taskDefinition.revision
        $cpu = $parsed.taskDefinition.cpu
        $mem = $parsed.taskDefinition.memory
        Write-Host "     OK  Revision $rev, CPU $cpu, Memory $mem MB" -ForegroundColor Green
        $captured++
    } else {
        Write-Host "     WARN  Not registered" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Done. Captured $captured of $($families.Count)." -ForegroundColor Green
Write-Host ""
Write-Host "All ECS task definitions now in $tdDir :" -ForegroundColor Cyan
Get-ChildItem $tdDir -File | ForEach-Object {
    Write-Host "  $($_.Name)" -ForegroundColor Gray
}
