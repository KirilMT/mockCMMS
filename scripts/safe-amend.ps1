param(
    [ValidateSet('amend', 'cleanup')]
    [string]$Command = 'amend',

    # Amend parameters
    [switch]$NoEdit,
    [string]$Author,
    [switch]$SkipPreCommit,
    [switch]$KeepStash,
    [switch]$DryRun,

    # Cleanup parameters
    [switch]$All,
    [string]$Stash,
    [switch]$Force,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommitArgs
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$IgnoreExitCode
    )

    & git @Arguments
    $exitCode = $LASTEXITCODE

    if (-not $IgnoreExitCode -and $exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode"
    }

    return $exitCode
}

function Test-HasUnstagedChanges {
    $porcelain = git status --porcelain
    foreach ($line in $porcelain) {
        if ($line.Length -lt 2) {
            continue
        }

        if ($line[0] -eq '?' -and $line[1] -eq '?') {
            continue
        }

        # Porcelain XY format: Y != ' ' means unstaged tracked changes are present.
        if ($line[1] -ne ' ') {
            return $true
        }
    }

    return $false
}

function Test-HasMixedIndexAndWorktreeChanges {
    $porcelain = git status --porcelain
    $mixedFiles = @()

    foreach ($line in $porcelain) {
        if ($line.Length -lt 4) {
            continue
        }

        if ($line[0] -eq '?' -and $line[1] -eq '?') {
            continue
        }

        $x = $line[0]
        $y = $line[1]
        if ($x -ne ' ' -and $y -ne ' ') {
            $mixedFiles += $line.Substring(3)
        }
    }

    return $mixedFiles
}

function Get-SafeAmendStashes {
    $allStashes = & git stash list
    $safeAmendStashes = @()

    foreach ($line in $allStashes) {
        if ($line -match "safe-amend-\d{8}-\d{6}") {
            $safeAmendStashes += @{
                Ref   = ($line -split ":")[0]
                Full  = $line
                Date  = ([regex]::Match($line, 'safe-amend-(\d{8})-(\d{6})').Groups[1].Value)
                Time  = ([regex]::Match($line, 'safe-amend-(\d{8})-(\d{6})').Groups[2].Value)
            }
        }
    }

    return $safeAmendStashes
}

function Invoke-SafeDrop {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StashRef,
        [switch]$Dry
    )

    if ($Dry) {
        Write-Host "   [DRY RUN] Would drop: $StashRef" -ForegroundColor DarkYellow
    }
    else {
        & git stash drop $StashRef 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ Dropped: $StashRef" -ForegroundColor Green
        }
        else {
            Write-Host "   ✗ Failed to drop: $StashRef" -ForegroundColor Red
            return $false
        }
    }

    return $true
}

Write-Host "`n=== Safe Amend Workflow ===" -ForegroundColor Cyan

# Guard: Only run amend logic for the 'amend' command
if ($Command -eq 'amend') {

Invoke-Git -Arguments @("rev-parse", "--is-inside-work-tree") | Out-Null

Write-Host "[1/6] Repository state" -ForegroundColor Yellow
Invoke-Git -Arguments @("status", "--branch", "--short")

$stashRef = $null
$stashTag = "safe-amend-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$hasUnstagedChanges = Test-HasUnstagedChanges
$mixedFiles = Test-HasMixedIndexAndWorktreeChanges
$useIndexRestore = $true

if ($mixedFiles.Count -gt 0) {
    $useIndexRestore = $false
    Write-Host "   Mixed staged+unstaged files detected. Using non-index stash restore mode:" -ForegroundColor DarkYellow
    foreach ($file in $mixedFiles) {
        Write-Host "     - $file" -ForegroundColor DarkYellow
    }
}

if ($hasUnstagedChanges) {
    Write-Host "[2/6] Unstaged changes found - stashing with --keep-index" -ForegroundColor Yellow
    Invoke-Git -Arguments @("stash", "push", "--keep-index", "-m", $stashTag)

    $stashLine = git stash list | Select-String -Pattern $stashTag | Select-Object -First 1
    if (-not $stashLine) {
        throw "Stash was created but could not be identified. Aborting to avoid data loss."
    }

    $stashRef = ($stashLine.Line -split ":")[0]

    Write-Host "[3/6] Stash captured: $stashRef" -ForegroundColor Yellow
    Invoke-Git -Arguments @("stash", "show", "--name-status", $stashRef)
}
else {
    Write-Host "[2/6] No unstaged changes detected" -ForegroundColor Green
}

$originalError = $null

try {
    if (-not $SkipPreCommit -and (Get-Command pre-commit -ErrorAction SilentlyContinue)) {
        Write-Host "[4/6] Running pre-commit (auto-fix aware)" -ForegroundColor Yellow

        $preCommitPassed = $false
        for ($attempt = 1; $attempt -le 2; $attempt++) {
            & pre-commit run
            $preCommitExit = $LASTEXITCODE

            if ($preCommitExit -eq 0) {
                $preCommitPassed = $true
                break
            }

            if ($attempt -eq 1) {
                Write-Host "   pre-commit modified files. Re-staging and retrying once..." -ForegroundColor DarkYellow
                Invoke-Git -Arguments @("add", "-A")
            }
        }

        if (-not $preCommitPassed) {
            throw "pre-commit failed after 2 attempts"
        }
    }
    elseif ($SkipPreCommit) {
        Write-Host "[4/6] Skipping pre-commit (requested)" -ForegroundColor DarkYellow
    }
    else {
        Write-Host "[4/6] pre-commit not available - continuing" -ForegroundColor DarkYellow
    }

    Write-Host "[5/6] Running git commit --amend" -ForegroundColor Yellow

    # --no-verify: pre-commit was already run manually in step [4/6].
    # Running hooks again via git would cause redundant execution and
    # stash conflicts when hooks modify files.
    $finalCommitArgs = @("commit", "--amend", "--no-verify")

    if ($NoEdit) {
        $finalCommitArgs += "--no-edit"
    }
    elseif (-not $CommitArgs -or $CommitArgs.Count -eq 0) {
        # Default to non-interactive amend to make automation deterministic.
        $finalCommitArgs += "--no-edit"
    }

    if ($Author) {
        $finalCommitArgs += "--author=$Author"
    }

    if ($CommitArgs) {
        $finalCommitArgs += $CommitArgs
    }

    if ($DryRun) {
        Write-Host "Dry run enabled - skipping amend command:" -ForegroundColor DarkYellow
        Write-Host "git $($finalCommitArgs -join ' ')" -ForegroundColor Gray
    }
    else {
        Invoke-Git -Arguments $finalCommitArgs
    }
}
catch {
    $originalError = $_
}
finally {
    if ($stashRef) {
        if ($useIndexRestore) {
            Write-Host "[6/6] Restoring stashed work with apply --index" -ForegroundColor Yellow
            & git stash apply --index $stashRef
        }
        else {
            Write-Host "[6/6] Restoring stashed work with apply (non-index mode)" -ForegroundColor Yellow
            & git stash apply $stashRef
        }

        $applyExit = $LASTEXITCODE

        if ($applyExit -ne 0) {
            Write-Host "Stash restore failed. Your work is still safe in $stashRef." -ForegroundColor Red
            if ($useIndexRestore) {
                Write-Host "Resolve conflicts, then re-run: git stash apply --index `"$stashRef`"" -ForegroundColor Red
            }
            else {
                Write-Host "Resolve conflicts, then re-run: git stash apply `"$stashRef`"" -ForegroundColor Red
            }
            if ($null -eq $originalError) {
                throw "Failed to restore stash $stashRef"
            }
        }
        elseif (-not $KeepStash) {
            Invoke-Git -Arguments @("stash", "drop", $stashRef)
            Write-Host "Stash restored and dropped: $stashRef" -ForegroundColor Green
        }
        else {
            Write-Host "Stash restored and kept: $stashRef" -ForegroundColor Green
        }
    }
}

if ($null -ne $originalError) {
    throw $originalError
}

Write-Host "Safe amend completed successfully." -ForegroundColor Green

} # end if ($Command -eq 'amend')

