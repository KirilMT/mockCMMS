# setup-dev.ps1 - Development Environment Setup
# Sets up development tools for Python and JavaScript

# Ensure we are in the project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   mockCMMS Development Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Error counter for final summary
$script:ErrorCount = 0

# Function to refresh environment variables without restart
function Refresh-EnvPath {
    Write-Host "   Refreshing environment variables..." -ForegroundColor Gray
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Step 1: Check Prerequisites
Write-Host "[Step 1/3] Checking prerequisites..." -ForegroundColor Yellow

# Step 1.1: Check for Python
function Check-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $v = python --version 2>&1
        if ($v -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 12) {
                Write-Host "   Found: " -NoNewline -ForegroundColor White
                Write-Host "$v" -NoNewline -ForegroundColor White
                Write-Host " OK" -ForegroundColor Green
                return $true
            }
            else {
                Write-Warning "   Found: $v (Python 3.12+ recommended)"
                return $true # Warning but proceed
            }
        }
    }
    return $false
}

if (-not (Check-Python)) {
    Write-Warning "   Python not found. Attempting to install latest version via winget..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            # Attempt silent install of latest Python 3
            Write-Host "   Installing Python..." -ForegroundColor Magenta
            winget install -e --id Python.Python.3 --silent --accept-package-agreements --accept-source-agreements

            if ($LASTEXITCODE -eq 0) {
                Write-Host "   Python installed successfully." -ForegroundColor Green
                Refresh-EnvPath

                # Re-check
                if (-not (Check-Python)) {
                    Write-Error "   Python installed but not found in PATH. Please restart terminal."
                    exit 1
                }
            }
            else {
                Write-Error "   Failed to install Python via winget."
                exit 1
            }
        }
        catch {
            Write-Error "   An error occurred during Python installation."
            exit 1
        }
    }
    else {
        Write-Error "   Python is not installed and winget (App Installer) is not available."
        Write-Error "   Please install Python 3.12+ manually from https://python.org"
        exit 1
    }
}

# Step 1.2: Check for Node.js
function Check-Node {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        $v = npm --version 2>&1
        if ($v -match "(\d+)\.(\d+)") {
            Write-Host "   Found: " -NoNewline -ForegroundColor White
            Write-Host "npm $v" -NoNewline -ForegroundColor White
            Write-Host " OK" -ForegroundColor Green
            return $true
        }
    }
    return $false
}

if (-not (Check-Node)) {
    Write-Warning "   Node.js/npm not found. Attempting to install latest version via winget..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            # Attempt silent install of Node.js
            Write-Host "   Installing Node.js..." -ForegroundColor Magenta
            winget install -e --id OpenJS.NodeJS --silent --accept-package-agreements --accept-source-agreements

            if ($LASTEXITCODE -eq 0) {
                Write-Host "   Node.js installed successfully." -ForegroundColor Green
                Refresh-EnvPath

                # Re-check
                if (-not (Check-Node)) {
                    Write-Error "   Node.js installed but not found in PATH. Please restart terminal."
                    exit 1
                }
            }
            else {
                Write-Error "   Failed to install Node.js via winget."
                exit 1
            }
        }
        catch {
            Write-Error "   An error occurred during Node.js installation."
            exit 1
        }
    }
    else {
        Write-Error "   Node.js is not installed and winget is not available."
        Write-Error "   Please install Node.js manually from https://nodejs.org"
        exit 1
    }
}


# Step 2: Python Development Setup
Write-Host "`n[Step 2/3] Setting up Python development tools..." -ForegroundColor Yellow

# Use correct Windows path
$pipPath = ".\.venv\Scripts\pip.exe"
$pythonPath = ".\.venv\Scripts\python.exe"

# Create venv if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "   Creating " -NoNewline -ForegroundColor White
    Write-Host ".venv" -NoNewline -ForegroundColor Magenta
    Write-Host "..." -NoNewline -ForegroundColor White
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    }
    else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Error "Failed to create virtual environment."
        exit 1
    }
}
else {
    Write-Host "   Virtual environment already exists " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green
}

# Verify pip exists
if (-not (Test-Path $pipPath)) {
    Write-Error "   pip not found at $pipPath"
    Write-Error "   Virtual environment may be corrupted. Try deleting .venv and running again."
    exit 1
}

# Upgrade pip first
Write-Host "   Checking " -NoNewline -ForegroundColor White
Write-Host "pip" -NoNewline -ForegroundColor Magenta
Write-Host "..." -NoNewline -ForegroundColor White

# Capture output to check if upgrade occurred
$pipOutput = (& $pythonPath -m pip install --upgrade pip 2>&1) -join " "
$pipExitCode = $LASTEXITCODE

if ($pipExitCode -eq 0) {
    # Get current pip version
    $pipVersionOutput = (& $pythonPath -m pip --version 2>&1) -join " "
    $pipVersion = ""
    if ($pipVersionOutput -match "pip ([0-9]+\.[0-9]+(\.[0-9]+)?)") {
        $pipVersion = $Matches[1]
    }

    # Check if it was already up to date or upgraded
    if ($pipOutput -match "Requirement already satisfied") {
        Write-Host " up to date " -NoNewline -ForegroundColor Green
        if ($pipVersion) { Write-Host "(v$pipVersion)" -ForegroundColor Gray } else { Write-Host "" }
    }
    else {
        Write-Host " upgraded " -NoNewline -ForegroundColor Green
        if ($pipVersion) { Write-Host "(v$pipVersion)" -ForegroundColor Gray } else { Write-Host "" }
    }
}
else {
    Write-Host " FAILED (non-critical)" -ForegroundColor Yellow
}

