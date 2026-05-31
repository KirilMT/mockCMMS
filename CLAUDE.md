<!-- See AGENTS.md for all shared context (stack, conventions, testing, boundaries, agent behavior). -->
<!-- This file contains ONLY Claude Code / Claude-specific additions. -->

# Claude Code — Tool-Specific Instructions

> **Primary reference:** [AGENTS.md](./AGENTS.md) — read it first.

---

## File Locking

Before editing any file, follow Skill: `file-locking`:

1. List all files the task will touch.
2. Run lock checks before edits. When the venv is not activated, use `.\.venv\Scripts\collab.exe active` (Windows) or `.venv/bin/collab active` (POSIX). Optional: `collab status <file>` with the same executable. Dev workflows may show watcher/IDE popups; AI agents must use explicit commands (see AGENTS.md).
3. If any target file is locked by another developer — **stop and report**. Do not edit.
4. If files are unlocked, proceed with edits — lock acquisition/release is automatic.
5. **ABSOLUTELY FORBIDDEN:** never force-release another developer's lock.

---

## Autonomous Execution

- Auto-run all standard operations: python, pytest, npm, ruff, black, isort, mypy, prettier, eslint.
- Auto-run commands with pipes, redirections, and chaining.
- Only `git commit` and `git push` require user approval.
- Never pause for "Should I proceed?" during lint/format/test loops.

---

## Browser Verification

When verifying UI changes:

1. Check that `python run.py` is running before browser actions.
2. Use browser tools to demonstrate ALL implemented/changed features.
3. **Login:** `admin` / `admin123`
4. Describe ONLY what's visible in screenshots — no assumptions.

---

## Task Completion

- Operate autonomously until work is done — pause only at `git commit`.
- Always run `python scripts/format_code.py` then `python scripts/validate_code.py` before finishing.
- If validation fails, self-correct up to 3 attempts before reporting.
