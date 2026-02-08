#!/usr/bin/env pwsh
<#
.SYNOPSIS
Detect local LLM setup and capabilities

.DESCRIPTION
Checks for Ollama, LM Studio, or other local LLM servers
and reports available models and vision support
#>

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "LOCAL LLM DETECTION" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

$foundLLM = $false

# Check common LLM server ports
$serversToCheck = @(
    @{Name="Ollama"; Port=11434; TagsEndpoint="/api/tags"; VersionEndpoint="/api/version"; GenerateEndpoint="/api/generate"},
    @{Name="LM Studio"; Port=1234; ModelsEndpoint="/v1/models"; ChatEndpoint="/v1/chat/completions"},
    @{Name="text-generation-webui"; Port=5000; ModelsEndpoint="/v1/models"},
    @{Name="LocalAI"; Port=8080; ModelsEndpoint="/v1/models"},
    @{Name="llama.cpp server"; Port=8081; ModelsEndpoint="/v1/models"}
)

foreach ($server in $serversToCheck) {
    Write-Host "Checking for $($server.Name) on port $($server.Port)..." -NoNewline

    try {
        $baseUrl = "http://localhost:$($server.Port)"

        # Try to connect
        $response = Invoke-WebRequest -Uri $baseUrl -TimeoutSec 2 -ErrorAction Stop 2>$null

        Write-Host " FOUND!" -ForegroundColor Green
        Write-Host "  Base URL: $baseUrl" -ForegroundColor Cyan
        $foundLLM = $true

        # Get models list
        if ($server.TagsEndpoint) {
            try {
                $modelsResponse = Invoke-RestMethod -Uri "$baseUrl$($server.TagsEndpoint)" -ErrorAction Stop
                Write-Host "  Available models:" -ForegroundColor Yellow

                if ($modelsResponse.models) {
                    foreach ($model in $modelsResponse.models) {
                        $modelName = $model.name
                        $isVision = $modelName -match "vision|llava|bakllava|llama.*3\.2.*vision"

                        Write-Host "    - $modelName" -NoNewline
                        if ($isVision) {
                            Write-Host " [VISION CAPABLE]" -ForegroundColor Green
                        } else {
                            Write-Host ""
                        }

                        if ($model.size) {
                            $sizeMB = [math]::Round($model.size / 1MB, 2)
                            Write-Host "      Size: $sizeMB MB" -ForegroundColor Gray
                        }
                    }
                }
            } catch {
                Write-Host "  Could not fetch models list" -ForegroundColor Yellow
            }
        }
        elseif ($server.ModelsEndpoint) {
            try {
                $modelsResponse = Invoke-RestMethod -Uri "$baseUrl$($server.ModelsEndpoint)" -ErrorAction Stop
                Write-Host "  Available models:" -ForegroundColor Yellow

                if ($modelsResponse.data) {
                    foreach ($model in $modelsResponse.data) {
                        $modelName = $model.id
                        Write-Host "    - $modelName"
                    }
                }
            } catch {
                Write-Host "  Could not fetch models list" -ForegroundColor Yellow
            }
        }

        # Output config for Python
        Write-Host ""
        Write-Host "  Python config:" -ForegroundColor Green
        Write-Host "    API_BASE = '$baseUrl'" -ForegroundColor White

        if ($server.GenerateEndpoint) {
            Write-Host "    GENERATE_ENDPOINT = '$($server.GenerateEndpoint)'" -ForegroundColor White
        }
        if ($server.ChatEndpoint) {
            Write-Host "    CHAT_ENDPOINT = '$($server.ChatEndpoint)'" -ForegroundColor White
        }

        Write-Host ""

    } catch {
        Write-Host " Not found" -ForegroundColor Gray
    }
}

Write-Host ""

# Check if any processes are running
Write-Host "Checking for running LLM processes..." -ForegroundColor Yellow
$processes = @("ollama", "lmstudio", "llama-server", "llama.cpp", "text-generation-webui")

foreach ($procName in $processes) {
    $proc = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "  Found: $procName (PID: $($proc.Id))" -ForegroundColor Green
        $foundLLM = $true
    }
}

Write-Host ""

if (-not $foundLLM) {
    Write-Host "No local LLM detected!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common setups:" -ForegroundColor Yellow
    Write-Host "  - Ollama: Install from ollama.ai, then run 'ollama serve'" -ForegroundColor Gray
    Write-Host "  - LM Studio: Download from lmstudio.ai, start local server" -ForegroundColor Gray
    Write-Host "  - llama.cpp: Build and run './server' with model" -ForegroundColor Gray
} else {
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 79) -ForegroundColor Cyan
    Write-Host "SUMMARY" -ForegroundColor Yellow
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 79) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Local LLM detected! You can use it for validation." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Note the API_BASE URL above" -ForegroundColor Gray
    Write-Host "  2. Choose a vision-capable model (marked [VISION CAPABLE])" -ForegroundColor Gray
    Write-Host "  3. Use the validation script with this config" -ForegroundColor Gray
}

Write-Host ""
