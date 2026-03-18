# setup-dev.ps1 - Development Environment Setup
# Calls setup.ps1 for production setup, then adds dev-specific tools

# Ensure we are in the project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   mockCMMS Development Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Error counter for final summary
$script:ErrorCount = 0

# ============================================================================
# STEP 1: RUN PRODUCTION SETUP
# ============================================================================
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "   PRODUCTION SETUP" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

$setupScript = Join-Path $scriptPath "setup.ps1"
if (-not (Test-Path $setupScript)) {
    Write-Error "setup.ps1 not found at: $setupScript"
    exit 1
}

Write-Host "Running production setup (setup.ps1)...`n" -ForegroundColor Yellow

# Execute setup.ps1 with CalledFromDev parameter to suppress header/footer
& $setupScript -CalledFromDev
$productionExitCode = $LASTEXITCODE

if ($productionExitCode -ne 0) {
    Write-Error "`nProduction setup failed. Cannot continue with development setup."
    exit $productionExitCode
}

Write-Host "`n" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Production Setup Complete" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# ============================================================================
# STEP 2: DEVELOPMENT TOOLS SETUP
# ============================================================================
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "   DEVELOPMENT TOOLS SETUP" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

# Function to refresh environment variables without restart
function Refresh-EnvPath {
    Write-Host "   Refreshing environment variables..." -ForegroundColor Gray
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Step 1: Check for Node.js (only dev requirement)
Write-Host "[Dev Step 1/6] Checking Node.js..." -ForegroundColor Yellow

# Step 1.1: Check for Node.js
function Check-Node {
    # First, check if npm command works
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        $v = npm --version 2>&1
        if ($v -match "(\d+)\.(\d+)") {
            Write-Host "   Found: " -NoNewline -ForegroundColor White
            Write-Host "npm $v" -NoNewline -ForegroundColor White
            Write-Host " OK" -ForegroundColor Green
            return $true
        }
    }

    # Check if Node.js is installed in common locations
    $nodeLocations = @(
        "${env:ProgramFiles}\nodejs",
        "${env:ProgramFiles(x86)}\nodejs",
        "${env:LOCALAPPDATA}\Programs\nodejs",
        "C:\Program Files\nodejs",
        "C:\Program Files (x86)\nodejs"
    )

    $nodeFound = $false
    foreach ($location in $nodeLocations) {
        if (Test-Path "$location\node.exe") {
            Write-Host "   Found Node.js at: $location" -ForegroundColor Yellow

            # Add to current session PATH if not already there
            if ($env:Path -notlike "*$location*") {
                $env:Path = "$location;$env:Path"
            }

            # Add to system PATH permanently
            try {
                $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
                if ($currentPath -notlike "*$location*") {
                    $newPath = "$location;$currentPath"
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

            $nodeFound = $true
            break
        }
    }

    # Re-check if npm works now
    if ($nodeFound) {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            $v = npm --version 2>&1
            if ($v -match "(\d+)\.(\d+)") {
                Write-Host "   Version: " -NoNewline -ForegroundColor White
                Write-Host "npm $v" -ForegroundColor Green
                return $true
            }
        }
    }

    return $false
}

if (-not (Check-Node)) {
    Write-Warning "   Node.js/npm not found. Attempting automatic installation via winget..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            # Try multiple possible Node.js package IDs
            $nodeIds = @("OpenJS.NodeJS", "OpenJS.NodeJS.LTS")
            $installed = $false

            foreach ($id in $nodeIds) {
                Write-Host "   Trying package ID: $id..." -ForegroundColor Gray

                # Start installation process
                $startTime = Get-Date
                $process = Start-Process -FilePath "winget" -ArgumentList "install -e --id $id --silent --accept-package-agreements --accept-source-agreements" -NoNewWindow -PassThru -Wait
                $duration = (Get-Date) - $startTime

                if ($process.ExitCode -eq 0) {
                    Write-Host "   Node.js installed successfully (took $([int]$duration.TotalSeconds) seconds)" -ForegroundColor Green
                    $installed = $true
                    break
                }
            }

            if ($installed) {
                Refresh-EnvPath

                # Re-check
                if (-not (Check-Node)) {
                    Write-Warning "   Node.js installed but not found in PATH."
                    Write-Host "   Please restart your terminal and run this script again." -ForegroundColor Yellow
                    exit 1
                }
            }
            else {
                Write-Warning "   Automatic installation via winget failed."
                Write-Host ""
                Write-Host "   Please install Node.js manually:" -ForegroundColor Yellow
                Write-Host "   1. Download from: https://nodejs.org/" -ForegroundColor White
                Write-Host "   2. Run installer (npm is included)" -ForegroundColor White
                Write-Host "   3. Restart terminal and run this script again" -ForegroundColor White
                exit 1
            }
        }
        catch {
            Write-Warning "   Automatic installation failed: $_"
            Write-Host "   Please install Node.js manually from https://nodejs.org" -ForegroundColor Yellow
            exit 1
        }
    }
    else {
        Write-Error "   Node.js not found and winget not available."
        Write-Host "   Please install Node.js manually from https://nodejs.org" -ForegroundColor Yellow
        exit 1
    }
}

