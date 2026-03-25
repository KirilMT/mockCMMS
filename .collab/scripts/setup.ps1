# Collaborative File Locking — Windows Setup
# Run this script from the project root: .\.collab\scripts\setup.ps1

$ErrorActionPreference = "Continue"
$CollabRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ProjectRoot = Split-Path -Parent $CollabRoot

Write-Host "`n=== Collaborative File Locking — Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

try {
    $version = & $python --version 2>&1
    Write-Host "  OK: $version" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Python not found. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

# 2. Check supabase package
Write-Host "[2/4] Checking supabase package..." -ForegroundColor Yellow
try {
    & $python -c "import supabase" 2>$null
    Write-Host "  OK: supabase-py is installed" -ForegroundColor Green
} catch {
    Write-Host "  WARN: supabase-py not installed. Installing..." -ForegroundColor Yellow
    & $python -m pip install supabase python-dotenv --quiet
    Write-Host "  OK: supabase-py installed" -ForegroundColor Green
}

# 3. Check .env
Write-Host "[3/4] Checking .env file..." -ForegroundColor Yellow
$envPath = Join-Path $ProjectRoot ".env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    $hasUrl = $envContent -match "SUPABASE_URL=(?!your)"
    $hasKey = $envContent -match "SUPABASE_ANON_KEY=(?!your)"

    if ($hasUrl -and $hasKey) {
        Write-Host "  OK: .env has Supabase credentials" -ForegroundColor Green
    } else {
        Write-Host "  WARN: .env exists but Supabase credentials may be placeholder values." -ForegroundColor Yellow
        Write-Host "  Edit .env and set SUPABASE_URL and SUPABASE_ANON_KEY." -ForegroundColor Yellow
        Write-Host "  Reference: .collab\.env.example" -ForegroundColor Yellow
    }
} else {
    Write-Host "  WARN: .env not found at project root." -ForegroundColor Yellow
    Write-Host "  Copy .collab\.env.example to .env and fill in your credentials." -ForegroundColor Yellow
}

# 4. Install hooks
Write-Host "[4/4] Installing git hooks..." -ForegroundColor Yellow
$hooksDir = Join-Path $ProjectRoot ".git\hooks"
$collabHooks = Join-Path $CollabRoot ".collab\hooks"

foreach ($hook in @("pre-commit", "post-commit", "pre-push")) {
    $src = Join-Path $collabHooks $hook
    $dst = Join-Path $hooksDir $hook
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  OK: Installed $hook hook" -ForegroundColor Green
    }
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Ensure .env has SUPABASE_URL and SUPABASE_ANON_KEY set"
Write-Host "  2. Run the schema in Supabase SQL Editor: .collab\schema.sql"
Write-Host "  3. Test: python collab.py active"
Write-Host ""