# Install core requirements first
if (Test-Path "requirements.txt") {
    # Check if Flask is already installed as a proxy for all dependencies
    $flaskCheck = & $pipPath show Flask 2>$null

    if ($flaskCheck -match "Name: Flask") {
        Write-Host "   Core dependencies already installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
    }
    else {
        Write-Host "   Installing " -NoNewline -ForegroundColor White
        Write-Host "requirements.txt" -NoNewline -ForegroundColor Magenta
        Write-Host " (core)..." -ForegroundColor White
        Write-Host ""

        # Show installation progress (visible output)
        & $pipPath install -r requirements.txt 2>&1 | Where-Object { $_ -notmatch "^ERROR:" -and $_ -notmatch "planning .* requires" }

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "   Core dependencies installed " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
        }
        else {
            Write-Host ""
            Write-Host "   Core dependencies installation " -NoNewline -ForegroundColor White
            Write-Host "FAILED" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
}
else {
    Write-Warning "   requirements.txt not found. Skipping core dependencies."
    $script:ErrorCount++
}

# Install dev requirements
if (Test-Path "requirements-dev.txt") {
    # Check if a key dev dependency is already installed
    $blackCheck = & $pipPath show black 2>$null

    if ($blackCheck -match "Name: black") {
        Write-Host "   Dev dependencies already installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
    }
    else {
        Write-Host "   Installing " -NoNewline -ForegroundColor White
        Write-Host "requirements-dev.txt" -NoNewline -ForegroundColor Magenta
        Write-Host "..." -ForegroundColor White
        Write-Host ""

        # Show installation progress (filter noise)
        & $pipPath install -r requirements-dev.txt 2>&1 | Where-Object { $_ -notmatch "^ERROR:" -and $_ -notmatch "planning .* requires" }

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "   Python dev dependencies installed " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
        }
        else {
            Write-Host ""
            Write-Host "   Installation " -NoNewline -ForegroundColor White
            Write-Host "FAILED" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
}
else {
    Write-Warning "   requirements-dev.txt not found."
    $script:ErrorCount++
}


# Step 3: JavaScript Development Setup
Write-Host "`n[Step 3/3] Setting up JavaScript development tools..." -ForegroundColor Yellow

if (-not (Test-Path "package.json")) {
    Write-Host "   Initializing " -NoNewline -ForegroundColor White
    Write-Host "package.json" -NoNewline -ForegroundColor Magenta
    Write-Host "..." -NoNewline -ForegroundColor White
    npm init -y 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    }
    else {
        Write-Host " FAILED" -ForegroundColor Red
        $script:ErrorCount++
    }
}
else {
    Write-Host "   package.json already exists " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green
}

# Check if npm packages are already installed
$packagesInstalled = $false
if (Test-Path "node_modules/jscpd") {
    if (Test-Path "node_modules/jest") {
        if (Test-Path "node_modules/@playwright/test") {
            $packagesInstalled = $true
        }
    }
}

if ($packagesInstalled) {
    Write-Host "   NPM dev packages already installed " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green
}
else {
    Write-Host "   Installing " -NoNewline -ForegroundColor White
    Write-Host "jscpd, jest, playwright" -NoNewline -ForegroundColor Magenta
    Write-Host "..." -ForegroundColor White
    Write-Host ""

    # Install packages with warnings suppressed
    $env:npm_config_loglevel = "error"
    npm install jscpd jest jest-environment-jsdom @playwright/test --save-dev 2>&1 | Where-Object { $_ -notmatch "^npm warn" }
    $env:npm_config_loglevel = $null

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "   NPM packages installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "   NPM install " -NoNewline -ForegroundColor White
        Write-Host "FAILED" -ForegroundColor Red
        $script:ErrorCount++
    }
}

# Playwright Browser Install - Check if already installed
$playwrightBrowsersPath = "$env:USERPROFILE\AppData\Local\ms-playwright"
$browsersInstalled = $false
if (Test-Path $playwrightBrowsersPath) {
    $browserFolders = Get-ChildItem $playwrightBrowsersPath -Directory -ErrorAction SilentlyContinue
    if ($browserFolders.Count -ge 3) {
        $browsersInstalled = $true
    }
}

if ($browsersInstalled) {
    Write-Host "   Playwright browsers already installed " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green
}
else {
    Write-Host "   Installing " -NoNewline -ForegroundColor White
    Write-Host "Playwright browsers" -NoNewline -ForegroundColor Magenta
    Write-Host "..." -ForegroundColor White

    npx playwright install 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Browsers installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
    }
    else {
        Write-Host "   Browser install " -NoNewline -ForegroundColor White
        Write-Host "FAILED" -ForegroundColor Red
        $script:ErrorCount++
    }
}


# Final Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($script:ErrorCount -eq 0) {
    Write-Host "   Development Setup Complete!" -ForegroundColor Green
}
else {
    Write-Host "   Setup completed with $($script:ErrorCount) warning(s)" -ForegroundColor Yellow
}
Write-Host "========================================`n" -ForegroundColor Cyan


# Display next steps
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                        NEXT STEPS                              " -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Activate the virtual environment (if not already active):" -ForegroundColor White
Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Magenta
Write-Host ""
Write-Host "  2. Run the application:" -ForegroundColor White
Write-Host "     python run.py" -ForegroundColor Magenta
Write-Host ""
Write-Host "  3. Run tests:" -ForegroundColor White
Write-Host "     pytest" -ForegroundColor Magenta
Write-Host ""
Write-Host "  4. Run E2E tests:" -ForegroundColor White
Write-Host "     npx playwright test" -ForegroundColor Magenta
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
