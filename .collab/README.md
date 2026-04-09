# Collaborative File Locking

Prevents merge conflicts by automatically locking files when a developer starts editing them, using Supabase Realtime as the backend.

---

## Prerequisites

- **Python** 3.10+
- **Supabase** account with a project ([supabase.com](https://supabase.com))
- **Node.js** (only for the VS Code extension)

---

## 5-Minute Setup Guide

### 1. Create the Database Schema

Open your Supabase project's **SQL Editor** and run the contents of `.collab/schema.sql`.

This creates:

- `file_locks` table (active locks)
- `file_locks_history` table (audit trail)
- `acquire_lock()` RPC function (atomic lock acquisition)
- Row Level Security policies (see [Security Model](#security-model) below)
- Realtime publication
- Auto-history trigger on lock release

### 2. Run the Development Setup

One command handles everything — dependencies, `.env` configuration, git hooks, and IDE integration:

**Windows:**

```powershell
.\scripts\setup-dev.ps1
```

The script automatically:

- Installs `supabase`, `psutil`, `plyer` Python packages
- Prompts for Supabase credentials if `.env` is missing or has placeholders
- Copies git hooks from `.collab/hooks/` to `.git/hooks/`
- Detects your IDE (PyCharm or VS Code) and configures the watcher

> **Note:** `.collab/scripts/setup.ps1` and `setup.sh` exist as standalone installers for environments outside the full mockCMMS dev workflow. For mockCMMS developers, `scripts/setup-dev.ps1` is the only command you need.

### 3. Environment Variables

After running the setup, verify your `.env` at the project root has these values:

| Variable                    | Description                                                                     |
| --------------------------- | ------------------------------------------------------------------------------- |
| `SUPABASE_URL`              | Your Supabase project URL (from Project Settings → API)                         |
| `SUPABASE_ANON_KEY`         | Anonymous/public key (from Project Settings → API → anon/public)                |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (**required** for dashboard force-release and full API access) |
| `LOCK_STRICT`               | If `1`, git hooks block on lock errors. Default `0` (warn only)                 |

> **Important:** `SUPABASE_SERVICE_ROLE_KEY` is needed for the dashboard's Force Release button to work. Without it, only your own locks can be released.

### 4. Verify Setup

```bash
python collab.py active
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

# Start background watcher (no idle timeout by default)
python collab.py daemon-start
python collab.py daemon-start --interval 10 --timeout 480

# Stop watcher
python collab.py daemon-stop

# Check watcher status
python collab.py daemon-status

# Open dashboard
python collab.py dashboard

# View lock history (all files)
python collab.py history

# View lock history (specific file, with partial-match fallback)
python collab.py history src/app.py --limit 10

# View lock history as raw JSON (for scripting)
python collab.py history --json
```

---

## Git Hooks

The hooks are located in `.collab/hooks/` and are copied to `.git/hooks/` during setup. They run automatically:

| Hook          | Behavior                                                                           |
| ------------- | ---------------------------------------------------------------------------------- |
| `pre-commit`  | Checks staged files for conflicts. **Always blocks** if another dev holds the lock |
| `post-commit` | Releases locks for committed files                                                 |
| `pre-push`    | Releases all your remaining locks and stops the daemon                             |

If the lock client is unavailable (network error, Python not found), hooks **warn and continue** unless `LOCK_STRICT=1`.

> **Windows note:** Hooks set `PYTHONUTF8=1` before invoking Python to prevent encoding errors with Unicode symbols on `cp1252` terminals.

---

## Dashboard

Open the real-time dashboard to monitor all team activity:

```bash
python collab.py dashboard
```

This starts a local HTTP server and opens the dashboard in your default browser. The dashboard:

- Shows all active file locks with developer, branch, reason, and optional expiry (informational)
- Updates in real-time via Supabase Realtime (no page refresh needed)
- **Release** button for your own locks; **Force Release** for admins with `SUPABASE_SERVICE_ROLE_KEY`
- Shows lock history with durations and outcomes

The PyCharm watcher also auto-starts a dashboard server and prints a **clickable `http://` URL** in the Run console.

---

## VS Code Extension

See [`.collab/vscode/README.md`](vscode/README.md) for details.

`setup-dev.ps1` auto-detects VS Code (`.vscode/` directory) and runs `npm install` for the extension.

Features:

- **Lock-on-open:** When you open a locked file, a popup warns you immediately
- Actionable buttons: _Open Dashboard_, _Show Locks_
- Status bar showing lock state of the current file
- Real-time conflict warnings via Supabase Realtime
- Watcher output piped to **Output Channel** (View > Output > Collab Locks)
- Commands: Show All Locks, Release My Locks, Open Dashboard

---

## PyCharm Setup

See [`.collab/pycharm/plugin_notes.md`](pycharm/plugin_notes.md) for details.

`setup-dev.ps1` auto-detects PyCharm (`.idea/` directory) and installs a Run Configuration.

Features:

- Pre-configured Run Configuration (Run > Collab Lock Watcher)
- Desktop notifications via `plyer` for conflict alerts and **remote lock warnings**
- Proactive remote lock scanning every 30 seconds (warns about files locked by others **before you save**)
- Clear conflict messaging: "Conflict cleared" vs "Released"
- Clickable dashboard URL printed at startup in the Run console
- No idle timeout by default (watcher runs until explicitly stopped via Ctrl+C or IDE stop button)
- Clean single-pass shutdown — guarded to prevent duplicate release requests

---

## Workflow Scenarios

### Scenario A — Happy Path (Single Developer)

1. Developer opens IDE → starts the Collab Lock Watcher run configuration
2. Developer edits `src/foo.py` → lock acquired automatically
3. Developer commits → lock released automatically
4. Dashboard reflects correct state at each step

### Scenario B — Conflict Detection (Two Developers)

1. Dev A locks `src/foo.py`
2. Dev B's watcher detects the remote lock within 30 seconds (when start editing) and shows a desktop notification: _"src/foo.py is locked by @alice"_
3. If Dev B saves changes to `src/foo.py`, the lock acquisition returns a conflict
4. Dev A commits → lock releases → Dev B's watcher clears the warning
5. Dev B can now edit without warnings

### Scenario C — Force Release via Dashboard

1. Dev A is away, file is still locked
2. Dev B opens the dashboard (clickable URL in watcher output)
3. Dev B sees their own locks with a **Release** button and Dev A's locks with a **Locked** label
4. If Dev B has admin access (`SUPABASE_SERVICE_ROLE_KEY` configured), they see a **Force Release** button on Dev A's lock
5. Admin clicks Force Release → lock is released, Dev A is notified on next sync

### Scenario D — Clean IDE Shutdown

1. Developer edits files while locks are held
2. Developer stops the Collab Lock Watcher (or closes PyCharm)
3. Shutdown handler releases all locks exactly once (guarded)
4. **No files remain "in use" by orphaned processes**
5. Zip/archive operations succeed immediately after IDE close

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

## Logging

All collaborative system logs are consolidated in `.collab/logs/`:

- **`application.log`**: General operation logs, heartbeat info, and non-fatal warnings.
- **`errors.log`**: Crash reports and unhandled exception tracebacks.
- **`test_application.log` / `test_errors.log`**: Logs generated during test runs (isolated from production logs).

Daemon processes (started via `daemon-start` or IDE plugins) redirect their stdout and stderr to these files automatically.

---

## Troubleshooting

### Daemon stuck / not stopping

```bash
python collab.py daemon-stop
# If that fails, see "Kill the Daemon Manually" above
```

### Lock stuck (file shows locked but developer is gone)

1. Use the dashboard's **Force Release** button (admins only), or
2. Run: `python collab.py force-release path/to/file.py`

### Dashboard Force Release not working

- Only your **own** locks show a Release button by default
- To force-release another developer's lock, you need **admin access** — set `SUPABASE_SERVICE_ROLE_KEY` in `.env`
- Restart the watcher or dashboard after changing `.env`

### Dashboard not loading

- Check that `.env` has `SUPABASE_URL` and `SUPABASE_ANON_KEY` set
- Verify the Supabase project is accessible
- Check browser console for errors
- Try: `python collab.py dashboard`

### Compression error ("file in use by another process")

This happens when orphaned daemon processes hold file handles or leave stale PID files. Fix:

1. Check the logs in `.collab/logs/errors.log` for any crash details.
2. Stop all daemons: `python collab.py daemon-stop`
3. Check for orphaned processes: look at `.collab/.daemon.pid`
4. Kill if needed (see "Kill the Daemon Manually")

### "Missing SUPABASE_URL or SUPABASE_ANON_KEY"

- Ensure you have an `.env` file at the project root
- Fill in your Supabase project credentials
- Make sure there are no quotes or trailing spaces in the values

### Unicode errors in git hooks on Windows

Hooks use a two-layer approach: `PYTHONUTF8=1` environment variable plus explicit `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` inside the Python code. If you still see encoding errors, ensure your hooks are up to date:

```powershell
.\scripts\setup-dev.ps1
```

---

## Database Schema

The complete schema is in `.collab/schema.sql`. Key components:

- **`file_locks`** — Active locks (file_path is primary key)
- **`file_locks_history`** — Audit trail of all lock/release events
- **`acquire_lock()`** — Atomic RPC function preventing race conditions
- **RLS policies** — See [Security Model](#security-model) below
- **`log_lock_release()`** — Trigger that auto-records history on release
- **Realtime** — `file_locks` table published for live subscriptions

---

## Security Model

The collab system uses **shared API keys** (not per-user JWT tokens). Since individual users don't have unique JWTs, Supabase RLS cannot distinguish between developers at the database level.

**How access control works:**

| Role         | Key used                    | Can release        | Enforced by         |
| ------------ | --------------------------- | ------------------ | ------------------- |
| Regular user | `SUPABASE_ANON_KEY`         | **Own locks only** | Application code    |
| Admin        | `SUPABASE_SERVICE_ROLE_KEY` | **Any lock**       | Service role bypass |

- **Application-level enforcement:** The CLI (`lock_client.py`) and dashboard (`index.html`) filter delete operations by `developer_id` for non-admin users. Non-admin users can only release locks where `developer_id` matches their identity.
- **Admin bypass:** When `SUPABASE_SERVICE_ROLE_KEY` is configured, the dashboard shows a "Force Release" button on other developers' locks. The service role key bypasses RLS entirely.
- **RLS policies** are permissive at the database level because shared API keys make JWT-based row filtering impossible. Ownership checks happen in the application layer.
