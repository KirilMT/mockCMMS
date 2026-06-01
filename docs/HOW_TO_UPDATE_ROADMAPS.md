# How to Update Roadmap Documents

This guide shows **both humans and AI assistants** how to keep the roadmap documents updated as work progresses.

---

## 📁 The Two Files

1. **`advanced-table-fixes-plan.md`** - Detailed task list (temporary, delete when done)
2. **`mockCMMS_roadmap.md`** - High-level roadmap (permanent)

---

## ✅ When You Complete a Task

### Step 1: Update the Detailed Plan (`advanced-table-fixes-plan.md`)

**Mark the checkbox:**

```markdown
- [x] Fix event listener attachment (use input element not button)
```

**Add completion notes:**

```markdown
- [x] Fix event listener attachment (use input element not button)
  - ✅ Completed on November 23, 2025
  - Changed querySelector from 'button' to 'input#globalSearchInput'
  - Tested with rapid typing and special characters
  - No errors in console
```

**Update Progress Tracking section:**

```markdown
**Overall Progress:** 8% (1/13 tasks completed)
**Phase 1:** 20% (1/5 tasks) - In Progress
**Current Focus:** Task 1.2 - Fix Global Search Functionality
```

### Step 2: Update Current Focus

Change the "Current Focus" line to the next task you're working on.

### Step 3: Add Blockers (if any)

If you encounter issues:

```markdown
**Blockers:**

- localStorage not working in private browsing mode
  - Workaround: Use sessionStorage as fallback
```

---

## 🎯 When You Complete a Phase

### Update the Detailed Plan

Change the phase status:

```markdown
**Phase 1:** 100% (5/5 tasks) - ✅ Completed November 25, 2025
**Phase 2:** 0% (0/2 tasks) - In Progress
```

Update the main Status field:

```markdown
**Status:** In Progress - Phase 2 (Validation & UX)
```

### Update the Roadmap (`mockCMMS_roadmap.md`)

Change the status line:

```markdown
**Status:** In Progress - Phase 2 (Validation & UX)
```

The "Updated" date is maintained automatically by `python scripts/format_code.py`
(it stamps any changed roadmap), so you normally do not edit it by hand. The line
looks like this:

```markdown
_Updated <Month D, YYYY>_
```

---

## 🏁 When You Complete the Entire Sprint

### In `advanced-table-fixes-plan.md`

Change the status to Completed:

```markdown
**Status:** ✅ Completed
```

Update Progress Tracking:

```markdown
**Overall Progress:** 100% (13/13 tasks completed)
**Completed:** December 10, 2025
```

### In `mockCMMS_roadmap.md`

**Move from "ACTIVE WORK" to "RECENTLY COMPLETED":**

```markdown
## ✅ RECENTLY COMPLETED

**Sprint:** Advanced Table Component Fixes & Enhancements (17 days)
**Completed:** December 10, 2025
**Summary:** Fixed critical bugs in advanced table component and added new features
**Key Outcomes:**

- AND/OR filter logic working correctly
- Filter persistence across page navigation
- Team column added to Users table
- Global search fixed and optimized
- Save/Load configuration working reliably
  **Plan Archive:** [Advanced Table Fixes Plan](./archived/advanced-table-fixes-plan.md)
```

**Clear or update "ACTIVE WORK" section** for the next sprint.

### Archive the Detailed Plan

Create an `archived/` folder in `docs/` and move the completed plan there, or simply delete it if you prefer.

---

## 🤖 For AI Assistants

**After EVERY implementation of a task:**

1. Open `docs/advanced-table-fixes-plan.md`
2. Find the task you just completed
3. Mark it `[x]` and add notes
4. Update Progress Tracking percentages
5. Update Current Focus
6. Commit with message: `docs: mark task [name] as complete`

**After completing a PHASE:**

1. Update both files as described above
2. Commit with message: `docs: complete Phase X of [sprint name]`

**After completing a SPRINT:**

1. Update both files as described above
2. Archive or delete the detailed plan
3. Commit with message: `docs: complete sprint [name]`

---

## 📝 Quick Reference

| Action        | File                           | What to Update                  |
| ------------- | ------------------------------ | ------------------------------- |
| Task done     | `advanced-table-fixes-plan.md` | Checkbox, notes, progress %     |
| Phase done    | Both files                     | Phase status, current phase     |
| Sprint done   | Both files                     | Move to completed, archive plan |
| Blocker found | `advanced-table-fixes-plan.md` | Add to Blockers section         |
| Decision made | `advanced-table-fixes-plan.md` | Add note under relevant task    |

---

## Example: Complete Workflow

### Starting Task 1.1

```markdown
**Current Focus:** Task 1.1 - Fix Save/Load Configuration System
```

### After 3 subtasks done

```markdown
#### Task 1.1: Fix Save/Load Configuration System

- [x] Add `this.savedConfigs` instance variable
  - ✅ Completed Nov 23, 2025
  - Added to constructor in advanced-table.js line 15
- [x] Create `populateConfigDropdown()` helper method
  - ✅ Completed Nov 23, 2025
  - Created at line 580, called after render()
- [x] Call repopulation after every render
  - ✅ Completed Nov 23, 2025
  - Added to render() method at line 65
- [ ] Add dropdown change event listener in `attachEventListeners()`
- [ ] Store dropdown value before render, restore after
- [ ] Add toast notification component
- [ ] Add error handling with user feedback
- [ ] Test: Save config → Filter → Check dropdown still populated

**Progress:** 3/8 subtasks complete (38%)
```

### After entire task done

```markdown
- [x] Task 1.1: Fix Save/Load Configuration System ✅ Nov 24, 2025
  - All 8 subtasks completed
  - Dropdown now persists correctly after filters
  - Added toast notifications for save/load feedback
  - All tests passing

**Overall Progress:** 8% (1/13 tasks completed)
**Current Focus:** Task 1.2 - Fix Global Search Functionality
```

---

**Remember:** Keep these files updated as you go! They're your source of truth for project progress.

_Updated June 1, 2026_