# Step 2: Check for GitHub CLI
Write-Host "`n[Dev Step 2/6] Checking GitHub CLI..." -ForegroundColor Yellow

function Check-GitHubCLI {
    # First check if gh command is available
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        $v = gh --version 2>&1 | Select-Object -First 1
        if ($v -match "gh version (\S+)") {
            Write-Host "   Found: " -NoNewline -ForegroundColor White
            Write-Host "gh $($Matches[1])" -NoNewline -ForegroundColor White
            Write-Host " OK" -ForegroundColor Green
            return $true
        }
    }

    # Check common installation location
    $ghPath = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path $ghPath) {
        Write-Host "   Found GitHub CLI at: $ghPath" -ForegroundColor Yellow
        $ghDir = Split-Path -Parent $ghPath

        # Add to current session PATH
        $env:Path = "$ghDir;$env:Path"

        # Add to system PATH permanently
        try {
            $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
            if ($currentPath -notlike "*$ghDir*") {
                $newPath = "$ghDir;$currentPath"
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
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            $v = gh --version 2>&1 | Select-Object -First 1
            if ($v -match "gh version (\S+)") {
                Write-Host "   Version: " -NoNewline -ForegroundColor White
                Write-Host "gh $($Matches[1])" -ForegroundColor Green
                return $true
            }
        }
    }

    return $false
}

if (-not (Check-GitHubCLI)) {
    Write-Warning "   GitHub CLI not found. Attempting automatic installation via winget..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            Write-Host "   Trying package ID: GitHub.cli..." -ForegroundColor Gray

            # Start installation process
            $startTime = Get-Date
            $process = Start-Process -FilePath "winget" -ArgumentList "install -e --id GitHub.cli --silent --accept-package-agreements --accept-source-agreements" -NoNewWindow -PassThru -Wait
            $duration = (Get-Date) - $startTime

            if ($process.ExitCode -eq 0) {
                Write-Host "   GitHub CLI installed successfully (took $([int]$duration.TotalSeconds) seconds)" -ForegroundColor Green
                Refresh-EnvPath

                # Re-check
                if (-not (Check-GitHubCLI)) {
                    Write-Warning "   GitHub CLI installed but not found in PATH."
                    Write-Host "   Please restart your terminal to use 'gh' command." -ForegroundColor Yellow
                }
            }
            else {
                Write-Warning "   Automatic installation via winget failed."
                Write-Host "   GitHub CLI is optional but recommended for PR creation." -ForegroundColor Yellow
                Write-Host "   You can install it later from: https://cli.github.com" -ForegroundColor Gray
            }
        }
        catch {
            Write-Warning "   Automatic installation failed: $_"
            Write-Host "   GitHub CLI is optional. Install from: https://cli.github.com" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "   GitHub CLI not found (optional)." -ForegroundColor Gray
        Write-Host "   Install from: https://cli.github.com" -ForegroundColor Gray
    }
}

# Step 3: Python Development Tools
Write-Host "`n[Dev Step 3/6] Installing Python development tools..." -ForegroundColor Yellow

# Use correct Windows path (venv already exists from setup.ps1)
$pipPath = ".\.venv\Scripts\pip.exe"
$pythonPath = ".\.venv\Scripts\python.exe"

