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
# Normalize path (ensure relative to repo root)
$pipPath = $pipPath.Replace('..\', '.\')
$pythonPath = $pythonPath.Replace('..\', '.\')

# Ensure pythonw.exe exists in the venv (required to avoid console popups on Windows)
$pythonwPath = ".\.venv\Scripts\pythonw.exe"
if (Test-Path $pythonwPath) {
    Write-Host "   Found: pythonw.exe in venv" -ForegroundColor Green
}
elseif (Test-Path $pythonPath) {
    try {
        Copy-Item -Path $pythonPath -Destination $pythonwPath -Force
        Write-Host "   Created: pythonw.exe in venv (copied from python.exe)" -ForegroundColor Green
    }
    catch {
        Write-Host "   Warning: pythonw.exe not found and could not be created in venv." -ForegroundColor Yellow
        Write-Host "            daemon-start will attempt to fallback to a detached python process." -ForegroundColor Yellow
    }
}
else {
    Write-Host "   Warning: venv python not found; cannot ensure pythonw.exe presence." -ForegroundColor Yellow
}

# Verify pip exists (should exist from production setup)
if (-not (Test-Path $pipPath)) {
    Write-Error "   pip not found at $pipPath"
    Write-Error "   Production setup may have failed. Run setup.ps1 manually."
    exit 1
}


# Install or update dev requirements efficiently
if (Test-Path "requirements-dev.txt") {
    # Pre-check: detect if supabase is already present before installing dev requirements
    $preSupabaseFound = $false
    $preSupabaseVersion = ""
    try {
        $showOut = & $pipPath show supabase 2>&1
        if ($LASTEXITCODE -eq 0 -and $showOut) {
            $preSupabaseFound = $true
            foreach ($l in $showOut -split "`n") {
                if ($l -match "^Version:\s*(.*)") { $preSupabaseVersion = $Matches[1].Trim() }
            }
        }
    }
    catch { }

    Write-Host "   Ensuring all dev dependencies are installed and up-to-date..." -ForegroundColor White
    & $pipPath install --upgrade --upgrade-strategy only-if-needed -r requirements-dev.txt > $null 2>&1
    # Post-check: detect if supabase got installed by the requirements install
    $postSupabaseFound = $false
    $postSupabaseVersion = ""
    try {
        $showOut2 = & $pipPath show supabase 2>&1
        if ($LASTEXITCODE -eq 0 -and $showOut2) {
            $postSupabaseFound = $true
            foreach ($l in $showOut2 -split "`n") {
                if ($l -match "^Version:\s*(.*)") { $postSupabaseVersion = $Matches[1].Trim() }
            }
        }
    }
    catch { $postSupabaseFound = $false; $postSupabaseVersion = "" }

    # If requirements install didn't bring in supabase, attempt an explicit install
    if (-not $preSupabaseFound -and -not $postSupabaseFound) {
        Write-Host "   supabase still not present after requirements install; attempting explicit pip install supabase psutil plyer..." -ForegroundColor Yellow
        $installOutput = & $pipPath install supabase psutil plyer 2>&1
        if ($LASTEXITCODE -eq 0) {
            try {
                $showOut3 = & $pipPath show supabase 2>&1
                if ($LASTEXITCODE -eq 0 -and $showOut3) {
                    $postSupabaseFound = $true
                    foreach ($l in $showOut3 -split "`n") {
                        if ($l -match "^Version:\s*(.*)") { $postSupabaseVersion = $Matches[1].Trim() }
                    }
                }
            }
            catch { $postSupabaseFound = $false; $postSupabaseVersion = "" }
            if ($postSupabaseFound) {
                Write-Host ""
                Write-Host "   Installed: " -NoNewline -ForegroundColor White
                Write-Host "supabase $postSupabaseVersion" -NoNewline -ForegroundColor Magenta
                Write-Host " OK" -ForegroundColor Green
                Write-Host "   supabase installed and import OK (version: $postSupabaseVersion)" -ForegroundColor Green
            }
            else {
                Write-Host "   supabase install attempted but pip show still fails. Install output:" -ForegroundColor Yellow
                Write-Host $installOutput -ForegroundColor Gray
            }
        }
        else {
            Write-Host "   Explicit pip install failed. Pip output:" -ForegroundColor Yellow
            Write-Host $installOutput -ForegroundColor Gray
        }
    }
    elseif (-not $preSupabaseFound -and $postSupabaseFound) {
        Write-Host ""
        Write-Host "   Installed: " -NoNewline -ForegroundColor White
        Write-Host "supabase $postSupabaseVersion" -NoNewline -ForegroundColor Magenta
        Write-Host " OK" -ForegroundColor Green
        Write-Host "   supabase installed and import OK (version: $postSupabaseVersion)" -ForegroundColor Green
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        # Robust check for all required dev tool executables
        $devTools = @{
            'conventional-pre-commit.exe' = 'conventional-pre-commit'
            'pre-commit.exe'              = 'pre-commit'
            'black.exe'                   = 'black'
            'isort.exe'                   = 'isort'
            'docformatter.exe'            = 'docformatter'
            'flake8.exe'                  = 'flake8'
            'ruff.exe'                    = 'ruff'
            'pylint.exe'                  = 'pylint'
            'mypy.exe'                    = 'mypy'
            'pytest.exe'                  = 'pytest'
            'yamllint.exe'                = 'yamllint'
            'collab.exe'                  = 'collab-runtime'
        }
        $missingTools = @()
        foreach ($exe in $devTools.Keys) {
            $exePath = ".venv\Scripts\$exe"
            if (-not (Test-Path $exePath)) {
                Write-Host "   $exe missing, attempting to (re)install $($devTools[$exe])..." -ForegroundColor Yellow
                & $pipPath install --force-reinstall $($devTools[$exe]) > $null 2>&1
                if (Test-Path $exePath) {
                    Write-Host "   $exe installed successfully." -ForegroundColor Green
                }
                else {
                    Write-Host "   WARNING: $exe still missing after install!" -ForegroundColor Red
                    $missingTools += $exe
                }
            }
        }
        if ($missingTools.Count -eq 0) {
            Write-Host ""
            Write-Host "   Python dev dependencies are present and up-to-date " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
        }
        else {
            Write-Host "   WARNING: Some dev tool executables are still missing: $($missingTools -join ', ')" -ForegroundColor Red
        }
    }
    else {
        Write-Host ""
        Write-Host "   Installation " -NoNewline -ForegroundColor White
        Write-Host "FAILED" -ForegroundColor Red
        $script:ErrorCount++
    }
}
else {
    Write-Warning "   requirements-dev.txt not found."
    $script:ErrorCount++
}

# Supabase check/installation is handled during the dev requirements install block above.
# The Step 7 summary below will show the final installed status.

# Export final supabase detection variables for use in Step 7 summary
if ($null -eq $supabaseFound) { $supabaseFound = $false }
if ($null -eq $supabaseVersion) { $supabaseVersion = "" }
if ($postSupabaseFound) { $supabaseFound = $true; $supabaseVersion = $postSupabaseVersion }
elseif ($preSupabaseFound) { $supabaseFound = $true; $supabaseVersion = $preSupabaseVersion }

# collab-runtime is a plain external dev dependency: it is pinned in
# requirements-dev.txt and installed by `pip install -r requirements-dev.txt`
# above, with its 'collab.exe' covered by the dev-tools executable check - the
# exact same handling as black/flake8/etc. There is no dedicated collab install
# or verification step. To change the version, edit the pin in requirements-dev.txt.


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
$templateFile = Join-Path $projectRoot ".gitmessage"

# Set commit template
if (Test-Path $templateFile) {
    git config --local commit.template .gitmessage
    Write-Host "   [OK] .gitmessage set as commit template" -ForegroundColor Green
}
else {
    Write-Host "   [WARN] .gitmessage not found, skipping commit template setup" -ForegroundColor Yellow
}

# Note: Hooks are managed by pre-commit tool in Step 6.

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
    Write-Host "   Installing repository hooks (framework mode)..." -ForegroundColor Yellow

    # Include post-rewrite so watcher is started on more git operations
    # (matches previous branch behavior which triggered watcher on rewrite-like ops)
    $hookTypes = @("pre-commit", "post-commit", "post-checkout", "post-merge", "post-rewrite", "pre-push")
    foreach ($type in $hookTypes) {
        Write-Host "     - Installing $type hook..." -ForegroundColor Gray
        & $preCommitExe install --hook-type $type --overwrite 2>&1 | Out-Null
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Framework hooks installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
        Write-Host "   Enabled:" -ForegroundColor White
        Write-Host "     - Validations: pre-commit (lint/test), pre-push (full)" -ForegroundColor Gray
        Write-Host "     - Live Locking hooks: post-checkout, post-merge, post-commit" -ForegroundColor Gray

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

        # Overlay lock hooks on top of the pre-commit framework hooks.
        # The lock hooks are the entry point - they handle lock acquisition and
        # then chain to 'pre-commit run' for validations. This MUST run AFTER
        # 'pre-commit install' so our hooks win (framework hooks are overwritten).
        Write-Host "   Overlaying collab locking hooks..." -ForegroundColor Yellow
        $collabHooksDir = Join-Path $projectRoot "scripts\hooks"
        foreach ($hookName in @("pre-commit", "post-commit", "pre-push")) {
            $srcHook = Join-Path $collabHooksDir $hookName
            $dstHook = Join-Path $hookDir $hookName
            if (Test-Path $srcHook) {
                Copy-Item $srcHook $dstHook -Force
                Write-Host "     - Installed collab $hookName hook (chains to framework)" -ForegroundColor Gray
            }
        }
        Write-Host "   Collab hooks installed " -NoNewline -ForegroundColor White
        Write-Host "OK" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "   Pre-commit hook install " -NoNewline -ForegroundColor White
        Write-Host "FAILED" -ForegroundColor Red
        $script:ErrorCount++
    }
}
else {
    Write-Host "   Pre-commit not found " -NoNewline -ForegroundColor White
    Write-Host "SKIPPED" -ForegroundColor Yellow
    Write-Host "   (Will be installed via requirements-dev.txt later)" -ForegroundColor Gray
}


# ============================================================================
# STEP 7: SUPABASE REALTIME LOCKING SETUP (REQUIRED)
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "   SUPABASE LOCKING SETUP (REQUIRED)" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

Write-Host "[Dev Step 7/7] Configure Supabase Realtime for live locks (required)..." -ForegroundColor Yellow

$envFile = Join-Path $projectRoot ".env"

# Show Supabase client status summary so user sees clearly at the start of Step 7
if ($supabaseFound) {
    Write-Host "   Supabase client: " -NoNewline -ForegroundColor White
    Write-Host "supabase $supabaseVersion" -NoNewline -ForegroundColor Magenta
    Write-Host " OK" -ForegroundColor Green
}
else {
    Write-Host "   Supabase client: NOT INSTALLED" -ForegroundColor Yellow
    Write-Host "   To install, run: .\.venv\Scripts\pip.exe install supabase" -ForegroundColor Gray
}

# Supabase locking is required for all developers. Ensure variables are provided.
$supabaseUrl = ""
$anonKey = ""
$serviceKey = ""

# Read example values to detect placeholder copies
$exampleFile = Join-Path $projectRoot ".env.example"
$exampleSupabaseUrl = ""; $exampleAnonKey = ""; $exampleServiceKey = ""
if (Test-Path $exampleFile) {
    foreach ($line in Get-Content $exampleFile) {
        if ($line -match "SUPABASE_URL=(.*)") { $exampleSupabaseUrl = $Matches[1].Trim() }
        if ($line -match "SUPABASE_ANON_KEY=(.*)") { $exampleAnonKey = $Matches[1].Trim() }
        if ($line -match "SUPABASE_SERVICE_ROLE_KEY=(.*)") { $exampleServiceKey = $Matches[1].Trim() }
    }
}

# Read actual .env if present
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match "SUPABASE_URL=(.*)") { $supabaseUrl = $Matches[1].Trim() }
        if ($line -match "SUPABASE_ANON_KEY=(.*)") { $anonKey = $Matches[1].Trim() }
        if ($line -match "SUPABASE_SERVICE_ROLE_KEY=(.*)") { $serviceKey = $Matches[1].Trim() }
    }
}

