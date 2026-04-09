"""Supabase-backed collaborative file lock client.

Provides atomic lock acquisition, release, and daemon management for preventing merge
conflicts in multi-developer workflows.
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


def _safe_now() -> datetime:
    """Return the current datetime using the (possibly monkeypatched) ``datetime``
    symbol imported into this module.

    Tests patch ``datetime`` with a fake
    class/instance and some replacement objects may present a ``now`` attribute
    that behaves oddly when bound. This helper attempts to call the patched
    ``now`` safely and falls back to the real datetime on failure.
    """
    try:
        return datetime.now()
    except TypeError:
        # If the patched datetime is an instance, try to fetch the class-level
        # attribute and call it as an unbound function (avoids implicit binding)
        try:
            cls = datetime if isinstance(datetime, type) else datetime.__class__
            now_attr = getattr(cls, "now", None)
            if callable(now_attr):
                # Call the class-level now and ensure we return a real datetime
                try:
                    res = now_attr()
                except TypeError:
                    # If calling now as an unbound function failed, continue to fallback
                    res = None
                # Use the real stdlib datetime type for isinstance checks to avoid
                # confusion when the module-level `datetime` has been monkeypatched
                from datetime import datetime as _real_dt

                if isinstance(res, _real_dt):
                    return res
        except Exception:
            pass
        # Last-resort: use the real datetime type from the stdlib
        from datetime import datetime as _real_dt

        return _real_dt.now()


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger("collab.lock_client")

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
LOCK_STRICT = os.getenv("LOCK_STRICT", "0") == "1"

# Expiry semantics: this project enforces NO automatic expiry. Locks persist
# until released explicitly. The DB RPC ignores time-based expiry; the
# expires_at column is kept for audit but is not used for automatic
# replacement. Clients do not send an expires_at value.

# Developer id prefixes treated as ephemeral (do not persist locks to the DB).
# Enforced in code (not configurable via .env) to avoid accidental skips.
EPHEMERAL_PREFIXES = ["test_dev", "ci"]

# (Intentionally no repo-level toggle) Do not expose a runtime flag to
# enable/disable `.collab/` locking — the watcher and client always consider
# files under `.collab/`.

# PID file lives inside .collab/ so it stays with the feature.
# Tests can override this via COLLAB_PID_FILE env var to avoid interfering with
# the live production watcher.
PID_FILE = os.getenv("COLLAB_PID_FILE") or os.path.join(_COLLAB_ROOT, ".daemon.pid")

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
        # First: if tests or other harnesses have injected a fake module into
        # ``sys.modules['supabase']``, prefer that module. Tests commonly
        # monkeypatch sys.modules rather than relying on import machinery, and
        # failing here causes fragile tests. If the injected module exposes a
        # ``create_client`` symbol it will be used. If the injected module has
        # a __file__ located inside the repository, treat that as accidental
        # local shadowing and fail fast with a clear message.
        supa_mod = sys.modules.get("supabase")
        if supa_mod is not None:
            # Honour any test-level import-time failures: if the import
            # machinery (builtins.__import__) has been monkeypatched to raise
            # ImportError for 'supabase' we should respect that and exit so
            # tests that simulate missing packages behave deterministically.
            try:
                __import__("supabase")
            except ImportError:
                logger.error(
                    "supabase-py is not installed (import failed). "
                    "Install it with: pip install supabase"
                )
                sys.exit(1)

            origin = None
            try:
                spec = getattr(supa_mod, "__spec__", None)
                spec_origin = getattr(spec, "origin", None) if spec else None
                origin = spec_origin or getattr(supa_mod, "__file__", None)
            except Exception:
                origin = None

            try:
                if origin:
                    origin_abs = os.path.abspath(origin)
                    if origin_abs.startswith(_COLLAB_ROOT):
                        logger.error(
                            "Detected local module 'supabase' at %s "
                            "which shadows the installed package.",
                            origin_abs,
                        )
                        logger.error(
                            "Remove or rename this file/folder and re-run "
                            "tests / watcher."
                        )
                        sys.exit(1)
            except Exception:
                # Defensive: any unexpected error inspecting the fake module
                # should not break tests; fall through and attempt to use it.
                pass

            create_fn = getattr(supa_mod, "create_client", None)
            if create_fn is None:
                logger.error(
                    "The 'supabase' module present in sys.modules "
                    "does not expose 'create_client'."
                )
                logger.error(
                    "If this is a test, ensure your fake module "
                    "provides 'create_client'."
                )
                sys.exit(1)

            _supabase_create_client = create_fn
            return _supabase_create_client

        # No preloaded module in sys.modules — fall back to importing the
        # real package. If it is missing, fail loudly with a helpful message.
        try:
            # This will call the import machinery and raise ImportError if
            # the package is not available or tests have patched __import__.
            from supabase import create_client as create_fn
        except ImportError:
            logger.error(
                "supabase-py is not installed. Install it with: pip install supabase\n"
                "See .collab/.env.example for required environment variables."
            )
            sys.exit(1)

        # After a successful import, detect if the resolved module originates
        # from the repository (e.g. .collab/supabase.py) which would indicate
        # an accidental shadowing of the real package.
        supa_mod = sys.modules.get("supabase")
        spec_origin = None
        if supa_mod is not None:
            spec = getattr(supa_mod, "__spec__", None)
            spec_origin = getattr(spec, "origin", None) if spec else None

        if supa_mod is not None:
            origin = spec_origin or getattr(supa_mod, "__file__", None)
        else:
            origin = None

        try:
            if origin:
                origin_abs = os.path.abspath(origin)
                if origin_abs.startswith(_COLLAB_ROOT):
                    logger.error(
                        "Detected local module 'supabase' at %s "
                        "which shadows the installed package.",
                        origin_abs,
                    )
                    logger.error(
                        "Remove or rename this file/folder and re-run "
                        "tests / watcher."
                    )
                    sys.exit(1)
        except Exception:
            pass

        _supabase_create_client = create_fn
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
    # Log the permanent failure with full traceback so operators can diagnose
    # why retries exhausted (e.g. DNS resolution errors). Use logger.exception
    # to ensure the stacktrace is written to .collab/logs/errors.log.
    logger.exception("Permanent network failure after %d attempts", MAX_RETRIES)
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

    def __init__(
        self, developer_id: Optional[str] = None, local_only: bool = False
    ) -> None:
        from typing import cast

        if not local_only:
            _validate_credentials()
        self.developer_id = developer_id or self._get_git_username()

        self._client = cast(Any, None)
        if not local_only:
            create_client = _get_create_client()
            key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
            self._client = cast(Any, create_client(SUPABASE_URL, key))

        self._parent_pid: Optional[int] = None
        self._is_admin: bool = bool(SUPABASE_SERVICE_ROLE_KEY)
        # Treat certain developer ids as ephemeral (e.g. CI/test accounts) so
        # they do not persist locks to the DB. This list is enforced in-code to
        # prevent arbitrary opt-outs via environment variables.
        # Determine if this developer id is ephemeral (CI/test prefixes)
        self._is_ephemeral: bool = False
        if self.developer_id:
            try:
                for p in EPHEMERAL_PREFIXES:
                    if self.developer_id.startswith(p):
                        self._is_ephemeral = True
                        break
            except Exception:
                # Defensive: if developer_id is not a str for any reason
                self._is_ephemeral = False

    def _normalize_file_path(self, file_path: str) -> str:
        """Normalize a file path to a project-root relative Unix-style path.

        This ensures that paths stored in Supabase match the paths produced by "git
        status --porcelain" (which are relative paths with forward slashes).
        """
        try:
            # If an absolute path was provided, make it relative to project root
            if os.path.isabs(file_path):
                rel = os.path.relpath(file_path, _PROJECT_ROOT)
            else:
                rel = file_path
            # Normalise separators to forward-slash for consistency in the DB
            rel = rel.replace("\\", "/")
            if rel.startswith("./"):
                rel = rel[2:]

            # Canonicalise collab/ -> .collab/ if it looks like a path mismatch.
            # We check for the presence of .collab directory to be safe.
            if rel.startswith("collab/"):
                rel = "." + rel
            return rel
        except Exception:
            return file_path.replace("\\", "/")

    @property
    def is_admin(self) -> bool:
        """Return True if this client has admin privileges (service role key)."""
        return self._is_admin

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
        # Local validation — accept either project-relative or absolute paths.
        full_path = (
            file_path
            if os.path.isabs(file_path)
            else os.path.join(_PROJECT_ROOT, file_path)
        )
        if not os.path.exists(full_path):
            return False, f"File or directory does not exist locally: {file_path}"

        # Ephemeral developer IDs do not persist locks to the backend
        # (useful for CI/test users). Short-circuit and return a local token.
        if getattr(self, "_is_ephemeral", False):
            token = f"ephemeral-{uuid.uuid4()}"
            logger.info(
                "🔒 [EPHEMERAL] %s (not persisted) — owner=%s",
                file_path,
                self.developer_id,
            )
            return True, token

        branch = branch_name or self._get_current_branch()
        token = str(uuid.uuid4())

        # Do not send expires_at: the RPC and DB intentionally ignore
        # time-based expiry. This keeps acquisition atomic while ensuring
        # locks persist until explicitly released.
        # Normalize the stored file_path so the watcher and dashboard see the
        # same canonical (project-relative, forward-slash) path.
        rpc_params = {
            "p_file_path": self._normalize_file_path(file_path),
            "p_developer_id": self.developer_id,
            "p_branch_name": branch,
            "p_reason": reason,
            "p_lock_token": token,
            "p_is_ephemeral": bool(getattr(self, "_is_ephemeral", False)),
        }

        assert self._client is not None, "Supabase client not initialized"
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
        # If ephemeral, nothing was persisted so there's nothing to delete.
        if getattr(self, "_is_ephemeral", False):
            logger.info(
                "🔓 [EPHEMERAL-RELEASE] %s (no-op for %s)", file_path, self.developer_id
            )
            return True, "ephemeral-released"

        assert self._client is not None, "Supabase client not initialized"
        try:
            norm = self._normalize_file_path(file_path)
            res = _retry_on_network_error(
                lambda: (
                    self._client.table("file_locks")
                    .delete()
                    .eq("file_path", norm)
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
        assert self._client is not None, "Supabase client not initialized"
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
        assert self._client is not None, "Supabase client not initialized"
        try:
            norm = self._normalize_file_path(file_path)
            res = _retry_on_network_error(
                lambda: (
                    self._client.table("file_locks")
                    .select("*")
                    .eq("file_path", norm)
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

        # With server-side expiry disabled, a present row implies an active
        # lock until it is explicitly released. Do not expose expires_at — it
        # was removed from the schema and is treated as audit-only historically.
        return {
            "is_locked": True,
            "locked_by": lock.get("developer_id"),
            "acquired_at": lock.get("acquired_at"),
            "reason": lock.get("reason"),
            "can_edit": lock.get("developer_id") == self.developer_id,
        }

    def release_all(self) -> int:
        """Release all locks held by this developer.

        Returns count released.
        """
        locks = self.active()
        my_locks = [lk for lk in locks if lk.get("developer_id") == self.developer_id]
        count = 0
        for lk in my_locks:
            ok, _ = self.release(lk.get("file_path", ""))
            if ok:
                count += 1
        return count

    def force_release(self, file_path: str) -> Tuple[bool, str]:
        """Force-release a lock on file_path.

        Non-admin users can only force-release their own locks. Admin users (with
        SUPABASE_SERVICE_ROLE_KEY) can force-release any lock.

        Returns (success: bool, message: str).
        """
        if not self._is_admin:
            # Non-admin: verify the lock belongs to this developer
            status_info = self.get_lock_status(file_path)
            if (
                status_info.get("is_locked")
                and status_info.get("locked_by") != self.developer_id
            ):
                owner = status_info.get("locked_by", "another developer")
                return False, (
                    f"Permission denied: {file_path} is locked by @{owner}. "
                    "Only admins can force-release other developers' locks."
                )

        try:
            query = self._client.table("file_locks").delete().eq("file_path", file_path)
            if not self._is_admin:
                query = query.eq("developer_id", self.developer_id)
            res = _retry_on_network_error(lambda: query.execute())
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
        """Acquire locks for multiple files.

        Returns (all_ok, failed_paths, message).
        """
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
        """Release locks for multiple files.

        Returns (ok, count, message).
        """
        count = 0
        for fp in file_paths:
            ok, _ = self.release(fp)
            if ok:
                count += 1
        return True, count, "Success"

    def history(self, file_path: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Fetch lock history records.

        When *file_path* is provided, an exact match is tried first.  If that
        returns nothing, a ``LIKE %<basename>%`` fallback query runs so the user
        does not have to remember the full stored path.
        """
        try:
            q = self._client.table("file_locks_history").select("*")
            if file_path:
                q = q.eq("file_path", file_path)
            q = q.order("id", desc=True).limit(limit)
            res = q.execute()
        except Exception as exc:
            logger.error("Failed to fetch lock history: %s", exc)
            return []

        _, data, error = self._parse_response(res)
        if error:
            logger.error("History query error: %s", error)
            return []
        rows = data or []

        # Fallback: if exact match returned nothing, try a partial match
        if not rows and file_path:
            try:
                basename = file_path.replace("\\", "/").rsplit("/", 1)[-1]
                q2 = (
                    self._client.table("file_locks_history")
                    .select("*")
                    .ilike("file_path", f"%{basename}%")
                    .order("id", desc=True)
                    .limit(limit)
                )
                res2 = q2.execute()
                _, data2, error2 = self._parse_response(res2)
                if not error2 and data2:
                    rows = data2
            except Exception:
                pass  # Fallback is best-effort

        return rows

    # ------------------------------------------------------------------
    # Daemon management
    # ------------------------------------------------------------------
    def daemon_start(
        self, interval: int = 5, timeout_mins: int = 0, open_dashboard: bool = False
    ) -> None:
        """Start the watcher as a background daemon process."""
        pid = self._read_pid()
        if pid and self._is_process_alive(pid):
            # Try to verify the PID metadata (entrypoint) first; prefer the
            # entrypoint field when present because background starters write
            # a human-friendly entrypoint. If the PID file is the legacy plain
            # integer format we intentionally *do not* treat a cmdline mismatch
            # as proof of staleness. Older clients wrote only the PID and users
            # expect the watcher to be considered running when that PID is
            # still alive (even if we can't reconstruct the exact cmdline).
            entrypoint = None
            had_metadata = False
            try:
                if os.path.exists(PID_FILE):
                    with open(PID_FILE, "r", encoding="utf-8") as fh:
                        raw = fh.read().strip()
                    if raw.startswith("{"):
                        had_metadata = True
                        obj = json.loads(raw)
                        entrypoint = obj.get("entrypoint")
            except Exception:
                entrypoint = None

            if entrypoint:
                print(f"Watcher already running (PID: {pid}) — {entrypoint}")
                return

            # If we have no richer metadata (legacy plain-PID) be conservative:
            # - If the PID matches the current process, consider it running.
            # - Otherwise try to verify the cmdline (if available) and only
            #   treat as running when it matches or cannot be determined.
            if not had_metadata:
                if pid == os.getpid():
                    print(f"Watcher already running (PID: {pid})")
                    return
                cmdline = self._get_cmdline_for_pid(pid)
                if cmdline:
                    if self._cmdline_matches_watcher(cmdline):
                        print(f"Watcher already running (PID: {pid})")
                        return
                    # cmdline present but doesn't match -> consider stale
                    # and continue to start a new watcher
                else:
                    # cmdline unavailable -> assume running to avoid false
                    # positives in restricted environments
                    print(f"Watcher already running (PID: {pid})")
                    return

            # Fallback: try to verify the process command-line to avoid
            # starting a duplicate when we do have metadata to inspect.
            cmdline = self._get_cmdline_for_pid(pid)
            if cmdline and self._cmdline_matches_watcher(cmdline):
                print(f"Watcher already running (PID: {pid})")
                return
            # If cmdline doesn't match, continue and start a new watcher

        print("Starting lock watcher in background...")
        cmd = [
            sys.executable,
            os.path.join(_COLLAB_ROOT, "core", "lock_client.py"),
            "watch",
            "--interval",
            str(interval),
            "--timeout",
            str(timeout_mins),
            "--daemon",
        ]
        if open_dashboard:
            cmd.append("--open-dashboard")

        if sys.platform == "win32":
            _logs_dir = os.path.join(_COLLAB_ROOT, "logs")
            os.makedirs(_logs_dir, exist_ok=True)
            log_path = os.path.join(_logs_dir, "application.log")
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
            print(f"❌ Watcher process (PID: {proc.pid}) exited immediately.")
            return

        print(f"✅ Started (PID: {proc.pid})")

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
        print("✅ Stopped.")

    def daemon_status(self) -> bool:
        """Check if the watcher daemon is running.

        Checks both the primary PID file and the legacy PyCharm watcher PID file for
        backward compatibility.
        """
        pid = self._read_pid()
        if pid and self._is_process_alive(pid):
            # Attempt to read PID metadata (entrypoint) and prefer it for
            # human-facing output when available. When the PID file is the
            # legacy plain-integer format we avoid strict cmdline verification
            # to reduce false negatives in environments where reconstructing
            # a cmdline is unreliable (tests, limited containers, etc.).
            entrypoint: Optional[str] = None
            had_metadata = False
            try:
                if os.path.exists(PID_FILE):
                    with open(PID_FILE, "r", encoding="utf-8") as fh:
                        raw = fh.read().strip()
                    if raw.startswith("{"):
                        had_metadata = True
                        obj = json.loads(raw)
                        entrypoint = obj.get("entrypoint")
            except Exception:
                entrypoint = None

            # If an entrypoint is present in the PID metadata, prefer it.
            if entrypoint:
                print(f"✅ Lock watcher is RUNNING (PID: {pid}) — {entrypoint}")
                return True

            # If we have no richer metadata (legacy plain-PID) preserve the
            # historical, lenient behaviour: older clients only wrote an integer PID
            # and callers expect a live PID to indicate the watcher is running.
            # Do NOT mark such PIDs stale solely because the reconstructed
            # command-line doesn't match — this avoids false negatives in tests
            # and constrained environments where cmdline inspection is unreliable.
            if not had_metadata:
                # If this is the legacy plain-PID file, preserve the historical
                # behavior: if the PID matches the current process, confidently
                # report running. Otherwise fall through and attempt a
                # best-effort cmdline verification below to avoid treating an
                # unrelated process as the watcher.
                if pid == os.getpid():
                    print(f"✅ Lock watcher is RUNNING (PID: {pid}) (cmdline unknown)")
                    return True

            # Fallback: try to verify the process command-line to avoid false positives
            cmdline = self._get_cmdline_for_pid(pid)
            if cmdline:
                if not self._cmdline_matches_watcher(cmdline):
                    # PID belongs to some other process; treat as stale
                    print(
                        f"❌ Lock watcher PID file points to PID {pid} "
                        "but command-line doesn't match."
                    )
                    logger.debug("PID %d cmdline: %s", pid, cmdline)
                    self._remove_pid()
                    return False
                print(f"✅ Lock watcher is RUNNING (PID: {pid}) — {cmdline}")
            else:
                # Can't verify cmdline — assume running
                print(f"✅ Lock watcher is RUNNING (PID: {pid}) (cmdline unknown)")
            return True
        # Fallback: check legacy PyCharm watcher PID file
        _legacy_pid_file = os.path.join(_COLLAB_ROOT, ".pycharm_watcher.pid")
        if os.path.exists(_legacy_pid_file):
            try:
                with open(_legacy_pid_file, "r") as f:
                    legacy_pid = int(f.read().strip())
                if self._is_process_alive(legacy_pid):
                    print(f"✅ Lock watcher is RUNNING (PID: {legacy_pid})")
                    return True
            except (ValueError, OSError):
                pass
        print("❌ Lock watcher is NOT running.")
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
            RequestHandler = http.server.SimpleHTTPRequestHandler
            RequestHandler.log_message = lambda *a, **k: None  # type: ignore  # noqa

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
        self,
        interval: int = 5,
        timeout_mins: int = 0,
        open_dashboard: bool = False,
        daemon_mode: bool = False,
    ) -> None:
        """Run the file-watching loop (foreground).

        Called by daemon_start.  When *daemon_mode* is True the parent-PID liveness
        check is skipped (detached daemons have no meaningful parent).
        """
        # Ensure file-based logging is wired so watch output goes to logs/
        from logging_config import setup_collab_logging

        setup_collab_logging(collab_dir=_COLLAB_ROOT)

        if not daemon_mode:
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
        timeout_label = f"{timeout_mins}m" if timeout_mins > 0 else "disabled"
        logger.info("Interval: %ds | Auto-timeout: %s", interval, timeout_label)
        logger.info("Monitoring local git changes for automatic locking...")

        last_modified: set = set()
        last_change_time = _safe_now()
        last_reconcile_time = _safe_now()
        last_parent_check = _safe_now()

        last_modified = self._reconcile()

        try:
            while True:
                try:
                    # Parent process liveness check every 30 seconds
                    # (skipped in daemon mode — detached processes have
                    # no meaningful parent PID)
                    if (
                        not daemon_mode
                        and (_safe_now() - last_parent_check).total_seconds() > 30
                    ):
                        last_parent_check = _safe_now()
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
                                path = self._normalize_file_path(
                                    self._parse_git_status_path(line)
                                )
                                if not self._should_ignore_path(path):
                                    current_modified.add(path)

                    if current_modified != last_modified:
                        last_change_time = _safe_now()
                        new_files = current_modified - last_modified
                        if new_files:
                            ts = _safe_now().strftime("%H:%M:%S")
                            logger.info("[%s] Detected: %s", ts, list(new_files))
                            branch = self._get_current_branch()
                            ok, failed, msg = self.acquire_multiple(
                                list(new_files),
                                branch_name=branch,
                                reason="Auto-Watch Sync",
                            )
                            if ok:
                                logger.info("🔒 Locked: %s", list(new_files))
                            else:
                                logger.warning("⚠️ CONFLICT ALERT: %s", msg)

                        released = last_modified - current_modified
                        if released:
                            ts = _safe_now().strftime("%H:%M:%S")
                            logger.info("[%s] Finalised: %s", ts, list(released))
                            ok, count, _ = self.release_multiple(list(released))
                            if ok and count > 0:
                                logger.info("🔓 Released: %d file(s)", count)

                        last_modified = current_modified
                    else:
                        # Periodic reconciliation
                        if (_safe_now() - last_reconcile_time) > timedelta(minutes=15):
                            last_modified = self._reconcile()
                            last_reconcile_time = _safe_now()

                        # Idle timeout
                        idle = _safe_now() - last_change_time
                        if timeout_mins > 0 and idle > timedelta(minutes=timeout_mins):
                            logger.info(
                                "Watcher timed out after %dm inactivity.", timeout_mins
                            )
                            break

                    time.sleep(interval)
                except Exception as e:
                    logger.error("Error in watcher loop: %s", e, exc_info=True)
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
        if os.getenv("COLLAB_TEST_MODE") != "1":
            atexit.register(self._graceful_shutdown)

        def _handle_signal(signum, frame):
            logger.info("Received signal %d, shutting down...", signum)
            self._graceful_shutdown()
            sys.exit(0)

        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

    def _graceful_shutdown(self) -> None:
        """Release all locks and clean up PID file.

        Guarded so it runs at most once per instance, even when called from multiple
        shutdown paths (signal, finally, atexit).
        """
        if getattr(self, "_shutdown_done", False):
            return
        self._shutdown_done = True

        # Never touch real Supabase OR local PID file in test mode to avoid
        # interfering with the live production environment.
        if os.getenv("COLLAB_TEST_MODE") == "1":
            return

        try:
            count = self.release_all()
            if count > 0:
                logger.info("✅ Released %d lock(s) during shutdown.", count)
        except Exception:
            # Ensure full traceback is captured for shutdown failures
            logger.exception("Error releasing locks during shutdown")
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
            return (
                subprocess.check_output(
                    args, stderr=subprocess.DEVNULL, creationflags=0x08000000
                )
                .decode()
                .strip()
            )
        else:
            return (
                subprocess.check_output(args, stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )

    @staticmethod
    def _parse_git_status_path(line: str) -> str:
        """Extract file path from git status --porcelain, handling renames."""
        p = line[3:].strip()
        if " -> " in p:
            p = p.split(" -> ")[-1].strip()
        if p.startswith('"') and p.endswith('"'):
            p = p[1:-1]
            try:
                p = p.encode("utf-8").decode("unicode_escape")
            except Exception:
                pass
        return p

    @staticmethod
    def _should_ignore_path(path: str) -> bool:
        """Return True for paths the watcher should skip."""
        norm = path.replace("\\", "/")
        if "/.git/" in norm or norm.startswith(".git/"):
            return True
        # Do not ignore `.collab/` paths — watcher and client will handle
        # editor/IDE metadata appropriately. Only .git is ignored here.
        return False

    @staticmethod
    def _read_pid() -> Optional[int]:
        """Read daemon PID from the PID file.

        Supports two formats for backward compatibility:
        - Plain integer stored in `.daemon.pid` (legacy)
        - JSON object stored in `.daemon.pid` containing a numeric "pid" field

        Returns the pid as an int, or None if the file is missing or malformed.
        """
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            if not raw:
                return None
            # Try JSON first (richer metadata), fall back to int
            if raw.startswith("{"):
                try:
                    obj = json.loads(raw)
                    pid = obj.get("pid")
                    if isinstance(pid, int):
                        return pid
                except Exception:
                    logger.debug("PID file contains invalid JSON: %s", raw)
                    return None
            # Fallback: plain integer
            return int(raw)
        except ValueError:
            logger.debug("PID file does not contain an integer: %s", PID_FILE)
            return None
        except OSError as e:
            logger.debug("Could not read PID file %s: %s", PID_FILE, e)
            return None

    @staticmethod
    def _get_cmdline_for_pid(pid: int) -> Optional[str]:
        """Return the command-line string for a process, or None if unavailable.

        Uses psutil when available. If psutil is not installed or access fails, returns
        None which indicates we couldn't verify the cmdline.
        """
        # Prefer psutil when available (robust cross-platform). If unavailable,
        # fall back to lightweight platform-specific methods (procfs on Unix,
        # WMIC/tasklist on Windows) so we can verify PID command-lines even
        # in minimal environments.
        try:
            import psutil

            try:
                p = psutil.Process(pid)
                cmd = p.cmdline()
                if isinstance(cmd, (list, tuple)):
                    return " ".join(cmd)
                return str(cmd)
            except Exception:
                # If psutil fails for this PID, continue to fallbacks
                pass
        except Exception:
            # psutil not installed — continue to platform fallbacks
            pass

        # Platform-specific fallbacks
        if sys.platform == "win32":
            # Try WMIC (widely available on older Windows) to fetch CommandLine
            try:
                out = subprocess.check_output(
                    [
                        "wmic",
                        "process",
                        "where",
                        f"ProcessId={pid}",
                        "get",
                        "CommandLine",
                    ],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                # WMIC prints a header line; strip and return the joined remainder
                lines = [line.strip() for line in out.splitlines() if line.strip()]
                if len(lines) >= 2:
                    return " ".join(lines[1:]).strip()
            except Exception:
                pass
            # Try PowerShell CIM as a more modern fallback (works on recent Windows)
            try:
                cmd_str = (
                    '(Get-CimInstance Win32_Process -Filter "ProcessId=%d").'
                    "CommandLine" % pid
                )
                ps_cmd = ("-NoProfile", "-Command", cmd_str)
                out = subprocess.check_output(
                    ["powershell", *ps_cmd], stderr=subprocess.DEVNULL, text=True
                )
                out = out.strip()
                if out:
                    return out
            except Exception:
                pass
            # As a last resort on Windows we cannot reliably get a cmdline
            return None
        else:
            # Unix-like systems: read /proc/<pid>/cmdline if available
            proc_path = f"/proc/{pid}/cmdline"
            try:
                if os.path.exists(proc_path):
                    with open(proc_path, "rb") as fh:
                        data = fh.read()
                        if not data:
                            return None
                        # cmdline entries are null-separated
                        raw_parts = data.split(b"\x00")
                        parts = [
                            part.decode(errors="replace") for part in raw_parts if part
                        ]
                        return " ".join(parts)
            except Exception:
                pass
            return None

    @staticmethod
    def _cmdline_matches_watcher(cmdline: str) -> bool:
        """Heuristic: return True if the command-line looks like our watcher.

        Matches the two supported watcher entrypoints:
        - `.collab/pycharm/live_locks_watcher.py`
        - `lock_client.py watch` (the lock_client watch subcommand)
        """
        if not cmdline:
            return False
        s = cmdline.lower()
        return (
            "live_locks_watcher" in s
            or ("lock_client.py" in s and "watch" in s)
            or ("collab.core.lock_client" in s and "watch" in s)
        )

    @staticmethod
    def _write_pid(pid: int) -> None:
        """Write daemon PID metadata to the PID file as JSON.

        Historically this file contained a plain integer.  Newer clients write a small
        JSON object with fields useful for diagnostics.  The reader already supports
        both formats for backward compatibility.
        """
        meta = {
            "pid": int(pid),
            # Use _safe_now to accommodate tests that monkeypatch the module
            # level `datetime` symbol. Ensure the stored time is in UTC.
            "started_at": _safe_now().astimezone(timezone.utc).isoformat(),
            # Use a human-friendly entrypoint string so other tools can display
            # a concise description without reconstructing the full cmdline.
            "entrypoint": "python lock_client.py",
            "cmdline": " ".join([sys.executable] + sys.argv),
            "cwd": os.getcwd(),
        }
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(json.dumps(meta))
        except OSError as e:
            logger.warning("Could not write PID file: %s", e)

    @staticmethod
    def _remove_pid() -> None:
        """Remove the PID file if it exists.

        Suppressed in COLLAB_TEST_MODE to prevent test processes from accidentally
        deleting the production watcher's PID file.
        """
        if os.getenv("COLLAB_TEST_MODE") == "1":
            return

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
    # Force UTF-8 on Windows so Unicode symbols (✓, ❌, 🔒) render correctly.
    # Mirrors the proven pattern from validate_code.py, format_code.py, run.py.
    # errors="replace" ensures graceful fallback if the terminal truly cannot
    # handle a character (e.g. bare cmd.exe with cp437).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    # Wire up file-based logging early so all CLI output is captured.
    if _COLLAB_ROOT not in sys.path:
        sys.path.insert(0, _COLLAB_ROOT)
    from logging_config import setup_collab_logging

    setup_collab_logging(collab_dir=_COLLAB_ROOT)

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
    fr = sub.add_parser(
        "force-release",
        help="Force release a lock (own locks only; admin can release any)",
    )
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
    ds.add_argument("--interval", type=int, default=5, help="Poll interval (seconds)")
    ds.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Idle timeout in minutes (0 = disabled)",
    )
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
    hp.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as raw JSON"
    )

    # watch (internal, called by daemon-start)
    wp = sub.add_parser("watch", help="Run watcher in foreground")
    wp.add_argument("--interval", type=int, default=5)
    wp.add_argument("--timeout", type=int, default=0)
    wp.add_argument("--open-dashboard", action="store_true")
    wp.add_argument(
        "--daemon",
        action="store_true",
        help="Daemon mode: skip parent-PID liveness check",
    )

    args = parser.parse_args()
    local_only = args.command in ("daemon-status", "daemon-stop")
    client = LockClient(local_only=local_only)

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
                f"🔒 Locked by @{info.get('locked_by')} since {info.get('acquired_at')}"
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
        client.daemon_start(
            interval=getattr(args, "interval", 5),
            timeout_mins=getattr(args, "timeout", 0),
            open_dashboard=(open_flag or auto_env),
        )

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
        fp = getattr(args, "file_path", None)
        rows = client.history(fp, limit=getattr(args, "limit", 20))
        if getattr(args, "json_output", False):
            print(json.dumps(rows, indent=2))
        elif not rows:
            if fp:
                print(f"No history found for '{fp}'.")
                print("  Tip: run 'python collab.py history' (no file) to see all.")
            else:
                print("No lock history found.")
        else:
            # Check if results came from fallback (partial match)
            if fp and rows and rows[0].get("file_path") != fp:
                actual = rows[0].get("file_path", "")
                print(
                    f"  (No exact match for '{fp}' — "
                    f"showing partial matches for '{actual.rsplit('/', 1)[-1]}')\n"
                )
            for row in rows:
                acquired = row.get("acquired_at", "?")[:19].replace("T", " ")
                released = row.get("released_at", "?")[:19].replace("T", " ")
                dev = row.get("developer_id", "?")
                fpath = row.get("file_path", "?")
                branch = row.get("branch_name", "")
                outcome = row.get("outcome", "?")
                print(
                    f"  {fpath}  @{dev}  "
                    f"[{acquired} → {released}]  "
                    f"branch:{branch}  {outcome}"
                )

    elif args.command == "watch":
        client.watch(
            interval=getattr(args, "interval", 5),
            timeout_mins=getattr(args, "timeout", 0),
            open_dashboard=getattr(args, "open_dashboard", False),
            daemon_mode=getattr(args, "daemon", False),
        )

    else:
        parser.print_help()


def main():
    """Entry point for ``python -m .collab.core.lock_client``."""
    try:
        _run_cli()
    except Exception as exc:
        import traceback as _tb

        tb_str = _tb.format_exc()
        # Log to standard .collab/logs/ via the structured logger
        logger.error("Unhandled exception: %s\n%s", exc, tb_str)
        print(
            "FATAL: lock_client crashed \u2014 see .collab/logs/errors.log",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
