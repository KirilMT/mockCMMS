"""Standalone lock watcher for PyCharm and other IDEs.

Monitors local git status and subscribes to Supabase Realtime for
collaborative file lock notifications. Uses plyer for cross-platform
desktop notifications.

Usage:
    python .collab/pycharm/live_locks_watcher.py [--interval 5] [--timeout 60]
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import subprocess
import sys
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
PID_FILE = os.path.join(_COLLAB_ROOT, ".pycharm_watcher.pid")
DEVELOPER_ID = None

# Track files currently in conflict (locked by another dev)
_active_conflicts: set[str] = set()


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


def _graceful_shutdown() -> None:
    """Release all locks and clean up PID file."""
    dev_id = DEVELOPER_ID
    if dev_id and SUPABASE_URL and SUPABASE_ANON_KEY:
        try:
            client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            client.table("file_locks").delete().eq("developer_id", dev_id).execute()
            logger.info("Released all locks during shutdown.")
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
        "--timeout", type=int, default=60, help="Idle timeout (minutes)"
    )
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env.\n"
            "See .collab/.env.example for setup."
        )
        sys.exit(1)

    DEVELOPER_ID = _get_developer_id()
    parent_pid = os.getppid()

    # Write PID file
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

    logger.info("=" * 60)
    logger.info("Collab Locks — PyCharm Watcher")
    logger.info("Developer: %s", DEVELOPER_ID)
    logger.info("Interval: %ds | Timeout: %dm", args.interval, args.timeout)
    logger.info("Parent PID: %d", parent_pid)
    logger.info("Dashboard: python collab.py dashboard (Ctrl+Click to open)")
    logger.info("=" * 60)

    last_modified: set = set()
    last_change_time = datetime.now()
    last_parent_check = datetime.now()

    try:
        while True:
            # Parent liveness check every 30 seconds
            now = datetime.now()
            if (now - last_parent_check).total_seconds() > 30:
                last_parent_check = now
                if not _is_process_alive(parent_pid):
                    logger.info(
                        "Parent (PID: %d) exited. Shutting down.",
                        parent_pid,
                    )
                    _graceful_shutdown()
                    return

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
                                "⚠ CONFLICT: %s is locked by @%s "
                                "— your changes may cause a merge "
                                "conflict. Run: python collab.py "
                                "dashboard",
                                fp,
                                owner,
                            )
                            _notify(
                                "🔒 Lock Conflict",
                                f"{fp} is locked by @{owner}.\n"
                                "Coordinate before committing.",
                            )
                        else:
                            logger.info("🔒 Locked: %s", fp)
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
                            logger.info("🔓 Released: %s", fp)
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
