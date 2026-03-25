"""Supabase-backed collaborative file lock client.

Provides atomic lock acquisition, release, and daemon management for
preventing merge conflicts in multi-developer workflows.
"""

from __future__ import annotations

import argparse
import atexit
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger("collab.lock_client")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_COLLAB_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
_PROJECT_ROOT = os.path.abspath(os.path.join(_COLLAB_ROOT, ".."))

# Load .env from the project root (never modify .env)
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
LOCK_DEFAULT_EXPIRY = int(os.getenv("LOCK_DEFAULT_EXPIRY_MINUTES", "480"))
LOCK_STRICT = os.getenv("LOCK_STRICT", "0") == "1"

# PID file lives inside .collab/ so it stays with the feature
PID_FILE = os.path.join(_COLLAB_ROOT, ".daemon.pid")

# Maximum retry attempts for network errors
MAX_RETRIES = 3

# ---------------------------------------------------------------------------
# Supabase client (lazy import)
# ---------------------------------------------------------------------------
_supabase_create_client = None


def _get_create_client():
    """Lazy-load the supabase create_client function."""
    global _supabase_create_client
    if _supabase_create_client is None:
        try:
            from supabase import create_client

            _supabase_create_client = create_client
        except ImportError:
            logger.error(
                "supabase-py is not installed. Install it with: pip install supabase\n"
                "See .collab/.env.example for required environment variables."
            )
            sys.exit(1)
    return _supabase_create_client


def _validate_credentials() -> None:
    """Validate that Supabase credentials are present, exit with clear error if not."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error(
            "Missing Supabase credentials.\n"
            "  SUPABASE_URL=%s\n"
            "  SUPABASE_ANON_KEY=%s\n\n"
            "Please copy .collab/.env.example to .env at the project root\n"
            "and fill in your Supabase project credentials.\n"
            "See .collab/README.md for setup instructions.",
            SUPABASE_URL or "(not set)",
            "(set)" if SUPABASE_ANON_KEY else "(not set)",
        )
        sys.exit(1)


def _retry_on_network_error(func, *args, **kwargs) -> Any:
    """Execute func with exponential backoff retry on network errors."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            # Only retry on network-related errors
            if any(
                kw in err_str
                for kw in ("timeout", "connection", "network", "unreachable")
            ):
                wait = 2**attempt
                logger.debug(
                    "Network error (attempt %d/%d), retrying in %ds: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    wait,
                    e,
                )
                time.sleep(wait)
            else:
                raise
    raise last_error  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Supabase Lock Client