function Is-Placeholder($val, $exampleVal) {
    if (-not $val) { return $true }
    # If equal to example placeholder, treat as missing
    if ($exampleVal -and $val -eq $exampleVal) { return $true }
    # Common placeholder patterns
    if ($val -match "your[_-]" -or $val -match "your-project" -or $val -match "example" -or $val -match "CHANGE_ME") { return $true }
    return $false
}

if (Is-Placeholder $supabaseUrl $exampleSupabaseUrl) { $supabaseUrl = Read-Host "   SUPABASE_URL (e.g. https://your-project.supabase.co) - REQUIRED" }
if (Is-Placeholder $anonKey $exampleAnonKey) { $anonKey = Read-Host "   SUPABASE_ANON_KEY - REQUIRED" }
if (Is-Placeholder $serviceKey $exampleServiceKey) { $serviceKey = Read-Host "   SUPABASE_SERVICE_ROLE_KEY (optional, recommended for admin tasks)" }

if (-not $supabaseUrl -or -not $anonKey) {
    Write-Error "SUPABASE_URL and SUPABASE_ANON_KEY are required for live locking. Setup cannot continue."
    exit 1
}

# Persist settings
$newEnv = @()
$foundUse = $false; $foundUrl = $false; $foundAnon = $false; $foundService = $false
if (Test-Path $envFile) {
    foreach ($line in (Get-Content $envFile)) {
        if ($line -match "^USE_SUPABASE=") { $newEnv += "USE_SUPABASE=1"; $foundUse = $true }
        elseif ($line -match "^SUPABASE_URL=") { $newEnv += "SUPABASE_URL=$supabaseUrl"; $foundUrl = $true }
        elseif ($line -match "^SUPABASE_ANON_KEY=") { $newEnv += "SUPABASE_ANON_KEY=$anonKey"; $foundAnon = $true }
        elseif ($line -match "^SUPABASE_SERVICE_ROLE_KEY=") { $newEnv += "SUPABASE_SERVICE_ROLE_KEY=$serviceKey"; $foundService = $true }
        else { $newEnv += $line }
    }
}
if (-not $foundUse) { $newEnv += "USE_SUPABASE=1" }
if (-not $foundUrl) { $newEnv += "SUPABASE_URL=$supabaseUrl" }
if (-not $foundAnon) { $newEnv += "SUPABASE_ANON_KEY=$anonKey" }
if (-not $foundService) { $newEnv += "SUPABASE_SERVICE_ROLE_KEY=$serviceKey" }
$newEnv | Out-File -FilePath $envFile -Encoding utf8
Write-Host "   Supabase configuration saved to .env" -ForegroundColor Green

