# setup-dev.ps1 - Development Environment Setup
# Sets up development tools for Python and JavaScript

# Ensure we are in the project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   mockCMMS Development Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$script:ErrorCount = 0

# Step 1: Check Prerequisites
Write-Host "[Step 1/3] Checking prerequisites..." -ForegroundColor Yellow

# Step 1.1: Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
         Write-Host "   Found: " -NoNewline -ForegroundColor White
         Write-Host "$pythonVersion" -NoNewline -ForegroundColor White
         Write-Host " OK" -ForegroundColor Green
    }
}
catch {
    Write-Warning "   Python not found. Attempting to install via winget..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            Write-Host "   Installing Python 3.12..." -ForegroundColor Magenta
            winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                 Write-Host "   Python installed. Please restart your terminal." -ForegroundColor Yellow
                 exit 0
            } else { Write-Error "   Failed to install Python."; exit 1 }
        } catch { Write-Error "   Installation failed."; exit 1 }
    } else { Write-Error "   Python missing. Install manually."; exit 1 }
}

# Step 1.2: Check Node.js/NPM
try {
    $npmVersion = npm --version 2>&1
    if ($npmVersion -match "(\d+)\.(\d+)") {
        Write-Host "   Found: " -NoNewline -ForegroundColor White
        Write-Host "npm $npmVersion" -NoNewline -ForegroundColor White
        Write-Host " OK" -ForegroundColor Green
    }
}
catch {
    Write-Warning "   Node.js/npm not found. Attempting to install via winget..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            Write-Host "   Installing Node.js..." -ForegroundColor Magenta
            winget install -e --id OpenJS.NodeJS --silent --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                 Write-Host "   Node.js installed. Please restart your terminal." -ForegroundColor Yellow
                 exit 0
            } else { Write-Error "   Failed to install Node.js."; exit 1 }
        } catch { Write-Error "   Installation failed."; exit 1 }
    } else { Write-Error "   Node.js missing. Install manually."; exit 1 }
}

# Step 2: Python Development Setup
Write-Host "`n[Step 2/3] Setting up Python development tools..." -ForegroundColor Yellow

if (-not (Test-Path ".venv")) {
    Write-Host "   Creating " -NoNewline -ForegroundColor White
    Write-Host ".venv" -NoNewline -ForegroundColor Magenta
    Write-Host "..." -NoNewline -ForegroundColor White
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) { Write-Host " OK" -ForegroundColor Green }
    else { Write-Error "Failed to create .venv"; exit 1 }
}

$pipPath = ".\.venv\Scripts\pip.exe"
if (-not (Test-Path $pipPath)) { Write-Error "pip not found in .venv"; exit 1 }

if (Test-Path "requirements-dev.txt") {
    Write-Host "   Installing " -NoNewline -ForegroundColor White
    Write-Host "requirements-dev.txt" -NoNewline -ForegroundColor Magenta
    Write-Host "..." -ForegroundColor White
    & $pipPath install -r requirements-dev.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Python dev dependencies installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
    } else {
        Write-Host "   Installation " -NoNewline -ForegroundColor White
        Write-Host "FAILED" -ForegroundColor Red
        $script:ErrorCount++
    }
} else { Write-Warning "requirements-dev.txt not found." }

# Step 3: JavaScript Development Setup
Write-Host "`n[Step 3/3] Setting up JavaScript development tools..." -ForegroundColor Yellow

if (-not (Test-Path "package.json")) {
    Write-Host "   Initializing " -NoNewline -ForegroundColor White
    Write-Host "package.json" -NoNewline -ForegroundColor Magenta
    Write-Host "..." -NoNewline -ForegroundColor White
    cmd /c "npm init -y" | Out-Null
    Write-Host " OK" -ForegroundColor Green
}

Write-Host "   Installing " -NoNewline -ForegroundColor White
Write-Host "jscpd, jest, playwright" -NoNewline -ForegroundColor Magenta
Write-Host "..." -ForegroundColor White

cmd /c "npm install jscpd jest jest-environment-jsdom @playwright/test --save-dev"

if ($LASTEXITCODE -eq 0) {
    Write-Host "   NPM packages installed " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "   NPM install " -NoNewline -ForegroundColor White
    Write-Host "FAILED" -ForegroundColor Red
    $script:ErrorCount++
}

# Playwright Browser Install
Write-Host "   Installing " -NoNewline -ForegroundColor White
Write-Host "Playwright browsers" -NoNewline -ForegroundColor Magenta
Write-Host "..." -ForegroundColor White
cmd /c "npx playwright install"
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Browsers installed " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Warning "Playwright browser install failed."
    $script:ErrorCount++
}

# Final Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($script:ErrorCount -eq 0) {
    Write-Host "   Development Setup Complete!" -ForegroundColor Green
} else {
    Write-Host "   Setup completed with $($script:ErrorCount) error(s)" -ForegroundColor Yellow
}
Write-Host "========================================`n" -ForegroundColor Cyan
