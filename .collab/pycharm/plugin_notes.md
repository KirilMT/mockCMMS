# PyCharm — Collaborative Lock Watcher Setup

## Overview

The PyCharm watcher is a standalone Python script that monitors your local git
changes and automatically acquires/releases file locks via Supabase. It uses
`plyer` for cross-platform desktop notifications.

## Prerequisites

Make sure you've run the development setup script at least once (this installs all Python dependencies, including `supabase` and `plyer`):

```powershell
.\scripts\setup-dev.ps1
```

## Quick Start (Manual)

```bash
python .collab/pycharm/live_locks_watcher.py --interval 5 --timeout 60
```

## Auto-Start on Project Open (Recommended)

### Option A: External Tools + Startup Task

1. **Create an External Tool**:
   - Go to `Settings → Tools → External Tools`
   - Click `+` to add a new tool:
     - **Name**: `Collab Lock Watcher`
     - **Program**: `$ProjectFileDir$/.venv/Scripts/python.exe`
       (or just `python` if not using a venv)
     - **Arguments**: `$ProjectFileDir$/.collab/pycharm/live_locks_watcher.py --interval 5 --timeout 480`
     - **Working directory**: `$ProjectFileDir$`

2. **Add as Startup Task**:
   - Go to `Settings → Tools → Startup Tasks`
   - Click `+` → `Add External Tool`
   - Select `Collab Lock Watcher`
   - Check `Run on project open`

### Option B: Run Configuration

1. Go to `Run → Edit Configurations`
2. Click `+` → `Python`
3. Configure:
   - **Name**: `Collab Lock Watcher`
   - **Script path**: `.collab/pycharm/live_locks_watcher.py`
   - **Parameters**: `--interval 5 --timeout 480`
   - **Working directory**: `$ProjectFileDir$`
   - **Python interpreter**: Your project's venv Python

4. To auto-start: Go to `Settings → Build, Execution, Deployment → Console`, and
   check `Run with my console manager` with the watcher configuration.

## Stopping the Watcher

- **Manual**: Press `Ctrl+C` in the Run tool window
- **Automatic**: The watcher detects when PyCharm (parent process) exits and
  performs a clean shutdown, releasing all locks
- **Kill manually**:

  ```bash
  # Windows
  type .collab\.pycharm_watcher.pid | ForEach-Object { taskkill /F /PID $_ }

  # Unix
  kill $(cat .collab/.pycharm_watcher.pid)
  ```

## Output

The watcher prints structured status lines to stdout:

```
[10:30:15] INFO: Collab Locks — PyCharm Watcher
[10:30:15] INFO: Developer: alice
[10:30:15] INFO: Interval: 5s | Timeout: 60m
[10:30:20] INFO: 🔒 Locked: src/services/db_utils.py
[10:31:45] WARNING: ⚠ CONFLICT: src/app.py is locked by @bob
[10:32:10] INFO: 🔓 Released: src/services/db_utils.py
```