# Auto-start note: the watcher is started automatically by git hooks
# (post-checkout, post-merge, post-commit) and by IDE integrations.
# We no longer register OS-level scheduled tasks here to avoid long-running
# background processes tied to user sessions. If you want to start the
# watcher manually for debugging, run:
#   .\.venv\Scripts\collab.exe daemon-start

# Install Collab Git Hooks
Write-Host "`n   Installing Collab Git Hooks..." -ForegroundColor Yellow
$hooksDir = Join-Path $projectRoot ".git\hooks"
$collabHooks = Join-Path $projectRoot "scripts\hooks"

foreach ($hook in @("pre-commit", "post-commit", "pre-push", "commit-msg")) {
    $src = Join-Path $collabHooks $hook
    $dst = Join-Path $hooksDir $hook
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "     - Copied $hook" -ForegroundColor Gray
    }
}
Write-Host "   Collab Git Hooks installed " -NoNewline -ForegroundColor White
Write-Host "OK" -ForegroundColor Green


# IDE Auto-Detection & Configuration
# Priority: definitive VS Code/Cursor signals first (env + process tree), then
# JetBrains. TERMINAL_EMULATOR=JetBrains-JediTerm is often missing outside a
# JetBrains terminal but can also leak from user/system env and falsely trigger
# when running from Cursor (e.g. Code Runner) where TERM_PROGRAM is unset.

