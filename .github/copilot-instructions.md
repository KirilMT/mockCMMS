<!-- See AGENTS.md (repo root) for all shared context (stack, conventions, testing, boundaries, agent behavior). -->
<!-- This file contains ONLY GitHub Copilot-specific additions. -->

# GitHub Copilot — Tool-Specific Instructions

> **Primary reference:** [AGENTS.md](../AGENTS.md) — read it first.

---

## CRITICAL ENVIRONMENT RULE - SHELL COMPATIBILITY (Permanent)

Never assume the shell. Detect the active terminal shell first, then use only shell-native syntax for all commands.

Mandatory behavior:

1. At the beginning of every new session, run environment detection for the current shell.
2. After detection, use only commands compatible with that shell.
3. Do not mix shell syntaxes in a single command.
4. If complex logic is needed, write a shell-native script (`.ps1` for PowerShell, `.sh` for bash/zsh).
5. This rule has highest priority.

PowerShell patterns:

```powershell
Write-Host "=== ENVIRONMENT DETECTION ===" -ForegroundColor Green
$PSVersionTable
Get-Command git
Get-Content <file> -TotalCount 300
Get-Content <file> -Tail 50
(Get-Content <file> | Measure-Object -Line).Lines
Get-Content <file> | Select-String -Pattern "..."
```

Bash/zsh patterns:

```bash
echo "=== ENVIRONMENT DETECTION ==="
echo "$SHELL"
git --version
head -n 300 <file>
tail -n 50 <file>
wc -l <file>
grep -n "..." <file>
```

Before outputting any terminal command, internally verify it is compatible with the detected shell (or is plain `git`). If unsure, run detection again and use shell-native file-reading/search patterns.

---

## File Locking

Before editing any file, follow Skill: `file-locking`:

1. List all files the task will touch.
2. Run `collab active` to check current locks. Optional targeted check: `collab status <file>`.
   Dev workflows may also show watcher/IDE popup warnings, but AI agents do not see those popups and must rely on explicit lock commands.
3. If any target file is locked by another developer — **stop and report**. Do not edit.
4. If files are unlocked, proceed with edits — lock acquisition/release is automatic.
5. **ABSOLUTELY FORBIDDEN:** never force-release another developer's lock.

---

## Tool Limitations

GitHub Copilot does **not** have access to:

- Browser automation tools (`browser_subagent`)
- Terminal command execution in all IDEs

**Implications:**

- Provide clear manual testing instructions instead of automated browser verification.
- Include step-by-step verification steps in PR descriptions.

---

## Verification Workflow (Manual)

Since Copilot cannot run browser tests automatically:

1. **Identify test plan** — check `docs/` for relevant `*_test_plan.md` files.
2. **Provide instructions** — give the user clear steps to verify changes manually.
3. **Create test checklist** — if no test plan exists, add a concise checklist to the PR description.
4. **Wait for confirmation** — do not mark a task complete until the user confirms verification.

---

## Task Completion

- Always run `python scripts/format_code.py` then `python scripts/validate_code.py` before finishing (if terminal access is available).
- Follow conventional commits: `type(scope): description`.
- See Skill: `commit-workflow` for the full commit procedure.
