# Collaborative File Locking

Prevents merge conflicts by automatically locking files when a developer starts editing them, using Supabase Realtime as the backend.

---

## Prerequisites

- **Python** 3.10+
- **Supabase** account with a project ([supabase.com](https://supabase.com))
- **Node.js** (only for the VS Code extension)

---

## 5-Minute Setup Guide

### 1. Configure Environment Variables

Open `.env` at the **project root** and ensure your Supabase credentials are set. If you don't have an `.env` file, copy `.env.example` to `.env`:

Required variables:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL (from Project Settings → API) |
| `SUPABASE_ANON_KEY` | Anonymous/public key (from Project Settings → API → anon/public) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (optional, for admin force-release) |
| `LOCK_DEFAULT_EXPIRY_MINUTES` | Lock auto-expiry in minutes (default: 480 = 8 hours) |
| `LOCK_STRICT` | If `1`, git hooks block on lock errors. Default `0` (warn only) |

### 2. Create the Database Schema

Open your Supabase project's **SQL Editor** and run the contents of `.collab/schema.sql`.

This creates:
- `file_locks` table (active locks)
- `file_locks_history` table (audit trail)
- `acquire_lock()` RPC function (atomic lock acquisition)
- Row Level Security policies
- Realtime publication
- Auto-history trigger on lock release

### 3. Setup Development Environment

Run the global setup script to install dependencies (Python + npm) and copy the git hooks:

**Windows:**
```powershell
.\scripts\setup-dev.ps1
```

*(This script automatically installs `supabase`, `psutil`, `plyer` and copies Collab git hooks from `.collab/hooks/` to `.git/hooks/`).*

### 4. Verify Setup

```bash
python -m .collab.core.lock_client active
```

If connected, this shows all active locks (initially none).

---

## CLI Reference

```bash
# Lock a file
python collab.py acquire path/to/file.py --reason "Refactoring"

# Unlock a file
python collab.py release path/to/file.py

# Check file status
python collab.py status path/to/file.py

# List all active locks
python collab.py active

# Release all your locks
python collab.py release-all

# Force release (admin)
python collab.py force-release path/to/file.py

# Start background watcher
python collab.py daemon-start

# Stop watcher
python collab.py daemon-stop

# Check watcher status
python collab.py daemon-status

# Open dashboard
python collab.py dashboard

# View lock history
python collab.py history path/to/file.py --limit 20
```

---

## Git Hooks

The hooks are located in `.collab/hooks/` and are copied to `.git/hooks/` during setup. They run automatically:

| Hook | Behavior |
|------|----------|
| `pre-commit` | Acquires locks for staged files. Blocks if conflict (when `LOCK_STRICT=1`) |
| `post-commit` | Releases locks for committed files |
| `pre-push` | Releases all your remaining locks and stops the daemon |

If the lock client is unavailable (network error, Python not found), hooks **warn and continue** unless `LOCK_STRICT=1`.

---

## Dashboard

Open the real-time dashboard to monitor all team activity:

```bash
python collab.py dashboard
```

This starts a local HTTP server and opens the dashboard in your default browser. The dashboard:
- Shows all active file locks with developer, branch, reason, and expiry
- Updates in real-time via Supabase Realtime (no page refresh needed)
- Includes a **Force Release** button for stuck locks
- Shows lock history with durations and outcomes

---

## VS Code Extension

See [`.collab/vscode/README.md`](vscode/README.md) for installation instructions.

Features:
- Status bar showing lock state of the current file
- Real-time conflict warnings when someone else locks your file
- Commands: Show All Locks, Release My Locks, Open Dashboard

---

## PyCharm Setup

See [`.collab/pycharm/plugin_notes.md`](pycharm/plugin_notes.md) for setup instructions.

Features:
- Standalone Python watcher (no JVM/Kotlin plugin needed)
- Desktop notifications via `plyer`
- Auto-shutdown when PyCharm exits

---

## Workflow Scenarios

### Scenario A — Happy Path (Single Developer)

1. Developer opens IDE → watcher starts automatically
2. Developer edits `src/foo.py` → lock acquired automatically
3. Developer commits → lock released automatically
4. Dashboard reflects correct state at each step

### Scenario B — Conflict Detection (Two Developers)

1. Dev A locks `src/foo.py`
2. Dev B opens or edits `src/foo.py`
3. Dev B sees a warning in the status bar and a popup: *"⚠ src/foo.py is locked by @alice since 14:32"*
4. Dev A commits → lock releases
5. Dev B can now edit without warnings

### Scenario C — Orphaned Lock After IDE Crash

1. Dev A locks a file, then IDE crashes
2. The daemon detects the parent process is dead (checks every 30s)
3. Daemon auto-releases all of Dev A's locks
4. Dashboard shows the file as unlocked

### Scenario D — Force Release via Dashboard

1. Dev A is away, file is still locked
2. Dev B opens the dashboard, clicks **Force Release**
3. Lock is released, Dev B can now edit

### Scenario E — Clean IDE Shutdown

1. Developer edits files while locks are held
2. Developer closes IDE normally
3. Daemon shuts down via `deactivate()` hook / signal handler / atexit
4. Locks are released
5. **No files remain "in use" by orphaned processes**
6. Zip/archive operations succeed immediately after IDE close

---

## Kill the Daemon Manually

If the daemon is stuck:

**Windows:**
```powershell
# Read PID and kill
$pid = Get-Content .collab\.daemon.pid
taskkill /F /PID $pid
Remove-Item .collab\.daemon.pid
```

**Unix/macOS:**
```bash
kill $(cat .collab/.daemon.pid)
rm .collab/.daemon.pid
```

Or use the CLI:
```bash
python collab.py daemon-stop
```

---

## Troubleshooting

### Daemon stuck / not stopping

```bash
python collab.py daemon-stop
# If that fails, see "Kill the Daemon Manually" above
```

### Lock stuck (file shows locked but developer is gone)

1. Wait for the lock to expire (default 8 hours), or
2. Use the dashboard's **Force Release** button, or
3. Run: `python collab.py force-release path/to/file.py`

### Dashboard not loading

- Check that `.env` has `SUPABASE_URL` and `SUPABASE_ANON_KEY` set
- Verify the Supabase project is accessible
- Check browser console for errors
- Try: `python collab.py dashboard`

### Compression error ("file in use by another process")

This happens when orphaned daemon processes hold file handles. Fix:
1. Stop all daemons: `python collab.py daemon-stop`
2. Check for orphaned processes: look at `.collab/.daemon.pid`
3. Kill if needed (see "Kill the Daemon Manually")

### "Missing SUPABASE_URL or SUPABASE_ANON_KEY"

- Ensure you have an `.env` file at the project root
- Fill in your Supabase project credentials
- Make sure there are no quotes or trailing spaces in the values

---

## Database Schema

The complete schema is in `.collab/schema.sql`. Key components:

- **`file_locks`** — Active locks (file_path is primary key)
- **`file_locks_history`** — Audit trail of all lock/release events
- **`acquire_lock()`** — Atomic RPC function preventing race conditions
- **RLS policies** — Read access for all, write access scoped by owner
- **`log_lock_release()`** — Trigger that auto-records history on release
- **Realtime** — `file_locks` table published for live subscriptions