function Test-SetupDevAncestorProcessMatch {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$NameWildcards
    )
    try {
        $current = Get-CimInstance -ClassName Win32_Process `
            -Filter "ProcessId=$PID" `
            -ErrorAction Stop
        $guard = 0
        while ($null -ne $current -and $guard -lt 20) {
            $procName = $current.Name
            foreach ($pattern in $NameWildcards) {
                if ($procName -like $pattern) {
                    return $true
                }
            }
            $parentPid = [int]$current.ParentProcessId
            if ($parentPid -le 0) {
                break
            }
            $current = Get-CimInstance -ClassName Win32_Process `
                -Filter "ProcessId=$parentPid" `
                -ErrorAction SilentlyContinue
            $guard++
        }
    }
    catch {
        return $false
    }
    return $false
}

function Test-SetupDevCursorHost {
    <#
    .SYNOPSIS
        True when setup is running under Cursor (env or process tree), not plain VS Code.
    #>
    if ($null -ne $env:CURSOR_TRACE_ID -and $env:CURSOR_TRACE_ID -ne "") {
        return $true
    }
    if ($null -ne $env:CURSOR_AGENT -and $env:CURSOR_AGENT -ne "") {
        return $true
    }
    return (Test-SetupDevAncestorProcessMatch -NameWildcards @("Cursor*"))
}

