# install.ps1

# Ensure we are in the project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "Starting mockCMMS installation..." -ForegroundColor Cyan

# 1. Check for Python
Write-Host "`nChecking for Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   Found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.12+."
    exit 1
}

# 2. Create Virtual Environment
Write-Host "`nSetting up virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "   Creating .venv..."
    python -m venv .venv
}
else {
    Write-Host "   .venv already exists." -ForegroundColor Gray
}

# 3. Install Dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
$pipPath = ".\.venv\Scripts\pip"
if (-not (Test-Path $pipPath)) {
    # Fallback for non-Windows or different venv structure if needed
    $pipPath = ".venv/bin/pip" 
}

# Upgrade pip
& $pipPath install --upgrade pip | Out-Null
Write-Host "   Pip upgraded." -ForegroundColor Gray

# Install requirements
& $pipPath install -r requirements.txt | Out-Null
Write-Host "   Core dependencies installed." -ForegroundColor Green

# Install modular apps
Write-Host "   Installing modular apps..." -ForegroundColor Gray
if (Test-Path "apps/planning") {
    & $pipPath install -e apps/planning | Out-Null
    Write-Host "   - Planning app installed." -ForegroundColor Green
}
if (Test-Path "apps/reports") {
    & $pipPath install -e apps/reports | Out-Null
    Write-Host "   - Reports app installed." -ForegroundColor Green
}

# 4. Environment Configuration
Write-Host "`nConfiguring environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "   Created .env from .env.example" -ForegroundColor Green
    }
    else {
        Write-Warning "   .env.example not found. Please create .env manually."
    }
}
else {
    Write-Host "   .env already exists." -ForegroundColor Gray
}

# 5. Database Initialization (Optional check)
Write-Host "`nChecking database..." -ForegroundColor Yellow
if (-not (Test-Path "instance")) {
    New-Item -ItemType Directory -Path "instance" | Out-Null
}

Write-Host "`nInstallation Complete!" -ForegroundColor Cyan
Write-Host "To run the application:"
Write-Host "1. Activate the environment: .\.venv\Scripts\Activate.ps1"
Write-Host "2. Run the app: python run.py"
