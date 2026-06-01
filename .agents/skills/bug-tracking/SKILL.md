---
name: bug-tracking
description: Use when discovering, reporting, or fixing bugs. Covers the full bug lifecycle from discovery to user-confirmed resolution.
---

# Bug Tracking Workflow

## Use this skill when

- You discover a potential bug during browsing or testing
- You are fixing a reported bug
- You need to update bug tracking documentation

## Do not use this skill when

- Writing new features (see Skill: `new-feature`)
- Working on test failures that aren't bugs (see Skill: `testing-workflow`)

---

## Bug Discovery Protocol

When you observe unexpected behavior:

1. **DO NOT** add it to any bug tracking document immediately.
2. **ASK the user first** — describe what you observed:
   - What action you were performing
   - What you expected to happen
   - What actually happened
   - Screenshot/evidence if available
3. **WAIT** for user confirmation before adding to bug tracking.
4. **Assign priority** with user input.

> ⚠️ Adding bugs without user confirmation leads to document pollution.

## Issue Severity Categorization

When reporting issues, categorize by severity:

| Severity        | Criteria                                                                           | Action                     |
| --------------- | ---------------------------------------------------------------------------------- | -------------------------- |
| 🔴 **Critical** | Security vulnerabilities, data loss, app crashes, type errors                      | Fix immediately            |
| 🟡 **High**     | Code duplicates >10 lines, coverage <70% for critical paths, broken user workflows | Fix this sprint            |
| 🟠 **Medium**   | Style violations, medium complexity (radon CC 10-15), missing docstrings           | Fix when touching the file |
| 🟢 **Low**      | Minor style issues, low complexity improvements, cosmetic concerns                 | Technical debt backlog     |

## Bug Fix Workflow

1. **Verify** the bug exists — reproduce it (browser test, API call, etc.)
2. **Apply fix** — make code changes
3. **Verify fix** — use browser automation or tests to confirm
4. **Update documentation** — mark as "Fixed" with resolution notes
5. **Notify user** — request confirmation before marking "Resolved"

## Status Transitions

| From        | To          | Trigger                                     |
| ----------- | ----------- | ------------------------------------------- |
| Open        | In Progress | You start working on the bug                |
| In Progress | Fixed       | Code applied, automated verification passed |
| Fixed       | ✅ Resolved | **User confirms** fix works                 |

**NEVER** mark a bug as "Resolved" without explicit user confirmation.
"Fixed" = code is applied. "Resolved" = user verified.

## Documentation Rules

### File Locations (Modular Structure)

| Scope              | File                                            |
| ------------------ | ----------------------------------------------- |
| Core CMMS bugs     | `docs/bug_tracking.md`                          |
| Planning app bugs  | `apps/planning/docs/planning_bug_tracking.md`   |
| Reporting app bugs | `apps/reporting/docs/reporting_bug_tracking.md` |

### Update Rules

- **ALWAYS** update summary counts when changing bug statuses.
- **NEVER** create duplicate bug IDs — search the document first.
- **NEVER** add app-specific bugs to `docs/bug_tracking.md` — use the app's own tracker.
- If referencing an app bug in core docs, use a **link**, not a duplicate entry.

## Safety

- Always reproduce the bug before fixing — don't fix phantom issues.
- Don't modify test configurations to hide bugs.
- If a visual test fails, investigate the code — don't update screenshots.

_Updated June 1, 2026_
