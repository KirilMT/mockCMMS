<!-- See AGENTS.md for all shared context (stack, conventions, testing, boundaries, agent behavior). -->
<!-- This file contains ONLY Claude Code / Claude-specific additions. -->

# Claude Code — Tool-Specific Instructions

> **Primary reference:** [AGENTS.md](./AGENTS.md) — read it first.

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