function Test-SetupDevCliPathIsUnderCursorInstall {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CliPath
    )
    if ([string]::IsNullOrWhiteSpace($CliPath)) {
        return $false
    }
    # Windows: ...\AppData\Local\Programs\cursor\... (case-insensitive)
    return $CliPath -match '(?i)[\\/]Programs[\\/]cursor[\\/]'
}

function Get-SetupDevCursorInstallRootFromProcess {
    <#
    .SYNOPSIS
        Directory containing Cursor.exe when an ancestor process is Cursor (for CLI discovery).
    #>
    try {
        $current = Get-CimInstance -ClassName Win32_Process `
            -Filter "ProcessId=$PID" `
            -ErrorAction Stop
        $guard = 0
        while ($null -ne $current -and $guard -lt 25) {
            if ($current.Name -like "Cursor*") {
                $exePath = $current.ExecutablePath
                if (-not [string]::IsNullOrWhiteSpace($exePath)) {
                    return (Split-Path -Parent $exePath)
                }
            }
            $parentPid = [int]$current.ParentProcessId
            if ($parentPid -le 0) {
                break
            }
            $current = Get-CimInstance -ClassName Win32_Process `
                -Filter "ProcessId=$parentPid" `
                -ErrorAction SilentlyContinue
            $guard++
        }
    }
    catch {
        return $null
    }
    return $null
}

function Resolve-SetupDevCursorCliPath {
    <#
    .SYNOPSIS
        Full path to cursor.cmd (or equivalent) without requiring the user PATH shim.
    .NOTES
        Cursor ships launchers under LocalAppData\Programs\cursor\resources\app\bin\ even when
        "Install shell command" was never run (unlike many VS Code installs that add code.cmd to PATH).
    #>
    $fromPath = Get-Command cursor -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }
    $relCandidates = @(
        "resources\app\bin\cursor.cmd",
        "resources\app\bin\cursor.exe",
        "bin\cursor.cmd"
    )
    foreach ($rootName in @("cursor", "Cursor")) {
        $root = Join-Path $env:LOCALAPPDATA "Programs\$rootName"
        foreach ($rel in $relCandidates) {
            $p = Join-Path $root $rel
            if (Test-Path -LiteralPath $p) {
                return $p
            }
        }
    }
    $procRoot = Get-SetupDevCursorInstallRootFromProcess
    if ($null -ne $procRoot) {
        foreach ($rel in $relCandidates) {
            $p = Join-Path $procRoot $rel
            if (Test-Path -LiteralPath $p) {
                return $p
            }
        }
    }
    return $null
}

function Resolve-SetupDevCursorBundleCodeShimPath {
    <#
    .SYNOPSIS
        Cursor bundles code.cmd next to cursor.cmd; it installs extensions into Cursor, not VS Code.
    #>
    foreach ($rootName in @("cursor", "Cursor")) {
        $shim = Join-Path $env:LOCALAPPDATA "Programs\$rootName\resources\app\bin\code.cmd"
        if (Test-Path -LiteralPath $shim) {
            return $shim
        }
    }
    $fromPath = Get-Command code -ErrorAction SilentlyContinue
    if ($fromPath -and (Test-SetupDevCliPathIsUnderCursorInstall -CliPath $fromPath.Source)) {
        return $fromPath.Source
    }
    return $null
}

