"""Standalone lock watcher for PyCharm and other IDEs.

Monitors local git status and subscribes to Supabase Realtime for
collaborative file lock notifications. Uses plyer for cross-platform
desktop notifications.

Usage:
    python .collab/pycharm/live_locks_watcher.py [--interval 5] [--timeout 0]
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone

# Ensure .collab packages are importable
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_COLLAB_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
_PROJECT_ROOT = os.path.abspath(os.path.join(_COLLAB_ROOT, ".."))
sys.path.insert(0, _COLLAB_ROOT)

# Load environment before reading config variables
load_dotenv = __import__("dotenv", fromlist=["load_dotenv"]).load_dotenv  # noqa: E402
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# ---------------------------------------------------------------------------
# UTF-8 encoding (Windows fix — same pattern as validate_code.py / run.py)
# ---------------------------------------------------------------------------
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("collab.pycharm_watcher")

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
try:
    from supabase import create_client
except ImportError:
    logger.error("supabase not installed. Run: pip install supabase")
    sys.exit(1)

try:
    from plyer import notification as desktop_notify
except ImportError:
    desktop_notify = None
    logger.warning(
        "plyer not installed — desktop notifications disabled. "
        "Run: pip install plyer"
    )

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PID_FILE = os.path.join(_COLLAB_ROOT, ".daemon.pid")
DEVELOPER_ID = None

# Track files currently in conflict (locked by another dev)
_active_conflicts: set[str] = set()
# Track remote locks we already warned about (avoid duplicate notifications)
_warned_remote_locks: set[str] = set()
# Guard to prevent _graceful_shutdown from running more than once
_shutdown_done: bool = False


def _get_developer_id() -> str:
    """Derive developer identity from git config or environment."""
    try:
        name = (
            subprocess.check_output(
                ["git", "config", "user.name"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        if name:
            return name
    except Exception:
        pass
    return os.getenv("USERNAME") or os.getenv("USER") or "unknown_user"


def _get_current_branch() -> str:
    """Return the current git branch name."""
    try:
        if sys.platform == "win32":
            return (
                subprocess.check_output(
                    ["git", "branch", "--show-current"],
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000,
                )
                .decode()
                .strip()
            )
        else:
            return (
                subprocess.check_output(
                    ["git", "branch", "--show-current"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
    except Exception:
        return "unknown"


def _parse_git_status_path(line: str) -> str:
    """Extract file path from git status --porcelain line."""
    p = line[3:].strip()
    if " -> " in p:
        p = p.split(" -> ")[-1].strip()
    if p.startswith('"') and p.endswith('"'):
        p = p[1:-1]
    return p


def _should_ignore_path(path: str) -> bool:
    """Return True for paths the watcher should skip."""
    norm = path.replace("\\", "/")
    if "/.git/" in norm or norm.startswith(".git/"):
        return True
    if norm.startswith(".collab/"):
        return True
    return False


def _notify(title: str, message: str) -> None:
    """Send a desktop notification if plyer is available."""
    if desktop_notify:
        try:
            desktop_notify.notify(
                title=title,
                message=message,
                app_name="Collab Locks",
                timeout=5,
            )
        except Exception:
            logger.info("[Notification] %s: %s", title, message)
    else:
        logger.info("[Notification] %s: %s", title, message)


def _is_process_alive(pid: int) -> bool:
    """Check if a process is alive."""
    if sys.platform == "win32":
        try:
            import psutil

            return bool(psutil.pid_exists(pid))
        except ImportError:
            try:
                out = subprocess.check_output(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    text=True,
                    creationflags=0x08000000,
                )
                return str(pid) in out
            except Exception:
                return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True


def _scan_remote_locks(client) -> None:
    """Fetch all active locks and warn about files locked by other developers.

    This runs independently of ``git status`` so the user receives
    conflict warnings *before* saving a file.  Only new remote locks
    trigger a desktop notification (tracked via ``_warned_remote_locks``).
    """
    try:
        res = client.table("file_locks").select("*").execute()
        data = getattr(res, "data", None) or []
    except Exception as exc:
        logger.debug("Remote lock scan failed: %s", exc)
        return

    current_remote: set[str] = set()
    for lock in data:
        owner = lock.get("developer_id", "")
        fp = lock.get("file_path", "")
        if owner == DEVELOPER_ID or not fp:
            continue
        current_remote.add(fp)
        if fp not in _warned_remote_locks:
            _warned_remote_locks.add(fp)
            logger.warning("🔒 REMOTE LOCK: %s is locked by @%s", fp, owner)
            _notify(
                "File Locked",
                f"{fp} is locked by @{owner}.\n" "Coordinate before editing.",
            )

    # Clear warnings for locks that were released remotely
    released = _warned_remote_locks - current_remote
    if released:
        _warned_remote_locks.difference_update(released)
        for fp in released:
            logger.info("✅ Remote lock cleared: %s", fp)


def _start_dashboard_server() -> str | None:
    """Start a local HTTP server serving the dashboard and return the URL.

    Returns the ``http://127.0.0.1:<port>/...`` URL that terminals render
    as a clickable link, or *None* on failure.
    """
    import http.server
    import json as _json
    import tempfile
    from functools import partial

    html_path = os.path.join(_COLLAB_ROOT, "dashboard", "index.html")
    if not os.path.exists(html_path):
        logger.warning("Dashboard HTML not found at %s", html_path)
        return None

    try:
        with open(html_path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except Exception as exc:
        logger.warning("Failed to read dashboard template: %s", exc)
        return None

    injected = {
        "url": SUPABASE_URL or "",
        "anonKey": SUPABASE_ANON_KEY or "",
        "serviceKey": SUPABASE_SERVICE_ROLE_KEY or None,
        "user": DEVELOPER_ID or "",
    }
    inject_script = (
        f"<script>window.__SUPABASE_CONFIG__ = {_json.dumps(injected)};</script>\n"
    )

    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".html", encoding="utf-8"
        )
        tmp.write(inject_script)
        tmp.write(content)
        tmp.flush()
        tmp.close()
    except Exception as exc:
        logger.warning("Failed to create temp dashboard: %s", exc)
        return None

    try:
        tmp_dir = os.path.dirname(tmp.name)
        filename = os.path.basename(tmp.name)

        handler = partial(http.server.SimpleHTTPRequestHandler, directory=tmp_dir)
        # Silence per-request log noise
        handler_cls = http.server.SimpleHTTPRequestHandler
        handler_cls.log_message = lambda *_a, **_k: None  # type: ignore[method-assign]

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        atexit.register(server.shutdown)

        return f"http://127.0.0.1:{port}/{filename}"
    except Exception as exc:
        logger.warning("Failed to start dashboard server: %s", exc)
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        return None


def _graceful_shutdown() -> None:
    """Release all locks and clean up PID file.

    Guarded so it runs at most once, even when invoked from multiple shutdown paths
    (signal handler, finally block, atexit).
    """
    global _shutdown_done
    if _shutdown_done:
        return
    _shutdown_done = True

    dev_id = DEVELOPER_ID
    if dev_id and SUPABASE_URL and SUPABASE_ANON_KEY:
        try:
            client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            client.table("file_locks").delete().eq("developer_id", dev_id).execute()
            logger.info("✅ Released all locks during shutdown.")
        except Exception as e:
            logger.error("Error releasing locks during shutdown: %s", e)
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Main Watcher Loop
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the PyCharm live lock watcher."""
    global DEVELOPER_ID

    import argparse

    parser = argparse.ArgumentParser(description="PyCharm Live Lock Watcher")
    parser.add_argument(
        "--interval", type=int, default=5, help="Poll interval (seconds)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Idle timeout in minutes (0 = disabled)",
    )
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env.\n"
            "See .collab/.env.example for setup."
        )
        sys.exit(1)

    DEVELOPER_ID = _get_developer_id()

    # Write PID file (unified with lock_client daemon)
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass

    # Register cleanup
    atexit.register(_graceful_shutdown)

    def _signal_handler(signum, frame):
        logger.info("Received signal %d, shutting down...", signum)
        _graceful_shutdown()
        sys.exit(0)

    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Create Supabase client
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # Start local dashboard server for a clickable URL
    dashboard_url = _start_dashboard_server()

    logger.info("=" * 60)
    logger.info("Collab Locks -- PyCharm Watcher")
    logger.info("Developer: %s", DEVELOPER_ID)
    timeout_label = f"{args.timeout}m" if args.timeout > 0 else "disabled"
    logger.info("Interval: %ds | Timeout: %s", args.interval, timeout_label)
    if dashboard_url:
        logger.info("Dashboard: %s", dashboard_url)
    else:
        logger.info("Dashboard: python collab.py dashboard")
    logger.info("=" * 60)

    last_modified: set = set()
    last_change_time = datetime.now()
    last_remote_scan = datetime.now()

    # Initial remote lock scan
    _scan_remote_locks(client)

    try:
        while True:

            # Remote lock scan every 30 seconds (independent of git status)
            now = datetime.now()
            if (now - last_remote_scan).total_seconds() > 30:
                last_remote_scan = now
                _scan_remote_locks(client)

            # Get git status
            try:
                if sys.platform == "win32":
                    out = (
                        subprocess.check_output(
                            ["git", "status", "--porcelain"],
                            stderr=subprocess.DEVNULL,
                            creationflags=0x08000000,
                        )
                        .decode()
                        .strip()
                    )
                else:
                    out = (
                        subprocess.check_output(
                            ["git", "status", "--porcelain"],
                            stderr=subprocess.DEVNULL,
                        )
                        .decode()
                        .strip()
                    )
            except Exception as e:
                logger.error("git status failed: %s", e)
                time.sleep(args.interval)
                continue

            current_modified = set()
            if out:
                for line in out.splitlines():
                    if len(line) > 3:
                        p = _parse_git_status_path(line)
                        if not _should_ignore_path(p):
                            current_modified.add(p)

            if current_modified != last_modified:
                last_change_time = datetime.now()
                branch = _get_current_branch()

                # New files to lock
                new_files = current_modified - last_modified
                for fp in new_files:
                    try:
                        res = client.rpc(
                            "acquire_lock",
                            {
                                "p_file_path": fp,
                                "p_developer_id": DEVELOPER_ID,
                                "p_branch_name": branch,
                                "p_reason": "Auto-Watch",
                                "p_expires_at": (
                                    datetime.now(timezone.utc) + timedelta(hours=8)
                                ).isoformat(),
                                "p_lock_token": str(__import__("uuid").uuid4()),
                            },
                        ).execute()
                        data = getattr(res, "data", None) or []
                        if (
                            isinstance(data, list)
                            and data
                            and data[0].get("status") == "conflict"
                        ):
                            owner = data[0].get("owner", "someone")
                            _active_conflicts.add(fp)
                            logger.warning(
                                "⚠️ CONFLICT: %s is locked by @%s "
                                "-- your changes may cause a merge "
                                "conflict. Run: python collab.py "
                                "dashboard",
                                fp,
                                owner,
                            )
                            _notify(
                                "Lock Conflict",
                                f"{fp} is locked by @{owner}.\n"
                                "Coordinate before committing.",
                            )
                        else:
                            logger.info("🔒 [LOCKED] %s", fp)
                    except Exception as e:
                        logger.error("Failed to acquire lock for %s: %s", fp, e)

                # Files no longer modified locally
                released = last_modified - current_modified
                for fp in released:
                    # Was this file in conflict?
                    if fp in _active_conflicts:
                        _active_conflicts.discard(fp)
                        logger.info(
                            "✅ Conflict cleared: %s " "(file reverted or resolved)",
                            fp,
                        )
                    else:
                        try:
                            client.table("file_locks").delete().eq("file_path", fp).eq(
                                "developer_id", DEVELOPER_ID
                            ).execute()
                            logger.info("🔓 [RELEASED] %s", fp)
                        except Exception as e:
                            logger.error(
                                "Failed to release lock for %s: %s",
                                fp,
                                e,
                            )

                last_modified = current_modified
            else:
                # Idle timeout check
                idle = datetime.now() - last_change_time
                if args.timeout > 0 and idle > timedelta(minutes=args.timeout):
                    logger.info("Timed out after %dm inactivity.", args.timeout)
                    break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    finally:
        _graceful_shutdown()


if __name__ == "__main__":
    main()