# Verify pip exists (should exist from production setup)
if (-not (Test-Path $pipPath)) {
    Write-Error "   pip not found at $pipPath"
    Write-Error "   Production setup may have failed. Run setup.ps1 manually."
    exit 1
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


# Step 4: JavaScript Development Tools
Write-Host "`n[Dev Step 4/6] Setting up JavaScript development tools..." -ForegroundColor Yellow

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

    # Install packages with warnings and notices suppressed
    $env:npm_config_loglevel = "error"
    npm install jscpd jest jest-environment-jsdom @playwright/test --save-dev 2>&1 |
        Where-Object { $_ -notmatch "^npm warn" -and $_ -notmatch "^npm notice" } |
        Out-Null
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

    # Suppress npm notices during Playwright install
    npx playwright install 2>&1 |
        Where-Object { $_ -notmatch "^npm notice" } |
        Out-Null

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

# ============================================================================
# STEP 5: GIT COMMIT TEMPLATE & HOOKS
# ============================================================================

Write-Host "`n[Dev Step 5/6] Setting up Conventional Commit template and commit-msg hook..." -ForegroundColor Yellow

$gitDir = Join-Path $projectRoot ".git"
$hookDir = Join-Path $gitDir "hooks"
$hookFile = Join-Path $hookDir "commit-msg"
$templateFile = Join-Path $projectRoot ".gitmessage"

# Set commit template
if (Test-Path $templateFile) {
    git config --local commit.template .gitmessage
    Write-Host "   [OK] .gitmessage set as commit template" -ForegroundColor Green
} else {
    Write-Host "   [WARN] .gitmessage not found, skipping commit template setup" -ForegroundColor Yellow
}

$hookTemplate = Join-Path $projectRoot ".githooks\commit-msg"

# Install commit-msg hook (DEPRECATED: Now handled by pre-commit in Step 6)
# if (Test-Path $hookTemplate) { ... }

# ============================================================================
# STEP 6: PRE-COMMIT HOOKS SETUP
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "   PRE-COMMIT HOOKS SETUP" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

Write-Host "[Dev Step 6/6] Setting up pre-commit hooks..." -ForegroundColor Yellow

# Use pre-commit from venv prioritized, then PATH
$preCommitExe = ".\.venv\Scripts\pre-commit.exe"
$hasPreCommit = $false

if (Test-Path $preCommitExe) {
    $hasPreCommit = $true
}
elseif (Get-Command pre-commit -ErrorAction SilentlyContinue) {
    $preCommitExe = "pre-commit"
    $hasPreCommit = $true
}

if ($hasPreCommit) {
    Write-Host "   Using: " -NoNewline -ForegroundColor White
    $preCommitVersion = & $preCommitExe --version 2>&1
    Write-Host "$preCommitVersion " -NoNewline -ForegroundColor White
    Write-Host "OK" -ForegroundColor Green

    # Install pre-commit hooks
    Write-Host "   Installing pre-commit hooks..." -ForegroundColor Yellow

    try {
        # Install pre-commit hooks (commits)
        & $preCommitExe install 2>&1 | Out-Null

        # Install commit-msg hooks (Conventional Commits)
        & $preCommitExe install --hook-type commit-msg 2>&1 | Out-Null

        # Install pre-push hooks
        & $preCommitExe install --hook-type pre-push 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "   Pre-commit hooks installed " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
            Write-Host "   Enabled:" -ForegroundColor White
            Write-Host "     - Pre-commit: Code formatting & validation" -ForegroundColor Gray
            Write-Host "     - Pre-push: Full validation & auto-release" -ForegroundColor Gray

            # Configure repo-local aliases for conflict-safe amend workflow.
            $safeAmendScript = Join-Path $projectRoot "scripts\safe-amend.ps1"
            $safeAmendScript = $safeAmendScript.Replace("/", "\")
            $safeAmendBase = "!pwsh -NoProfile -ExecutionPolicy Bypass -File `"$safeAmendScript`""

            try {
                $err1 = git config --local alias.safe-amend "$safeAmendBase amend" 2>&1
                if ($LASTEXITCODE -ne 0) { throw $err1 }

                $err2 = git config --local alias.safe-amend-cleanup "$safeAmendBase cleanup" 2>&1
                if ($LASTEXITCODE -ne 0) { throw $err2 }

                Write-Host "   Git aliases configured: " -NoNewline -ForegroundColor White
                Write-Host "git safe-amend, git safe-amend-cleanup" -ForegroundColor Magenta
            }
            catch {
                Write-Host "   Git alias setup " -NoNewline -ForegroundColor White
                Write-Host "FAILED" -ForegroundColor Yellow
                Write-Host "   Error: $_" -ForegroundColor Gray
                $script:ErrorCount++
            }
        }
        else {
            Write-Host ""
            Write-Host "   Pre-commit hook install " -NoNewline -ForegroundColor White
            Write-Host "FAILED" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
    catch {
        Write-Host ""
        Write-Host "   Pre-commit hook install " -NoNewline -ForegroundColor White
        Write-Host "FAILED" -ForegroundColor Red
        Write-Host "   Error: $_" -ForegroundColor Red
        $script:ErrorCount++
    }
}
else {
    Write-Host "   Pre-commit not found " -NoNewline -ForegroundColor White
    Write-Host "SKIPPED" -ForegroundColor Yellow
    Write-Host "   (Will be installed via requirements-dev.txt later)" -ForegroundColor Gray
}


# Final Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($script:ErrorCount -eq 0) {
    Write-Host "   Development Setup Complete!" -ForegroundColor Green
    Write-Host "   (Production + Dev Tools)" -ForegroundColor Gray
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