# ============================================================================
# CLEANUP COMMAND
# ============================================================================
function Invoke-Cleanup {
    Write-Host "`n=== Safe Amend Stash Cleanup ===" -ForegroundColor Cyan
    Write-Host ""

    $safeAmendStashes = Get-SafeAmendStashes

    if ($safeAmendStashes.Count -eq 0) {
        Write-Host "No safe-amend stashes found." -ForegroundColor Green
        Write-Host ""
        return
    }

    Write-Host "Found $($safeAmendStashes.Count) safe-amend stash(es):" -ForegroundColor Yellow
    Write-Host ""

    $toDelete = @()

    foreach ($stash in $safeAmendStashes) {
        $dateTime = "$($stash.Date) $($stash.Time)"
        Write-Host "  $($stash.Ref)" -ForegroundColor Magenta
        Write-Host "    Created: $dateTime" -ForegroundColor Gray
        Write-Host "    Full: $($stash.Full)" -ForegroundColor Gray
        Write-Host ""

        if ($All -or -not $Stash) {
            $toDelete += $stash
        }
        elseif ($Stash -eq $stash.Ref) {
            $toDelete += $stash
        }
    }

    if ($toDelete.Count -eq 0) {
        if ($Stash) {
            Write-Host "No matching stash: $Stash" -ForegroundColor Red
            Write-Host ""
            exit 1
        }
        else {
            Write-Host "No action specified (use -All to clean all, or -Stash <ref>)" -ForegroundColor Yellow
            Write-Host ""
            return
        }
    }

    Write-Host "Ready to delete: $($toDelete.Count) stash(es)" -ForegroundColor Yellow
    Write-Host ""

    if (-not $Force -and -not $DryRun) {
        Write-Host "Confirm deletion (y/n)? " -ForegroundColor Cyan -NoNewline
        $confirm = Read-Host

        if ($confirm -ne 'y' -and $confirm -ne 'Y') {
            Write-Host "Cancelled." -ForegroundColor Gray
            Write-Host ""
            return
        }
    }

    Write-Host ""
    $dropped = 0

    foreach ($stash in $toDelete) {
        if (Invoke-SafeDrop -StashRef $stash.Ref -Dry:$DryRun) {
            $dropped++
        }
    }

    Write-Host ""

    if ($DryRun) {
        Write-Host "[DRY RUN] Would delete $dropped/$($toDelete.Count) stash(es)" -ForegroundColor DarkYellow
    }
    else {
        Write-Host "Deleted $dropped/$($toDelete.Count) stash(es)" -ForegroundColor Green
    }

    Write-Host ""
}

# ============================================================================
# COMMAND DISPATCH
# ============================================================================
switch ($Command) {
    'amend' {
        # Main amend logic is executed above (no action needed here)
    }
    'cleanup' {
        Invoke-Cleanup
    }
    default {
        throw "Unknown command: $Command"
    }
}
