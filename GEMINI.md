<!-- See AGENTS.md for all shared context (stack, conventions, testing, boundaries, agent behavior). -->
<!-- This file contains ONLY Antigravity IDE and Gemini-specific additions. -->

# Gemini / Antigravity IDE — Tool-Specific Instructions

> **Primary reference:** [AGENTS.md](./AGENTS.md) — read it first.

---

## Autonomous Execution (Antigravity-Specific)

### SafeToAutoRun Authorization

All standard operations MUST use `SafeToAutoRun=true`:

| Category       | Commands                                                                              |
| -------------- | ------------------------------------------------------------------------------------- |
| **Python**     | `python`, `pytest`, `pip`, `ruff`, `black`, `isort`, `mypy`, `docformatter`, `bandit` |
| **Node.js**    | `npm`, `npx`, `node`, `prettier`, `eslint`, `jest`, `playwright`                      |
| **Shell**      | `Get-Content`, `Select-String`, `Remove-Item`, `Copy-Item`, `findstr`, `dir`          |
| **Git (read)** | `git status`, `git diff`, `git log`, `git branch`, `git show`                         |
| **Complex**    | Pipes (`\|`), redirections (`>`), chaining (`;`) — all auto-run                       |

**Only `git commit` and `git push` require user approval.**

### Background Command Monitoring

For long-running commands, monitor until completion — never prompt "still running?":

| Command                    | Expected Duration |
| -------------------------- | ----------------- |
| `validate_code.py --quick` | ~5 min            |
| `validate_code.py` (full)  | ~15-20 min        |
| `pytest tests/backend`     | ~5 min            |
| `npm run test:e2e`         | ~5 min            |

Use `command_status` with `WaitDurationSeconds=300` and keep polling until DONE.

---

## Browser Verification (Antigravity-Specific)

When verifying UI changes:

1. **Check server** — verify `python run.py` is running before using `browser_subagent`.
2. **Use `browser_subagent`** to demonstrate ALL implemented/changed features.
3. **Login:** `admin` / `admin123`
4. **Evidence accuracy** — describe ONLY what's visible in screenshots. Trust the screenshot over assumptions. Zero tolerance for hallucination.

---

## Artifact Management

- **One artifact per type per task:** ONE implementation plan, ONE task list, ONE walkthrough.
- **Update, don't recreate** — always update existing artifacts.
- **Never delete completed work** in artifacts.
- Use `task.md`, `implementation_plan.md`, `walkthrough.md` naming.

---

## Debug Log Rules

- Location: `logs/` directory (create if missing).
- Extension: `.log` only.
- Naming: `debug_<context>_<timestamp>.log`
- **Cleanup:** Delete log files after reading content.
