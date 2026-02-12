#!/usr/bin/env pwsh
# Local DB Native Setup Script (Windows)
# Run: powershell -ExecutionPolicy Bypass -File scripts/install-db.ps1

$ErrorActionPreference = "Stop"

$ES_VERSION = "7.17.27"
$QDRANT_VERSION = "1.13.2"
$INSTALL_DIR = "C:\dev-tools"

Write-Host "=== Daiso Kiosk - Local DB Setup Script ===" -ForegroundColor Cyan

# Create Install Directory
if (-not (Test-Path $INSTALL_DIR)) {
    New-Item -ItemType Directory -Path $INSTALL_DIR | Out-Null
    Write-Host "[OK] Created directory: $INSTALL_DIR" -ForegroundColor Green
}

# ============================================
# 1. Elasticsearch 7.x
# ============================================
$ES_DIR = "$INSTALL_DIR\elasticsearch-$ES_VERSION"
if (Test-Path $ES_DIR) {
    Write-Host "[SKIP] Elasticsearch $ES_VERSION already installed" -ForegroundColor Yellow
} else {
    Write-Host "[1/2] Downloading Elasticsearch $ES_VERSION..." -ForegroundColor Cyan
    $esZip = "$INSTALL_DIR\elasticsearch-$ES_VERSION.zip"
    Invoke-WebRequest -Uri "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-$ES_VERSION-windows-x86_64.zip" -OutFile $esZip

    Write-Host "  Extracting..." -ForegroundColor Cyan
    Expand-Archive -Path $esZip -DestinationPath $INSTALL_DIR
    Remove-Item $esZip

    # JVM Memory Limit (128MB)
    $jvmOptions = "$ES_DIR\config\jvm.options"
    (Get-Content $jvmOptions) -replace '-Xms\d+[gm]', '-Xms128m' -replace '-Xmx\d+[gm]', '-Xmx128m' | Set-Content $jvmOptions
    Write-Host "  JVM Memory Limit Set: -Xms128m -Xmx128m" -ForegroundColor Green

    # Security Disabled + Single Node
    $esConfig = "$ES_DIR\config\elasticsearch.yml"
    Add-Content -Path $esConfig -Value "`nxpack.security.enabled: false`ndiscovery.type: single-node"

    # [FIXED] Replaced '&' with 'AND' to prevent PowerShell parser error
    Write-Host "  Security Disabled AND Single-Node Setup Complete" -ForegroundColor Green

    Write-Host "[OK] Elasticsearch $ES_VERSION Installed" -ForegroundColor Green
}

# ============================================
# 2. Qdrant
# ============================================
$QDRANT_DIR = "$INSTALL_DIR\qdrant"
if (Test-Path "$QDRANT_DIR\qdrant.exe") {
    Write-Host "[SKIP] Qdrant $QDRANT_VERSION already installed" -ForegroundColor Yellow
} else {
    Write-Host "[2/2] Downloading Qdrant $QDRANT_VERSION..." -ForegroundColor Cyan
    $qdrantZip = "$INSTALL_DIR\qdrant.zip"
    Invoke-WebRequest -Uri "https://github.com/qdrant/qdrant/releases/download/v$QDRANT_VERSION/qdrant-x86_64-pc-windows-msvc.zip" -OutFile $qdrantZip

    Write-Host "  Extracting..." -ForegroundColor Cyan
    if (-not (Test-Path $QDRANT_DIR)) {
        New-Item -ItemType Directory -Path $QDRANT_DIR | Out-Null
    }
    Expand-Archive -Path $qdrantZip -DestinationPath $QDRANT_DIR
    Remove-Item $qdrantZip

    Write-Host "[OK] Qdrant $QDRANT_VERSION Installed" -ForegroundColor Green
}

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Elasticsearch: $ES_DIR\bin\elasticsearch.bat" -ForegroundColor White
Write-Host "Qdrant:        $QDRANT_DIR\qdrant.exe" -ForegroundColor White
Write-Host ""
Write-Host "--- How to Run ---" -ForegroundColor Yellow
Write-Host "1. Elasticsearch:  $ES_DIR\bin\elasticsearch.bat"
Write-Host "2. Qdrant:         $QDRANT_DIR\qdrant.exe"
Write-Host ""
Write-Host "--- Verification ---" -ForegroundColor Yellow
Write-Host "Elasticsearch:  curl http://localhost:9200"
Write-Host "Qdrant:         curl http://localhost:6333"