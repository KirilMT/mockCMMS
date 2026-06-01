---
name: skills-maintenance
description: Use when a task reveals a gap or wrong guidance in a skill, a new tool/library is added, a repeated agent mistake shows a missing rule, or the user asks to create, update, or audit skills. Keeps the .agents/skills library accurate and synchronized with the codebase. Trigger proactively.
---

# Skills Maintenance Workflow

## Use this skill when

- A task revealed a gap, stale path, or incorrect guidance in an existing skill
- A new tool, library, or convention was introduced to the repo
- A repeated mistake shows a rule is missing
- The user asks to create, update, or audit skills
- A successful, reusable approach should be preserved for future agents

## Do not use this skill when

- You are following an existing skill as-is (just use it)
- The change is a one-off and not worth encoding as durable guidance

---

## Purpose

Keep `.agents/skills/` accurate, current, and synchronized with the codebase and with `AGENTS.md`. A stale or wrong skill is worse than none — it makes agents repeat mistakes confidently.

> **Avoid duplication.** Global, cross-skill behaviour (research-first, no-bypass, no-new-files, autonomy, file-locking, shell-compatibility) lives **once** in `AGENTS.md` → "Agent Behavior Rules" (and the `shell-compatibility` / `file-locking` skills). Skills must **reference** those rules, never restate them.

---

## Step 1 — Decide: update existing vs. create new

**Default: update an existing skill.** A new skill has a cost — agents must know when to trigger it. Create one only when all of these hold:

- The content is a complete, self-contained workflow with a distinct trigger
- It does not fit any existing skill's scope
- It would otherwise bloat an existing skill past readability

Before creating a new skill, confirm:

- [ ] The content is not a global rule that belongs in `AGENTS.md`
- [ ] It cannot be a new section in an existing skill
- [ ] It does not duplicate guidance already in another skill or `AGENTS.md`
- [ ] It will be registered in the Skills table in `AGENTS.md`

---

## Step 2 — Place the content in the right location

| Content type                           | Where it belongs                        |
| -------------------------------------- | --------------------------------------- |
| Universal agent behaviour rule         | `AGENTS.md` → "Agent Behavior Rules"    |
| Shell / terminal command usage         | Skill: `shell-compatibility`            |
| File locking before edits              | Skill: `file-locking`                   |
| Finding files / repo navigation        | Skill: `repo-navigation`                |
| Test writing / coverage / validation   | Skill: `testing-workflow`               |
| Git staging / commit / push procedure  | Skill: `commit-workflow`                |
| Bug discovery / fix lifecycle          | Skill: `bug-tracking`                   |
| New feature or modular app scaffolding | Skill: `new-feature`                    |
| Skills library maintenance             | Skill: `skills-maintenance` (this file) |
| Claude-specific behaviour              | `CLAUDE.md`                             |
| GitHub Copilot-specific behaviour      | `.github/copilot-instructions.md`       |

---

## Step 3 — Draft the change (style rules)

- Imperative voice: "Run X before Y", not "You should run X".
- Tables for decision logic; fenced code blocks for exact commands.
- One atomic rule per bullet.
- Use `ALWAYS` / `NEVER` / `MANDATORY` for hard constraints; avoid vague words ("usually", "might", "consider") for rules that must always apply.
- Cross-reference instead of copying: link to the owning skill or `AGENTS.md` section.

---

## Step 4 — Check for conflicts and duplication

Before finalizing, verify the change:

- Does not contradict `AGENTS.md` or the same skill
- Does not duplicate a rule already stated elsewhere (if it does, reference the source instead)
- Does not require matching updates in other skills (if it does, make them in the same change)

---

## Step 5 — Propose before committing

**NEVER silently rewrite a skill.** Always:

1. Show the user the exact change (old → new).
2. Explain what gap or failure triggered it.
3. Wait for confirmation before committing.

Commit skill/docs changes separately from feature or fix work, following Skill: `commit-workflow` (e.g. `docs(agents): update <skill> — <reason>`).

---

## Step 6 — Register a new skill

If a new skill was created:

- [ ] Add a row to the Skills table in `AGENTS.md`
- [ ] Write a trigger description specific enough to fire reliably

---

## Audit checklist (run periodically or when asked)

For each skill in `.agents/skills/`:

- [ ] Does it still match how the repo actually works?
- [ ] Are all referenced file paths and commands still valid (check `pyproject.toml`, `package.json`)?
- [ ] Does it reference any removed tool or library?
- [ ] Does it contradict or duplicate `AGENTS.md` or another skill?
- [ ] Is it missing coverage for a known, recurring pain point?
- [ ] Is the `description` specific enough to trigger reliably?

---

## Safety

- **NEVER** modify a skill to retroactively justify a past mistake — update skills to prevent future ones.
- **NEVER** delete skill content without user approval; mark it deprecated with a note instead.
- Treat skill files with the same care as `AGENTS.md` — they govern agent behaviour across all future sessions.

_Updated June 1, 2026_
