# Cleans up the two failed-run timestamp sets from AWS_Restoration\, keeping
# only the successful 20260524-000428 run.
#
# Before running, verify what will be deleted by passing -WhatIf:
#   .\Cleanup-AWS-Restoration-Duplicates.ps1 -WhatIf

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$RestoreDir = 'S:\aiwork\songbook-splitter\AWS_Restoration',
    [string[]]$DropTimestamps = @('20260523-235921', '20260524-000206'),
    [string]$KeepTimestamp = '20260524-000428'
)

Write-Host "Restoration directory: $RestoreDir" -ForegroundColor Cyan
Write-Host "Keeping timestamp:     $KeepTimestamp" -ForegroundColor Green
Write-Host "Dropping timestamps:   $($DropTimestamps -join ', ')" -ForegroundColor Yellow
Write-Host ""

$total = 0
$bytes = 0
foreach ($ts in $DropTimestamps) {
    $items = Get-ChildItem -Path $RestoreDir -Recurse -Force | Where-Object { $_.Name -like "*$ts*" }
    foreach ($item in $items) {
        if ($item.PSIsContainer) {
            $size = (Get-ChildItem $item.FullName -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum
        } else {
            $size = $item.Length
        }
        $bytes += $size
        $total++
        $sizeStr = if ($size -lt 1KB) { "$size B" }
                   elseif ($size -lt 1MB) { "$([math]::Round($size/1KB,1)) KB" }
                   else { "$([math]::Round($size/1MB,1)) MB" }
        Write-Host "  $sizeStr`t$($item.FullName -replace [regex]::Escape($RestoreDir + '\'), '')" -ForegroundColor Gray
        if ($PSCmdlet.ShouldProcess($item.FullName, "Delete")) {
            Remove-Item -LiteralPath $item.FullName -Recurse -Force
        }
    }
}

Write-Host ""
Write-Host "Total: $total items, $([math]::Round($bytes/1MB,2)) MB" -ForegroundColor Cyan
