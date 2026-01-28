# setup.ps1 - Enhanced mockCMMS Installation Script
# Provides detailed feedback and error handling for Windows environments

# Accept parameter to suppress header/footer when called from dev script
param(
    [switch]$CalledFromDev = $false
)

# Ensure we are in the project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# Only show header if not called from dev script
if (-not $CalledFromDev) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "   mockCMMS Installation Script" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

# Error counter for final summary
$script:ErrorCount = 0

# Function to refresh environment variables without restart
function Refresh-EnvPath {
    Write-Host "   Refreshing environment variables..." -ForegroundColor Gray
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Step 1: Check Prerequisites
Write-Host "[Step 1/5] Checking prerequisites..." -ForegroundColor Yellow

# Step 1.1: Check for Python
function Check-Python {
    # First check if python command is available
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
            } else {
                Write-Warning "   Found: $v (Python 3.12+ recommended)"
                return $true # Warning but proceed
            }
        }
    }

    # Check common Python installation locations
    $pythonLocations = @(
        "${env:LOCALAPPDATA}\Programs\Python\Python312\python.exe",
        "${env:LOCALAPPDATA}\Programs\Python\Python311\python.exe",
        "${env:LOCALAPPDATA}\Programs\Python\Python310\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe"
    )

    foreach ($location in $pythonLocations) {
        if (Test-Path $location) {
            Write-Host "   Found Python at: $location" -ForegroundColor Yellow
            $pythonDir = Split-Path -Parent $location

            # Add to current session PATH
            $env:Path = "$pythonDir;$pythonDir\Scripts;$env:Path"

            # Add to system PATH permanently
            try {
                $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
                if ($currentPath -notlike "*$pythonDir*") {
                    $newPath = "$pythonDir;$pythonDir\Scripts;$currentPath"
                    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
                    Write-Host "   Added to system PATH " -NoNewline -ForegroundColor White
                    Write-Host "OK" -ForegroundColor Green
                }
                else {
                    Write-Host "   Already in system PATH " -NoNewline -ForegroundColor White
                    Write-Host "OK" -ForegroundColor Green
                }
            }
            catch {
                Write-Warning "   Could not add to system PATH (may require admin rights). Added to current session only."
            }

            # Re-check if command works now
            if (Get-Command python -ErrorAction SilentlyContinue) {
                $v = python --version 2>&1
                Write-Host "   Version: " -NoNewline -ForegroundColor White
                Write-Host "$v" -ForegroundColor Green
                return $true
            }
        }
    }

    return $false
}

if (-not (Check-Python)) {
    Write-Warning "   Python not found. Attempting automatic installation via winget..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            # Try multiple possible Python package IDs
            $pythonIds = @("Python.Python.3.12", "Python.Python.3.11", "Python.Python.3")
            $installed = $false

            foreach ($id in $pythonIds) {
                Write-Host "   Trying package ID: $id..." -ForegroundColor Gray

                # Start installation process
                $startTime = Get-Date
                $process = Start-Process -FilePath "winget" -ArgumentList "install -e --id $id --silent --accept-package-agreements --accept-source-agreements" -NoNewWindow -PassThru -Wait
                $duration = (Get-Date) - $startTime

                if ($process.ExitCode -eq 0) {
                    Write-Host "   Python installed successfully (took $([int]$duration.TotalSeconds) seconds)" -ForegroundColor Green
                    $installed = $true
                    break
                }
            }

            if ($installed) {
                Refresh-EnvPath

                # Re-check
                if (-not (Check-Python)) {
                    Write-Warning "   Python installed but not found in PATH."
                    Write-Host "   Please restart your terminal and run this script again." -ForegroundColor Yellow
                    exit 1
                }
            }
            else {
                Write-Warning "   Automatic installation via winget failed."
                Write-Host ""
                Write-Host "   Please install Python manually:" -ForegroundColor Yellow
                Write-Host "   1. Download from: https://www.python.org/downloads/" -ForegroundColor White
                Write-Host "   2. Run installer and check 'Add Python to PATH'" -ForegroundColor White
                Write-Host "   3. Restart terminal and run this script again" -ForegroundColor White
                exit 1
            }
        }
        catch {
            Write-Warning "   Automatic installation failed: $_"
            Write-Host "   Please install Python manually from https://www.python.org" -ForegroundColor Yellow
            exit 1
        }
    }
    else {
        Write-Error "   Python not found and winget not available."
        Write-Host "   Please install Python manually from https://www.python.org" -ForegroundColor Yellow
        exit 1
    }
}


# Step 2: Create Virtual Environment
Write-Host "`n[Step 2/5] Setting up virtual environment..." -ForegroundColor Yellow
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


# Step 3: Install Dependencies
Write-Host "`n[Step 3/5] Installing core dependencies..." -ForegroundColor Yellow

# Use correct Windows path
$pipPath = ".\.venv\Scripts\pip.exe"
$pythonPath = ".\.venv\Scripts\python.exe"

# Verify pip exists
if (-not (Test-Path $pipPath)) {
    Write-Error "   pip not found at $pipPath"
    Write-Error "   Virtual environment may be corrupted. Try deleting .venv and running again."
    exit 1
}

# Upgrade pip (use python -m pip to avoid "cannot modify pip while running" error)
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
    Write-Warning "Could not upgrade pip, continuing with existing version..."
}