# ---------------------------------------------------------------------------
class LockClient:
    """Supabase-backed file lock client.

    All lock operations use the Supabase REST API with the official Python
    client. Lock acquisition uses the atomic ``acquire_lock`` RPC function
    defined in ``schema.sql`` to prevent race conditions.
    """

    def __init__(self, developer_id: Optional[str] = None) -> None:
        _validate_credentials()
        self.developer_id = developer_id or self._get_git_username()
        create_client = _get_create_client()
        key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
        self._client = create_client(SUPABASE_URL, key)
        self._parent_pid: Optional[int] = None

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_git_username() -> str:
        """Derive developer identity from git config or environment."""
        try:
            name = (
                subprocess.check_output(
                    ["git", "config", "user.name"], stderr=subprocess.DEVNULL
                )
                .decode()
                .strip()
            )
            if name:
                return name
        except Exception:
            pass
        return os.getenv("USERNAME") or os.getenv("USER") or "unknown_user"

    @staticmethod
    def _get_current_branch() -> Optional[str]:
        """Return the current git branch name, or None."""
        try:
            if sys.platform == "win32":
                return (
                    subprocess.check_output(
                        ["git", "branch", "--show-current"],
                        stderr=subprocess.DEVNULL,
                        cwd=_PROJECT_ROOT,
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
                        cwd=_PROJECT_ROOT,
                    )
                    .decode()
                    .strip()
                )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Response parsing (handles varying supabase-py response shapes)
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_response(res) -> Tuple[Optional[int], Any, Any]:
        """Normalize supabase-py response into (status, data, error)."""
        status = getattr(res, "status_code", None) or getattr(res, "status", None)
        data = getattr(res, "data", None)
        error = getattr(res, "error", None)
        if isinstance(res, dict):
            status = status or res.get("status") or res.get("status_code")
            data = data if data is not None else res.get("data")
            error = error or res.get("error")
        return (status, data, error)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def acquire(
        self,
        file_path: str,
        reason: Optional[str] = None,
        branch_name: Optional[str] = None,
        expires_minutes: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Acquire a lock on file_path using the atomic RPC function.

        Returns (success: bool, message: str).
        """
        # Local validation
        full_path = os.path.join(_PROJECT_ROOT, file_path)
        if not os.path.exists(full_path):
            return False, f"File or directory does not exist locally: {file_path}"

        branch = branch_name or self._get_current_branch()
        expiry_mins = expires_minutes or LOCK_DEFAULT_EXPIRY
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expiry_mins)
        token = str(uuid.uuid4())

        rpc_params = {
            "p_file_path": file_path,
            "p_developer_id": self.developer_id,
            "p_branch_name": branch,
            "p_reason": reason,
            "p_expires_at": expires_at.isoformat(),
            "p_lock_token": token,
        }

        try:
            res = _retry_on_network_error(
                lambda: self._client.rpc("acquire_lock", rpc_params).execute()
            )
        except Exception as e:
            return False, f"API Error: {e}"

        status, data, error = self._parse_response(res)

        if error:
            msg = (
                error.get("message", str(error))
                if isinstance(error, dict)
                else str(error)
            )
            return False, f"API Error: {msg}"

        # Parse RPC result
        if isinstance(data, list) and len(data) > 0:
            row = data[0]
            if row.get("status") == "ok":
                return True, token
            if row.get("status") == "conflict":
                owner = row.get("owner", "another developer")
                return False, (
                    f"⚠ {file_path} is locked by @{owner}. Editing is not recommended."
                )

        if status in (200, 201):
            return True, token

        return False, f"Unexpected response: status={status}, data={data}"

    def release(self, file_path: str) -> Tuple[bool, str]:
        """Release a lock on file_path owned by this developer.

        Returns (success: bool, message: str).
        """
        try:
            res = _retry_on_network_error(
                lambda: (
                    self._client.table("file_locks")
                    .delete()
                    .eq("file_path", file_path)
                    .eq("developer_id", self.developer_id)
                    .execute()
                )
            )
        except Exception as e:
            return False, f"API Error: {e}"

        status, data, error = self._parse_response(res)
        if error:
            return False, f"API Error: {error}"
        if status in (200, 204) or data is not None:
            return True, "released"
        return False, "No lock released (not owner or lock does not exist)"

    def active(self) -> List[Dict]:
        """Return all currently active locks."""
        try:
            res = _retry_on_network_error(
                lambda: self._client.table("file_locks").select("*").execute()
            )
        except Exception:
            return []
        _, data, error = self._parse_response(res)
        if error:
            return []
        return data or []

    def get_lock_status(self, file_path: str) -> Dict:
        """Return the lock status for a specific file."""
        try:
            res = _retry_on_network_error(
                lambda: (
                    self._client.table("file_locks")
                    .select("*")
                    .eq("file_path", file_path)
                    .execute()
                )
            )
        except Exception as e:
            return {"is_locked": False, "error": str(e)}

        _, data, error = self._parse_response(res)
        if error:
            return {"is_locked": False, "error": str(error)}

        rows = data or []
        if not rows:
            return {"is_locked": False, "can_edit": True}

        lock = rows[0]
        try:
            expiry = datetime.fromisoformat(lock.get("expires_at", ""))
        except (ValueError, TypeError):
            expiry = datetime.now(timezone.utc)

        if expiry < datetime.now(timezone.utc):
            return {"is_locked": False, "can_edit": True, "expired": True}

        return {
            "is_locked": True,
            "locked_by": lock.get("developer_id"),
            "acquired_at": lock.get("acquired_at"),
            "expires_at": lock.get("expires_at"),
            "reason": lock.get("reason"),
            "can_edit": lock.get("developer_id") == self.developer_id,
        }

    def release_all(self) -> int:
        """Release all locks held by this developer. Returns count released."""
        locks = self.active()
        my_locks = [lk for lk in locks if lk.get("developer_id") == self.developer_id]
        count = 0
        for lk in my_locks:
            ok, _ = self.release(lk.get("file_path", ""))
            if ok:
                count += 1
        return count

    def force_release(self, file_path: str) -> Tuple[bool, str]:
        """Force-release a lock regardless of owner (admin action)."""
        try:
            res = _retry_on_network_error(
                lambda: (
                    self._client.table("file_locks")
                    .delete()
                    .eq("file_path", file_path)
                    .execute()
                )
            )
        except Exception as e:
            return False, f"API Error: {e}"
        _, data, error = self._parse_response(res)
        if error:
            return False, f"API Error: {error}"
        if data is not None:
            return True, "force-released"
        return False, "No lock removed"

    def acquire_multiple(
        self,
        file_paths: List[str],
        reason: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> Tuple[bool, List[str], str]:
        """Acquire locks for multiple files. Returns (all_ok, failed_paths, message)."""
        failed = []
        for fp in file_paths:
            ok, msg = self.acquire(fp, reason=reason, branch_name=branch_name)
            if not ok:
                failed.append(fp)
                logger.warning("Lock conflict: %s — %s", fp, msg)
        if failed:
            return False, failed, "Conflicts or errors"
        return True, [], "Success"

    def release_multiple(self, file_paths: List[str]) -> Tuple[bool, int, str]:
        """Release locks for multiple files. Returns (ok, count, message)."""
        count = 0
        for fp in file_paths:
            ok, _ = self.release(fp)
            if ok:
                count += 1
        return True, count, "Success"

    def history(self, file_path: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Fetch lock history records."""
        try:
            q = (
                self._client.table("file_locks_history")
                .select("*")
                .order("id", desc=True)
                .limit(limit)
            )
            if file_path:
                q = q.eq("file_path", file_path)
            res = q.execute()
        except Exception:
            return []
        _, data, error = self._parse_response(res)
        return data or [] if not error else []

    # ------------------------------------------------------------------
    # Daemon management
    # ------------------------------------------------------------------
    def daemon_start(
        self, interval: int = 5, timeout_mins: int = 60, open_dashboard: bool = False
    ) -> None:
        """Start the watcher as a background daemon process."""
        pid = self._read_pid()
        if pid and self._is_process_alive(pid):
            print(f"Watcher already running (PID: {pid})")
            return

        print("Starting lock watcher in background...")
        cmd = [
            sys.executable,
            os.path.join(_COLLAB_ROOT, "core", "lock_client.py"),
            "watch",
            "--interval",
            str(interval),
            "--timeout",
            str(timeout_mins),
        ]
        if open_dashboard:
            cmd.append("--open-dashboard")

        if sys.platform == "win32":
            log_path = os.path.join(_COLLAB_ROOT, ".daemon.log")
            log_fh: Any
            try:
                log_fh = open(log_path, "a", encoding="utf-8")
            except Exception:
                log_fh = subprocess.DEVNULL

            pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            DETACHED = 0x00000008 | 0x08000000

            if os.path.exists(pythonw):
                proc = subprocess.Popen(
                    [pythonw] + cmd[1:],
                    stdout=log_fh,
                    stderr=log_fh,
                    close_fds=True,
                    cwd=_PROJECT_ROOT,
                )
            else:
                proc = subprocess.Popen(
                    cmd,
                    creationflags=DETACHED,
                    stdout=log_fh,
                    stderr=log_fh,
                    close_fds=True,
                    cwd=_PROJECT_ROOT,
                )
        else:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=_PROJECT_ROOT,
            )

        self._write_pid(proc.pid)
        time.sleep(0.5)

        if not self._is_process_alive(proc.pid):
            self._remove_pid()
            print(f"Watcher process (PID: {proc.pid}) exited immediately.")
            return

        print(f"Started (PID: {proc.pid})")

    def daemon_stop(self) -> None:
        """Stop the running watcher daemon."""
        pid = self._read_pid()
        if not pid or not self._is_process_alive(pid):
            print("No running watcher found.")
            self._remove_pid()
            return

        print(f"Stopping lock watcher (PID: {pid})...")

        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
            )
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        # Wait up to 5 seconds for clean exit
        for _ in range(10):
            if not self._is_process_alive(pid):
                break
            time.sleep(0.5)
        else:
            # Force kill if still running
            if sys.platform != "win32":
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        self._remove_pid()
        print("Stopped.")

    def daemon_status(self) -> bool:
        """Check if the watcher daemon is running."""
        pid = self._read_pid()
        if pid and self._is_process_alive(pid):
            print(f"Lock watcher is RUNNING (PID: {pid})")
            return True
        print("Lock watcher is NOT running.")
        self._remove_pid()
        return False

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> None:
        """Open the collaborative dashboard in the default browser."""
        url, _ = self._prepare_dashboard_server()
        if not url:
            return
        try:
            import webbrowser

            webbrowser.open(url)
        except Exception:
            print(f"Open in browser manually: {url}")

    def _prepare_dashboard_server(self) -> Tuple[Optional[str], Optional[str]]:
        """Create temp HTML with injected config, start local HTTP server.

        Returns (url, tmp_path) or (None, None) on error.
        """
        html_path = os.path.join(_COLLAB_ROOT, "dashboard", "index.html")
        if not os.path.exists(html_path):
            logger.error("Dashboard file not found at %s", html_path)
            return None, None

        try:
            with open(html_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as e:
            logger.error("Error reading dashboard template: %s", e)
            return None, None

        injected = {
            "url": SUPABASE_URL or "",
            "anonKey": SUPABASE_ANON_KEY or "",
            "serviceKey": SUPABASE_SERVICE_ROLE_KEY or None,
            "user": self.developer_id or "",
        }
        inject_script = (
            f"<script>window.__SUPABASE_CONFIG__ = {json.dumps(injected)};</script>\n"
        )

        try:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".html", encoding="utf-8"
            )
            tmp.write(inject_script)
            tmp.write(content)
            tmp.flush()
            tmp.close()
        except Exception as e:
            logger.error("Error creating temp dashboard file: %s", e)
            return None, None

        try:
            import http.server
            from functools import partial

            tmp_dir = os.path.dirname(tmp.name)
            filename = os.path.basename(tmp.name)

            Handler = partial(http.server.SimpleHTTPRequestHandler, directory=tmp_dir)

            # Silence request logging
            http.server.SimpleHTTPRequestHandler.log_message = lambda *a, **k: None  # type: ignore[method-assign]

            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            port = server.server_address[1]

            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            atexit.register(server.shutdown)

            url = f"http://127.0.0.1:{port}/{filename}"

            # Probe until ready
            import socket as _socket

            for _ in range(20):
                try:
                    with _socket.create_connection(("127.0.0.1", port), timeout=0.3):
                        break
                except Exception:
                    time.sleep(0.05)

            return url, tmp.name
        except Exception as e:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
            logger.error("Failed to start local dashboard server: %s", e)
            return None, None

    # ------------------------------------------------------------------
    # Watcher (foreground process)
    # ------------------------------------------------------------------
    def watch(
        self, interval: int = 5, timeout_mins: int = 60, open_dashboard: bool = False
    ) -> None:
        """Run the file-watching loop (foreground). Called by daemon_start."""
        self._parent_pid = os.getppid()
        self._write_pid(os.getpid())
        self._register_signal_handlers()

        if open_dashboard:
            try:
                self.dashboard()
            except Exception as e:
                logger.warning("Failed to open dashboard from watcher: %s", e)

        logger.info("Lock watcher started")
        logger.info("Developer: %s", self.developer_id)
        logger.info("Interval: %ds | Auto-timeout: %dm", interval, timeout_mins)
        logger.info("Monitoring local git changes for automatic locking...")

        last_modified: set = set()
        last_change_time = datetime.now()
        last_reconcile_time = datetime.now()
        last_parent_check = datetime.now()

        last_modified = self._reconcile()

        try:
            while True:
                try:
                    # Parent process liveness check every 30 seconds
                    if (datetime.now() - last_parent_check).total_seconds() > 30:
                        last_parent_check = datetime.now()
                        if self._parent_pid and not self._is_process_alive(
                            self._parent_pid
                        ):
                            logger.info(
                                "Parent process (PID: %d) is dead. Shutting down...",
                                self._parent_pid,
                            )
                            self._graceful_shutdown()
                            return

                    out = self._run_git_status()
                    current_modified = set()
                    if out:
                        for line in out.splitlines():
                            if len(line) > 3:
                                path = self._parse_git_status_path(line)
                                if not self._should_ignore_path(path):
                                    current_modified.add(path)

                    if current_modified != last_modified:
                        last_change_time = datetime.now()
                        new_files = current_modified - last_modified
                        if new_files:
                            ts = datetime.now().strftime("%H:%M:%S")
                            logger.info("[%s] Detected: %s", ts, list(new_files))
                            branch = self._get_current_branch()
                            ok, failed, msg = self.acquire_multiple(
                                list(new_files),
                                branch_name=branch,
                                reason="Auto-Watch Sync",
                            )
                            if ok:
                                logger.info("Locked: %s", list(new_files))
                            else:
                                logger.warning("CONFLICT ALERT: %s", msg)

                        released = last_modified - current_modified
                        if released:
                            ts = datetime.now().strftime("%H:%M:%S")
                            logger.info("[%s] Finalised: %s", ts, list(released))
                            ok, count, _ = self.release_multiple(list(released))
                            if ok and count > 0:
                                logger.info("Released: %d file(s)", count)

                        last_modified = current_modified
                    else:
                        # Periodic reconciliation
                        if (datetime.now() - last_reconcile_time) > timedelta(
                            minutes=15
                        ):
                            last_modified = self._reconcile()
                            last_reconcile_time = datetime.now()

                        # Idle timeout
                        idle = datetime.now() - last_change_time
                        if timeout_mins > 0 and idle > timedelta(minutes=timeout_mins):
                            logger.info(
                                "Watcher timed out after %dm inactivity.", timeout_mins
                            )
                            break

                    time.sleep(interval)
                except Exception as e:
                    logger.error("Error in watcher loop: %s", e)
                    time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user.")
        finally:
            self._graceful_shutdown()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _register_signal_handlers(self) -> None:
        """Register cleanup handlers for clean shutdown."""
        atexit.register(self._graceful_shutdown)

        def _handle_signal(signum, frame):
            logger.info("Received signal %d, shutting down...", signum)
            self._graceful_shutdown()
            sys.exit(0)

        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

    def _graceful_shutdown(self) -> None:
        """Release all locks and clean up PID file."""
        try:
            count = self.release_all()
            if count > 0:
                logger.info("Released %d lock(s) during shutdown.", count)
        except Exception as e:
            logger.error("Error releasing locks during shutdown: %s", e)
        self._remove_pid()

    def _reconcile(self) -> set:
        """Sync Supabase locks with local git status."""
        logger.info("Reconciling Supabase locks with local Git status...")
        try:
            out = self._run_git_status()
            git_modified = set()
            if out:
                for line in out.splitlines():
                    if len(line) > 3:
                        p = self._parse_git_status_path(line)
                        if not self._should_ignore_path(p):
                            git_modified.add(p)
        except Exception as e:
            logger.error("Error getting git status: %s", e)
            return set()

        try:
            active = self.active()
            my_locks = {
                lk["file_path"]
                for lk in active
                if lk.get("developer_id") == self.developer_id
            }
        except Exception as e:
            logger.error("Error getting Supabase locks: %s", e)
            return git_modified

        stale = my_locks - git_modified
        if stale:
            logger.info("Releasing %d stale lock(s)...", len(stale))
            self.release_multiple(list(stale))

        missing = git_modified - my_locks
        if missing:
            logger.info("Acquiring %d missing lock(s)...", len(missing))
            branch = self._get_current_branch()
            self.acquire_multiple(
                list(missing), branch_name=branch, reason="Auto-Watch Sync"
            )

        logger.info("Reconciliation complete.")
        return git_modified

    @staticmethod
    def _run_git_status() -> str:
        """Run git status --porcelain and return output."""
        args = ["git", "status", "--porcelain"]
        if sys.platform == "win32":
            return subprocess.check_output(
                args, stderr=subprocess.DEVNULL, creationflags=0x08000000
            ).decode().strip()
        else:
            return subprocess.check_output(
                args, stderr=subprocess.DEVNULL
            ).decode().strip()

    @staticmethod
    def _parse_git_status_path(line: str) -> str:
        """Extract file path from git status --porcelain, handling renames."""
        p = line[3:].strip()
        if " -> " in p:
            p = p.split(" -> ")[-1].strip()
        if p.startswith('"') and p.endswith('"'):
            p = p[1:-1]
            try:
                p = p.encode('utf-8').decode('unicode_escape')
            except Exception:
                pass
        return p

    @staticmethod
    def _should_ignore_path(path: str) -> bool:
        """Return True for paths the watcher should skip."""
        norm = path.replace("\\", "/")
        if "/.git/" in norm or norm.startswith(".git/"):
            return True
        if norm.startswith(".collab/"):
            return True
        return False

    @staticmethod
    def _read_pid() -> Optional[int]:
        """Read daemon PID from the PID file."""
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    return int(f.read().strip())
            except (ValueError, OSError):
                pass
        return None

    @staticmethod
    def _write_pid(pid: int) -> None:
        """Write daemon PID to the PID file."""
        try:
            with open(PID_FILE, "w") as f:
                f.write(str(pid))
        except OSError as e:
            logger.warning("Could not write PID file: %s", e)

    @staticmethod
    def _remove_pid() -> None:
        """Remove the PID file if it exists."""
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except OSError:
            pass

    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        """Check if a process with the given PID is alive."""
        if sys.platform == "win32":
            try:
                import psutil

                return bool(psutil.pid_exists(pid))
            except ImportError:
                # Fallback: use tasklist
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
                return True  # Process exists but we lack permission


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _run_cli() -> None:
    """CLI entry point for the lock client."""
    parser = argparse.ArgumentParser(
        description="Collaborative File Lock Manager (Supabase)"
    )
    sub = parser.add_subparsers(dest="command")

    # acquire
    acq = sub.add_parser("acquire", help="Acquire a lock on a file")
    acq.add_argument("file_path")
    acq.add_argument("--reason", help="Reason for the lock")

    # release
    rel = sub.add_parser("release", help="Release a lock on a file")
    rel.add_argument("file_path")

    # active
    sub.add_parser("active", help="List all active locks")

    # status
    st = sub.add_parser("status", help="Check lock status of a file")
    st.add_argument("file_path")

    # release-all
    sub.add_parser("release-all", help="Release all locks held by you")

    # force-release
    fr = sub.add_parser("force-release", help="Force release a lock (admin)")
    fr.add_argument("file_path")

    # acquire-batch
    ab = sub.add_parser("acquire-batch", help="Acquire locks on multiple files")
    ab.add_argument("file_paths", nargs="+")
    ab.add_argument("--reason")

    # release-batch
    rb = sub.add_parser("release-batch", help="Release locks on multiple files")
    rb.add_argument("file_paths", nargs="+")

    # daemon-start
    ds = sub.add_parser("daemon-start", help="Start the watcher daemon")
    ds.add_argument("--open-dashboard", action="store_true")

    # daemon-stop
    sub.add_parser("daemon-stop", help="Stop the watcher daemon")

    # daemon-status
    sub.add_parser("daemon-status", help="Check watcher daemon status")

    # dashboard
    sub.add_parser("dashboard", help="Open the collaborative dashboard")

    # reconcile
    sub.add_parser("reconcile", help="Sync local git status with Supabase")

    # history
    hp = sub.add_parser("history", help="Show lock history")
    hp.add_argument("file_path", nargs="?")
    hp.add_argument("--limit", type=int, default=20)

    # watch (internal, called by daemon-start)
    wp = sub.add_parser("watch", help="Run watcher in foreground")
    wp.add_argument("--interval", type=int, default=5)
    wp.add_argument("--timeout", type=int, default=60)
    wp.add_argument("--open-dashboard", action="store_true")

    args = parser.parse_args()
    client = LockClient()

    if args.command == "acquire":
        ok, msg = client.acquire(args.file_path, reason=args.reason)
        if ok:
            print(f"✓ Locked {args.file_path} (ID: {msg})")
        else:
            print(f"✗ Failed to lock {args.file_path}: {msg}")
        sys.exit(0 if ok else 1)

    elif args.command == "release":
        ok, msg = client.release(args.file_path)
        print(f"{'✓' if ok else '✗'} {msg}")

    elif args.command == "active":
        locks = client.active()
        if not locks:
            print("No active locks.")
        else:
            for lk in locks:
                print(
                    f"  {lk.get('file_path')} — @{lk.get('developer_id')} "
                    f"(branch: {lk.get('branch_name', 'N/A')}, "
                    f"reason: {lk.get('reason', 'N/A')})"
                )

    elif args.command == "status":
        info = client.get_lock_status(args.file_path)
        if info.get("is_locked"):
            print(
                f"🔒 Locked by @{info.get('locked_by')} "
                f"since {info.get('acquired_at')} "
                f"(expires: {info.get('expires_at')})"
            )
        else:
            print("🔓 File is unlocked.")

    elif args.command == "release-all":
        count = client.release_all()
        print(f"Released {count} lock(s).")

    elif args.command == "force-release":
        ok, msg = client.force_release(args.file_path)
        print(f"{'✓' if ok else '✗'} {msg}")

    elif args.command == "acquire-batch":
        ok, failed, msg = client.acquire_multiple(
            args.file_paths, reason=getattr(args, "reason", None)
        )
        if ok:
            print(f"✓ Locked {len(args.file_paths)} file(s).")
        else:
            print(f"✗ {msg}. Failed: {failed}")
            sys.exit(1)

    elif args.command == "release-batch":
        ok, count, msg = client.release_multiple(args.file_paths)
        print(f"Released {count} lock(s).")

    elif args.command == "daemon-start":
        open_flag = getattr(args, "open_dashboard", False)
        auto_env = os.getenv("AUTO_OPEN_DASHBOARD", "0").lower() in ("1", "true", "yes")
        client.daemon_start(open_dashboard=(open_flag or auto_env))

    elif args.command == "daemon-stop":
        client.daemon_stop()

    elif args.command == "daemon-status":
        client.daemon_status()

    elif args.command == "dashboard":
        client.dashboard()
        print("Dashboard local server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    elif args.command == "reconcile":
        client._reconcile()

    elif args.command == "history":
        rows = client.history(
            getattr(args, "file_path", None), limit=getattr(args, "limit", 20)
        )
        print(json.dumps(rows, indent=2))

    elif args.command == "watch":
        client.watch(
            interval=getattr(args, "interval", 5),
            timeout_mins=getattr(args, "timeout", 60),
            open_dashboard=getattr(args, "open_dashboard", False),
        )

    else:
        parser.print_help()


def main():
    """Entry point for ``python -m .collab.core.lock_client``."""
    _run_cli()


if __name__ == "__main__":
    main()