function Resolve-SetupDevMicrosoftVsCodeCliPath {
    <#
    .SYNOPSIS
        Full path to Microsoft VS Code's code.cmd when installed in the default per-user location.
    #>
    $official = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin\code.cmd"
    if (Test-Path -LiteralPath $official) {
        return $official
    }
    return $null
}

function Resolve-SetupDevVsCodeInstallCliPath {
    <#
    .SYNOPSIS
        Prefer a code.cmd that is NOT Cursor's bundled shim (installs into real VS Code).
    #>
    $fromPath = Get-Command code -ErrorAction SilentlyContinue
    if ($fromPath) {
        if (-not (Test-SetupDevCliPathIsUnderCursorInstall -CliPath $fromPath.Source)) {
            return $fromPath.Source
        }
    }
    return (Resolve-SetupDevMicrosoftVsCodeCliPath)
}

function Get-SetupDevEditorInstallCli {
    <#
    .SYNOPSIS
        Resolves which executable to use for ` --install-extension` so the collab .vsix lands in
        the editor the developer is actually using (Cursor vs VS Code).
    .NOTES
        - VS Code's installer often puts `code` on PATH; Cursor frequently does not put `cursor` on PATH
          even though cursor.cmd exists under %LocalAppData%\Programs\cursor\resources\app\bin\.
        - We resolve those paths automatically so "Install shell command" is not required.
        - Cursor's bundle also ships code.cmd (under the Cursor install dir); that targets Cursor,
          not Microsoft VS Code  - we use it when the Cursor launcher cannot be found.
    #>
    $inCursor = Test-SetupDevCursorHost
    $cursorCli = Resolve-SetupDevCursorCliPath
    $cursorCodeShim = Resolve-SetupDevCursorBundleCodeShimPath
    $vsCodeCli = Resolve-SetupDevVsCodeInstallCliPath

    if ($inCursor) {
        if ($null -ne $cursorCli) {
            return [PSCustomObject][ordered]@{
                Exe           = $cursorCli
                DisplayLabel  = "Cursor"
                SkipInstall   = $false
                SkipReason    = $null
            }
        }
        if ($null -ne $cursorCodeShim) {
            return [PSCustomObject][ordered]@{
                Exe           = $cursorCodeShim
                DisplayLabel  = "Cursor (code shim)"
                SkipInstall   = $false
                SkipReason    = $null
            }
        }
        if ($null -ne $vsCodeCli) {
            return [PSCustomObject][ordered]@{
                Exe           = $null
                DisplayLabel  = $null
                SkipInstall   = $true
                SkipReason    = "Cursor host detected but Cursor install path could not be found; " `
                    + "refusing Microsoft VS Code's code.cmd so the extension is not installed into the wrong app."
            }
        }
        return [PSCustomObject][ordered]@{
            Exe           = $null
            DisplayLabel  = $null
            SkipInstall   = $true
            SkipReason    = "Could not locate Cursor or VS Code CLI for extension install."
        }
    }

    if ($null -ne $vsCodeCli) {
        return [PSCustomObject][ordered]@{
            Exe           = $vsCodeCli
            DisplayLabel  = "VS Code"
            SkipInstall   = $false
            SkipReason    = $null
        }
    }
    if ($null -ne $cursorCli) {
        return [PSCustomObject][ordered]@{
            Exe           = $cursorCli
            DisplayLabel  = "Cursor"
            SkipInstall   = $false
            SkipReason    = $null
        }
    }
    $anyCode = Get-Command code -ErrorAction SilentlyContinue
    if ($anyCode) {
        return [PSCustomObject][ordered]@{
            Exe           = $anyCode.Source
            DisplayLabel  = "code (PATH)"
            SkipInstall   = $false
            SkipReason    = $null
        }
    }
    return [PSCustomObject][ordered]@{
        Exe           = $null
        DisplayLabel  = $null
        SkipInstall   = $true
        SkipReason    = "Neither Cursor nor VS Code CLI could be resolved; skipping collab extension auto-install."
    }
}

function Get-SetupDevDetectedIde {
    param([string]$RepoRoot)

    # VS Code family: Cursor, VS Code, Antigravity, Windsurf (vscode-like hosting)
    if ($env:TERM_PROGRAM -eq "vscode") {
        return "vscode"
    }
    if ($null -ne $env:VSCODE_PID -and $env:VSCODE_PID -ne "") {
        return "vscode"
    }
    if ($null -ne $env:VSCODE_CWD -and $env:VSCODE_CWD -ne "") {
        return "vscode"
    }
    if ($null -ne $env:VSCODE_IPC_HOOK -and $env:VSCODE_IPC_HOOK -ne "") {
        return "vscode"
    }
    if ($null -ne $env:VSCODE_IPC_HOOK_CLI -and $env:VSCODE_IPC_HOOK_CLI -ne "") {
        return "vscode"
    }
    if ($null -ne $env:VSCODE_CRASH_REPORTER_PROCESS_TYPE -and $env:VSCODE_CRASH_REPORTER_PROCESS_TYPE -ne "") {
        return "vscode"
    }
    if ($null -ne $env:CURSOR_TRACE_ID -and $env:CURSOR_TRACE_ID -ne "") {
        return "vscode"
    }
    if ($null -ne $env:CURSOR_AGENT -and $env:CURSOR_AGENT -ne "") {
        return "vscode"
    }
    if (Test-SetupDevAncestorProcessMatch -NameWildcards @("Cursor*", "Code.exe", "code.exe")) {
        return "vscode"
    }

    # JetBrains integrated terminal (may be absent in external shells)
    if ($env:TERMINAL_EMULATOR -like "*JetBrains*") {
        return "jetbrains"
    }
    if (Test-SetupDevAncestorProcessMatch -NameWildcards @("pycharm*.exe", "idea*.exe", "WebStorm*.exe", "Rider*.exe", "CLion*.exe", "DataGrip*.exe", "PhpStorm*.exe", "GoLand*.exe", "RubyMine*.exe")) {
        return "jetbrains"
    }

    # Directory hints (weaker): .idea may exist while the dev uses Cursor
    if (Test-Path (Join-Path $RepoRoot ".vscode")) {
        return "vscode"
    }
    if (Test-Path (Join-Path $RepoRoot ".cursor")) {
        return "vscode"
    }
    if (Test-Path (Join-Path $RepoRoot ".idea")) {
        return "jetbrains"
    }

    return $null
}

function Invoke-SetupDevCollabLocksVsixInstall {
    <#
    .SYNOPSIS
        Downloads collab-file-locks .vsix from KirilMT/collab GitHub Releases and installs it
        using the editor CLI resolved by Get-SetupDevEditorInstallCli (Cursor vs VS Code paths).
    #>
    $editorCli = Get-SetupDevEditorInstallCli
    if ($editorCli.SkipInstall) {
        Write-Host "     - $($editorCli.SkipReason)" -ForegroundColor Yellow
        Write-Host "     - Manual: download .vsix from" -ForegroundColor Gray
        Write-Host "       https://github.com/KirilMT/collab/releases/latest" -ForegroundColor Gray
        Write-Host "       then: cursor --install-extension <path-to.vsix>   (Cursor)" -ForegroundColor Gray
        Write-Host "       or:  code --install-extension <path-to.vsix>     (VS Code)" -ForegroundColor Gray
        return
    }

    Write-Host "     - Collab extension installer: $($editorCli.DisplayLabel)" -ForegroundColor Gray
    Write-Host "       $($editorCli.Exe)" -ForegroundColor DarkGray
    Write-Host "     - Fetching latest collab-file-locks .vsix from GitHub Releases..." -ForegroundColor Gray
    try {
        $releaseUri = "https://api.github.com/repos/KirilMT/collab/releases/latest"
        # GitHub API requires a User-Agent header
        $releaseInfo = Invoke-RestMethod -Uri $releaseUri `
            -Headers @{ "User-Agent" = "mockCMMS-setup-dev" } `
            -ErrorAction Stop
        $vsixAsset = $releaseInfo.assets | Where-Object { $_.name -like "*.vsix" } | Select-Object -First 1
        if (-not $vsixAsset) {
            Write-Host "     - No .vsix asset found on release $($releaseInfo.tag_name); skipping." -ForegroundColor Yellow
            return
        }

        $vsixDest = Join-Path $env:TEMP $vsixAsset.name
        Write-Host "     - Downloading $($vsixAsset.name) ($($releaseInfo.tag_name))..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $vsixAsset.browser_download_url `
            -OutFile $vsixDest `
            -Headers @{ "User-Agent" = "mockCMMS-setup-dev" } `
            -ErrorAction Stop
        $installExe = $editorCli.Exe
        $installOutput = & $installExe --install-extension $vsixDest --force 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Host "     - $installExe --install-extension failed (non-fatal):" -ForegroundColor Yellow
            Write-Host "       $installOutput" -ForegroundColor Gray
        }
        else {
            Write-Host "     - Installed extension " -NoNewline -ForegroundColor White
            Write-Host "OK" -ForegroundColor Green
            Write-Host "       ($($vsixAsset.name) -> $($editorCli.DisplayLabel))" -ForegroundColor Gray
        }
        Remove-Item $vsixDest -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "     - Could not auto-install extension (non-fatal): $_" -ForegroundColor Yellow
        Write-Host "     - Manual install: https://github.com/KirilMT/collab/releases/latest" -ForegroundColor Gray
    }
}

Write-Host "`n   Detecting IDE environment..." -ForegroundColor Yellow

$detectedIDE = Get-SetupDevDetectedIde -RepoRoot $projectRoot

switch ($detectedIDE) {
    "vscode" {
        Write-Host "     - VS Code / Cursor / Antigravity (or compatible host) detected" -ForegroundColor Gray
        Invoke-SetupDevCollabLocksVsixInstall
    }
    "jetbrains" {
        Write-Host "     - PyCharm/IntelliJ detected" -ForegroundColor Gray
        $ideaPath = Join-Path $projectRoot ".idea"
        $runConfigDir = Join-Path $ideaPath "runConfigurations"
        if (-not (Test-Path $runConfigDir)) {
            New-Item -Path $runConfigDir -ItemType Directory -Force | Out-Null
        }
        Write-Host "     - Create a Run Configuration that executes: collab watch" -ForegroundColor Gray
    }
    default {
        Write-Host "     - No IDE detected (run manually: collab daemon-start)" -ForegroundColor Gray
    }
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


# Display next steps - IDE-aware
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                        NEXT STEPS                              " -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

switch ($detectedIDE) {
    "vscode" {
        Write-Host "  1. Collab Locks extension:" -ForegroundColor White
        Write-Host "     Auto-installed above from KirilMT/collab GitHub Releases (into Cursor or VS Code," -ForegroundColor Magenta
        Write-Host "     whichever CLI setup-dev used: cursor vs code)." -ForegroundColor Magenta
        Write-Host "     If auto-install was skipped, download .vsix from:" -ForegroundColor Gray
        Write-Host "       https://github.com/KirilMT/collab/releases/latest" -ForegroundColor Gray
        Write-Host "     Then install: cursor --install-extension <path> (Cursor) or" -ForegroundColor Gray
        Write-Host "                  code --install-extension <path> (VS Code)." -ForegroundColor Gray
        Write-Host "     The extension auto-starts on open and shows lock status" -ForegroundColor Gray
        Write-Host "     in the status bar." -ForegroundColor Gray
    }
    "jetbrains" {
        Write-Host "  1. Start the Collab Lock Watcher in PyCharm:" -ForegroundColor White
        Write-Host "     Create a Run Configuration for 'collab watch' and run it" -ForegroundColor Magenta
        Write-Host "     The watcher runs in the Run tool window (background tab)." -ForegroundColor Gray
    }
    default {
        Write-Host "  1. Start the lock watcher manually:" -ForegroundColor White
        Write-Host "     collab daemon-start" -ForegroundColor Magenta
    }
}

Write-Host ""
Write-Host "  2. Activate the virtual environment (if not already active):" -ForegroundColor White
Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Magenta
Write-Host ""
Write-Host "  3. Run the application:" -ForegroundColor White
Write-Host "     python run.py" -ForegroundColor Magenta
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