# Install core dependencies
if (Test-Path "requirements.txt") {
    # Check if Flask is already installed as a proxy for all dependencies
    $flaskCheck = & $pipPath show Flask 2>$null

    if ($flaskCheck -match "Name: Flask") {
        # Dependencies already installed - just verify
        Write-Host "   Core dependencies already installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
    }
    else {
        Write-Host "   Installing core dependencies from " -NoNewline -ForegroundColor White
        Write-Host "requirements.txt" -NoNewline -ForegroundColor Magenta
        Write-Host "..." -ForegroundColor White
        Write-Host ""

        # Show installation progress (visible output)
        & $pipPath install -r requirements.txt

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "   Core dependencies installed " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
        }
        else {
            Write-Host ""
            Write-Host "   Core dependencies installation " -NoNewline -ForegroundColor White
            Write-Host "FAILED" -ForegroundColor Red
            Write-Error "pip install failed. Check the output above for errors."
            exit 1
        }
    }
}
else {
    Write-Warning "   requirements.txt not found. Skipping core dependencies."
    $script:ErrorCount++
}

# Step 4: Install Modular Apps
Write-Host "`n[Step 4/5] Installing modular apps..." -ForegroundColor Yellow

$appsInstalled = 0

if (Test-Path "apps/planning/setup.py") {
    # Check if planning is already installed
    $planningCheck = & $pipPath show planning 2>$null

    if ($planningCheck -match "Name: planning") {
        # Editable packages need to be reinstalled to update links, but we can do it quietly
        Write-Host "   " -NoNewline
        Write-Host "Planning app" -NoNewline -ForegroundColor Magenta
        Write-Host " (re-linking)..." -NoNewline -ForegroundColor White
        & $pipPath install -e apps/planning --quiet 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Host " OK" -ForegroundColor Green
            $appsInstalled++
        }
        else {
            Write-Host " FAILED" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
    else {
        Write-Host "   Installing " -NoNewline -ForegroundColor White
        Write-Host "Planning app" -NoNewline -ForegroundColor Magenta
        Write-Host "..." -ForegroundColor White
        Write-Host ""

        & $pipPath install -e apps/planning

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "   " -NoNewline
            Write-Host "Planning app" -NoNewline -ForegroundColor Magenta
            Write-Host " installed " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
            $appsInstalled++
        }
        else {
            Write-Host ""
            Write-Host "   " -NoNewline
            Write-Host "Planning app" -NoNewline -ForegroundColor Magenta
            Write-Host " installation " -NoNewline -ForegroundColor White
            Write-Host "FAILED" -ForegroundColor Red
            Write-Warning "Check the output above for errors."
            $script:ErrorCount++
        }
    }
}
else {
    Write-Host "   Planning app not found (skipping)" -ForegroundColor Gray
}

if (Test-Path "apps/reports/setup.py") {
    # Check if reports is already installed
    $reportsCheck = & $pipPath show reports 2>$null

    if ($reportsCheck -match "Name: reports") {
        # Editable packages need to be reinstalled to update links, but we can do it quietly
        Write-Host "   " -NoNewline
        Write-Host "Reports app" -NoNewline -ForegroundColor Magenta
        Write-Host " (re-linking)..." -NoNewline -ForegroundColor White
        & $pipPath install -e apps/reports --quiet 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Host " OK" -ForegroundColor Green
            $appsInstalled++
        }
        else {
            Write-Host " FAILED" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
    else {
        Write-Host "`n   Installing " -NoNewline -ForegroundColor White
        Write-Host "Reports app" -NoNewline -ForegroundColor Magenta
        Write-Host "..." -ForegroundColor White
        Write-Host ""

        & $pipPath install -e apps/reports

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "   " -NoNewline
            Write-Host "Reports app" -NoNewline -ForegroundColor Magenta
            Write-Host " installed " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
            $appsInstalled++
        }
        else {
            Write-Host ""
            Write-Host "   " -NoNewline
            Write-Host "Reports app" -NoNewline -ForegroundColor Magenta
            Write-Host " installation " -NoNewline -ForegroundColor White
            Write-Host "FAILED" -ForegroundColor Red
            Write-Warning "Check the output above for errors."
            $script:ErrorCount++
        }
    }
}
else {
    Write-Host "   Reports app not found (skipping)" -ForegroundColor Gray
}


# Step 5: Environment Configuration
Write-Host "`n[Step 5/5] Configuring environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "   Created " -NoNewline -ForegroundColor White
        Write-Host ".env" -NoNewline -ForegroundColor Magenta
        Write-Host " from " -NoNewline -ForegroundColor White
        Write-Host ".env.example" -NoNewline -ForegroundColor Magenta
        Write-Host " " -NoNewline
        Write-Host "OK" -ForegroundColor Green
    }
    else {
        Write-Warning "   .env.example not found. You will need to create .env manually."
        $script:ErrorCount++
    }
}
else {
    Write-Host "   " -NoNewline
    Write-Host ".env" -NoNewline -ForegroundColor Magenta
    Write-Host " already exists " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green
}

# Final Summary - Only show if not called from dev script
if (-not $CalledFromDev) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    if ($script:ErrorCount -eq 0) {
        Write-Host "   Installation Complete!" -ForegroundColor Green
    }
    else {
        Write-Host "   Installation completed with $($script:ErrorCount) warning(s)" -ForegroundColor Yellow
    }
    Write-Host "========================================`n" -ForegroundColor Cyan


    # Display next steps
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "                        NEXT STEPS                              " -ForegroundColor Yellow
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Activate the virtual environment:" -ForegroundColor White
    Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  2. Run the application:" -ForegroundColor White
    Write-Host "     python run.py" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  3. (Optional) Setup development environment:" -ForegroundColor White
    Write-Host "     .\scripts\setup-dev.ps1" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
}
