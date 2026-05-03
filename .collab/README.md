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

# Force release all locks (admin)
python collab.py force-release-all

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

| Hook          | Behavior                                                                            |
| ------------- | ----------------------------------------------------------------------------------- |
| `pre-commit`  | Checks staged files for conflicts. **Always blocks** if another dev holds the lock. |
| `post-commit` | **Preserves Locks**: Does nothing, ensuring locks persist until files are pushed.   |
| `pre-push`    | **Full Release**: Releases all remaining locks for the developer.                   |

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

## Session Identity & Stability

The system uses a **Stable Session Token** logic to ensure that your identity is consistent across different tools on the same machine.

- **Cross-IDE Re-adoption**: If you start a watcher in Antigravity and then switch to PyCharm, the new watcher will automatically re-adopt your existing locks (marking them as `[RESUMED]`) instead of showing "Multi-Session" warnings.
- **Normalization**: Identity is derived from your `developer_id`, your `hostname`, and the `project_root`. These are normalized to lowercase to ensure consistency across different environment configurations.

---

## Automatic Lifecycle (Clean Machine)

On Windows, background daemons are designed to be "failure-hermetic" and self-cleaning.

- **Terminal-Tied Lifecycle**: When you start a daemon from an IDE's integrated terminal, it ties its lifecycle to that specific **Terminal Shell**. Closing the IDE window or the terminal tab will automatically terminate the background locking process within 5 seconds.
- **Lock Preservation**: Closing the IDE or stopping the watcher **strictly preserves your locks** in Supabase. Your work remains protected until you explicitly push it or release it manually.
- **Self-Healing Startup**: If you start a new watcher while an "orphaned" one (whose owner has died) is still running, the system will automatically detect the orphan, terminate it, and replace it with a fresh process.

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

### Scenario B — Lock Lifecycle (Commit vs. Revert)

1. **Local Commit**: If you commit your changes but don't push yet, the watcher **preserves your lock**. This ensures your work remains protected until it is successfully delivered to the remote server.
2. **Rollback/Revert**: If you use `git restore` or `git checkout` to discard your changes so they match the server, the watcher detects that the file is no longer "in progress" and **automatically releases** the lock.
3. **Conflict Detection**: If Dev B tries to edit a file that Dev A has committed (but not pushed), Dev B's watcher will warn them: _"src/foo.py is locked by @Alice"_.

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
# Extract PID from JSON metadata and kill
$json = Get-Content .collab\.daemon.pid | ConvertFrom-Json
taskkill /F /PID $json.pid
Remove-Item .collab\.daemon.pid
```

**Unix/macOS:**

```bash
# Extract PID using jq and kill
kill $(cat .collab/.daemon.pid | jq -r .pid)
rm .collab/.daemon.pid
```

### Windows Background Execution

On Windows, the daemon automatically uses `pythonw.exe` (if available in the venv) to ensure no terminal window popups. It is executed with `DETACHED_PROCESS` and `CREATE_NO_WINDOW` flags to isolate it from system-wide PDF hooks (like Acrobat Distiller) that might otherwise cause "Error 183" popups.

### Startup Polling

When starting the daemon, the CLI polls for up to 3 seconds to wait for the background child to initialize and record its true PID. This handles environments where the initial Python launcher exits immediately after spawning the real watcher.

Or use the CLI:

```bash
python collab.py daemon-stop
```

---

## Logging

All collaborative system logs are consolidated in `.collab/logs/`:

- **`collab.log`**: Unified runtime log for collab components, including info, warnings, and errors.
- **`test_collab.log`**: Unified test-mode log used when `COLLAB_TEST_MODE=1`.

Daemon processes (started via `daemon-start` or IDE plugins) write structured logs to these files through the collab logging configuration.

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

### "Watcher already running" but it isn't

The system detects "Orphaned Watchers" automatically. If the software says it's already running but you are sure it isn't, running `python collab.py daemon-start` will automatically identify the dead parent process and replace the old watcher with a new one.

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

1. Check `.collab/logs/collab.log` for crash details and recent watcher/daemon lifecycle events.
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
