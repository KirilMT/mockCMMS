# PyCharm — Collaborative Lock Watcher Setup

## Overview

The PyCharm watcher is a standalone Python script that monitors your local git
changes and automatically acquires/releases file locks via Supabase. It uses
`plyer` for cross-platform desktop notifications.

## Automatic Setup (Recommended)

Run the development setup script — it auto-detects PyCharm and installs the
Run Configuration for you:

```powershell
.\scripts\setup-dev.ps1
```

After setup, open **Run > Collab Lock Watcher** in PyCharm and click Run.
The watcher runs in the **Run** tool window (background tab) and will not
interfere with your coding workflow.

## Manual Start

```bash
python .collab/pycharm/live_locks_watcher.py --interval 5 --timeout 480
```

## How Conflicts Work

When the watcher detects a conflict (file locked by another developer):

1. A **desktop notification** pops up with the file name and lock owner
2. The terminal shows a detailed warning with a dashboard link:
   ```
   [10:30] WARNING: ⚠ CONFLICT: src/app.py is locked by @bob
                     — your changes may cause a merge conflict.
                     Run: python collab.py dashboard
   ```
3. **Commits are blocked** — the `pre-commit` hook prevents committing
   files locked by another developer
4. When you revert the file or the conflict resolves, the watcher logs:
   ```
   [10:35] INFO: ✅ Conflict cleared: src/app.py (file reverted or resolved)
   ```

## Stopping the Watcher

- **Manual**: Press the **Stop** button (⬛) in PyCharm's Run tool window, or `Ctrl+C`
- **Automatic**: When PyCharm sends SIGINT/SIGTERM on IDE close, the watcher
  performs a clean shutdown, releasing all locks via its signal handler
- **CLI**: `python collab.py daemon-stop`

## Output

The watcher prints structured status lines to stdout:

```
[10:30:15] INFO: Collab Locks — PyCharm Watcher
[10:30:15] INFO: Developer: alice
[10:30:15] INFO: Interval: 5s | Timeout: 480m
[10:30:15] INFO: Dashboard: python collab.py dashboard (Ctrl+Click to open)
[10:30:20] INFO: 🔒 Locked: src/services/db_utils.py
[10:31:45] WARNING: ⚠ CONFLICT: src/app.py is locked by @bob
[10:32:10] INFO: 🔓 Released: src/services/db_utils.py
[10:33:00] INFO: ✅ Conflict cleared: src/app.py (file reverted or resolved)
```
