---
name: file-locking
description: Use BEFORE any file modification. Check locks, edit safely with automatic lock handling, and never force-release others' locks.
---

# File Locking Workflow

## Use this skill when

- You are about to edit one or more files for any reason (bug, feature, refactor, docs)
- You need to check whether a file is currently locked by another developer
- You are about to run commands that modify files (for example `python scripts/format_code.py`, codemods, or bulk refactors)

## Do not use this skill when

- You are only reading files (status checks, searches, reviews)
- You are running tests or validation that do not modify files

---

## Why This Matters

This repository uses an installed **collab** file-locking runtime to prevent merge conflicts when multiple developers or AI agents work simultaneously. Editing a file that another developer has locked will cause conflicts.

**Rule: Never edit a file without verifying it is either unlocked or already locked by the current developer (the dev using this AI agent).**

---

## Step 1: Identify All Files to Change

Before touching anything, enumerate the **complete list of files** the task requires. Do this upfront — discovering mid-task that a file is locked wastes effort.

For a typical feature/bug task, this includes:

- Source files to edit
- Test files to create or update
- Documentation files to update
- Config files to modify

---

## Step 2: Check Lock Status

For AI agents, lock checks are mandatory before any file-modifying action. Dev workflows may also show watcher/IDE conflict notifications, but AI agents do not see those popups and must rely on explicit commands.

**Agent shells often do not activate `.venv`.** Do not assume `collab` is on `PATH`. Use the project venv executable:

```powershell
# Windows (mockCMMS default)
.\.venv\Scripts\collab.exe active
.\.venv\Scripts\collab.exe status path/to/file.py
```

```bash
# macOS/Linux (after setup-dev or manual venv)
.venv/bin/collab active
.venv/bin/collab status path/to/file.py
```

If the venv is already activated, `collab active` and `collab status <file>` are equivalent.

Cross-reference the active lock list against your planned file list.

---

## Step 3: Decision Gate

For each file in your list:

| Lock state | Owner                 | Action                                                                  |
| ---------- | --------------------- | ----------------------------------------------------------------------- |
| Unlocked   | —                     | Proceed with edits (lock is acquired automatically when editing starts) |
| Locked     | **Current developer** | Proceed — already owned by the active dev                               |
| Locked     | **Another developer** | **STOP** — see below                                                    |

### If a file is locked by another developer

**Do not edit the file.** Instead:

1. Report to the user exactly which files are locked and by whom:
   ```
   ⛔ Cannot proceed — the following files are locked by another developer:
     - src/routes/api.py  →  locked by @alice (reason: "Fixing auth bug")
     - src/services/db_utils.py  →  locked by @alice
   ```
2. Ask the user whether to:
   - **Wait** and retry later
   - **Contact** the lock owner to coordinate
   - **Proceed with a reduced scope** (only edit unlocked files, if the task allows it)
3. **ABSOLUTE AI RULE:** force-releasing another developer's lock is forbidden.

---

## Step 4: Edit Files

Make your changes. In normal workflows, lock acquisition and release are automatic while editing and after cleanup/sync.

---

## Quick Reference

```powershell
# Windows — list everything currently locked (preferred for agents)
.\.venv\Scripts\collab.exe active
```

```bash
# Activated venv or POSIX
collab active
```

---

## Checklist (for AI agents)

- [ ] Listed all files the task will touch
- [ ] Ran lock check via venv `collab` (`.\.venv\Scripts\collab.exe active` on Windows, or `collab active` with venv activated) before file-modifying work
- [ ] Verified no target file is locked by another developer
- [ ] Applied edits only when files were unlocked or already locked by the current developer
- [ ] Did not run force-release on another developer's lock (forbidden)
