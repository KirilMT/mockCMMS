# Planning App Bug Tracking Document

_Created: December 10, 2025_
_Last Updated: December 10, 2025_

---

## 📋 DOCUMENT PURPOSE

This document tracks all identified bugs in the **Planning App** (`apps/planning`). Each bug includes:

- **Description**: What the bug is and how it manifests
- **Priority**: Critical, High, Medium, or Low
- **Status**: Open, In Progress, or Fixed
- **Affected Files**: Files that need to be modified

> [!NOTE]
> For main mockCMMS bugs, see `docs/bug_tracking.md`.

---

## 🤖 AI AGENT INSTRUCTIONS

> [!NOTE]
> **For detailed AI workflow rules**, see `AGENTS.md` Section 1.10 (Bug Tracking & Discovery).

### Status Definitions

| Icon     | Status      | Meaning                           |
| -------- | ----------- | --------------------------------- |
| (none)   | Open        | Bug identified, not yet addressed |
| 🔄       | In Progress | Currently being worked on         |
| ✅ FIXED | Fixed       | Code applied, user confirmed      |

### Resolved Bug Simplification Rule

> [!IMPORTANT]
> After a bug is marked **RESOLVED for 5+ days**, simplify its entry:
>
> 1. **Keep:** Status, Resolution date, 1-2 sentence summary, Affected files
> 2. **Remove:** Current/Expected Behavior, Possible Solution, Code snippets, Testing scenarios
> 3. **Purpose:** Reduce document size for efficient AI processing

> [!IMPORTANT]
> Always update the **Summary Counts** section when changing bug statuses.

---

## 🐛 OPEN BUGS

### Bug #P1: Dashboard "Due Soon" Count Incorrect

**Priority:** Medium
**Status:** Open
**Source:** Migrated from main app Bug #19 - December 10, 2025

**Description:**
The "Due Soon" counter on the Dashboard includes closed/completed orders, inflating the urgency.

**Expected Behavior:**

- Count should only include Open or In Progress orders
- Completed/Closed orders should be excluded

**Possible Solution:**

1. Update Dashboard query to filter by status
2. Exclude Closed/Completed from "Due Soon" calculation

**Affected Files:**

- `apps/planning/src/routes/` (dashboard route)
- `apps/planning/src/templates/` (dashboard template)

---

## ✅ RESOLVED BUGS

_No resolved bugs yet._

---

## 📊 BUG SUMMARY

> [!NOTE]
> Last updated: December 10, 2025

### Summary Counts

| Category  | Open  | In Progress | Fixed | Total |
| --------- | ----- | ----------- | ----- | ----- |
| Critical  | 0     | 0           | 0     | 0     |
| High      | 0     | 0           | 0     | 0     |
| Medium    | 1     | 0           | 0     | 1     |
| Low       | 0     | 0           | 0     | 0     |
| **Total** | **1** | **0**       | **0** | **1** |

### Open Bugs

- **Medium:** #P1 Dashboard "Due Soon" Count

---

## 📅 MAINTENANCE GUIDELINES

**When a bug is fixed:**

1. Change status to "✅ FIXED" with date
2. Add 1-2 sentence resolution summary
3. List affected files
4. Update summary counts

**After 5+ days resolved:**

1. Simplify entry per "Resolved Bug Simplification Rule"
2. Remove verbose details

**When adding new bugs:**

1. Use next available bug number (`#P2`, `#P3`, etc.)
2. Set priority (Critical, High, Medium, Low)
3. Add to appropriate section
4. Update summary counts

> [!TIP]
> **Numbering Convention:** Planning app bugs use `#P` prefix to distinguish from main app bugs.

---

_This document tracks bugs specific to the Planning App component of mockCMMS._
