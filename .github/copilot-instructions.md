<!-- See AGENTS.md (repo root) for all shared context (stack, conventions, testing, boundaries, agent behavior). -->
<!-- This file contains ONLY GitHub Copilot-specific additions. -->

# GitHub Copilot — Tool-Specific Instructions

> **Primary reference:** [AGENTS.md](../AGENTS.md) — read it first.

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
