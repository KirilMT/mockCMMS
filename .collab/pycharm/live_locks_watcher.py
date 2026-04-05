"""Standalone lock watcher for PyCharm and other IDEs.

Monitors local git status and subscribes to Supabase Realtime for
collaborative file lock notifications. Uses plyer for cross-platform
desktop notifications.

Usage:
    python .collab/pycharm/live_locks_watcher.py [--interval 5] [--timeout 0]
"""

from __future__ import annotations

import atexit
import importlib
import importlib.util
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# Optional colored output (avoid try/except to reduce unreachable-branch lines)
_HAS_COLORAMA = False
try:
    _colorama_spec = importlib.util.find_spec("colorama")
except Exception:
    _colorama_spec = None
if _colorama_spec is not None:
    colorama_mod = importlib.import_module("colorama")
    Fore = getattr(colorama_mod, "Fore")
    Style = getattr(colorama_mod, "Style")
    _colorama_init = getattr(colorama_mod, "init", None)
    if callable(_colorama_init):
        try:
            _colorama_init()
        except Exception:
            pass
    _HAS_COLORAMA = True

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

# Reduce noisy HTTP client logs (Supabase client uses httpx under the hood)
for _noisy in ("httpx", "httpx._client", "urllib3", "asyncio"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

# Type annotation: allow create_client to be None until we bind the real factory.
create_client: Optional[Callable[..., Any]] = None

try:
    _supa_spec = importlib.util.find_spec("supabase")
except Exception:
    _supa_spec = None
if _supa_spec is None:
    logger.error("supabase not installed. Run: pip install supabase")
    sys.exit(1)
else:
    _supa = importlib.import_module("supabase")
    create_client = getattr(_supa, "create_client")

try:
    _ply_spec = importlib.util.find_spec("plyer")
except Exception:
    _ply_spec = None
if _ply_spec is None:
    desktop_notify = None
    logger.warning(
        "plyer not installed — desktop notifications disabled. "
        "Run: pip install plyer"
    )
else:
    _ply = importlib.import_module("plyer")
    desktop_notify = getattr(_ply, "notification", None)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PID_FILE = os.path.join(_COLLAB_ROOT, ".daemon.pid")
DEVELOPER_ID = None

# Ephemeral developer prefixes enforced in code (not via env) to avoid
# accidental disabling of lock persistence. These accounts (e.g. CI/test)
# will not write locks to the remote DB and are used by automated runners.
EPHEMERAL_PREFIXES = ["test_dev", "ci"]

# Expiry semantics: disabled. The DB RPC ignores time-based expiry and locks
# persist until explicitly released. The watcher does not send an expires_at
# value when acquiring locks.

# Track files currently in conflict (locked by another dev)
_active_conflicts: set[str] = set()
# Track remote locks we already warned about (avoid duplicate notifications)
_warned_remote_locks: set[str] = set()
# Track all remote locks last seen (used to surface any add/remove activity)
_known_remote_locks: set[str] = set()
# Track locks this watcher process has acquired locally (avoid duplicate notices)
_local_owned_locks: set[str] = set()
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
    # Do not ignore `.collab/` — watcher should consider files under it.
    return False


def _color(text: str, color: str) -> str:
    if not _HAS_COLORAMA:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def _is_ephemeral_dev(dev_id: Optional[str]) -> bool:
    if not dev_id:
        return False
    for p in EPHEMERAL_PREFIXES:
        if dev_id.startswith(p):
            return True
    return False


# (No _compute_expires_at) - watcher intentionally does not compute or send
# expires_at. The DB handles locks as persistent until release.


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
    # Only rebind `_known_remote_locks` in this function; the other sets are
    # mutated in-place (add/discard) so they do not need a `global` declaration.
    global _known_remote_locks

    try:
        res = client.table("file_locks").select("*").execute()
        data = getattr(res, "data", None) or []
    except Exception as exc:
        logger.debug("Remote lock scan failed: %s", exc)
        return

    # Build set of all remote file paths (normalize separators) and map full lock rows
    current_remote_all: set[str] = set()
    owner_map: dict[str, dict] = {}
    for lock in data:
        owner = lock.get("developer_id", "")
        fp = lock.get("file_path", "")
        if not fp:
            continue
        fp = fp.replace("\\", "/")
        current_remote_all.add(fp)
        owner_map[fp] = lock

        # If this watcher already acquired this lock locally, skip notifications
        if owner == DEVELOPER_ID and fp in _local_owned_locks:
            continue

        # If the lock belongs to the same developer but a different session,
        # surface it as a normal locked message (not a conflict) and include
        # metadata (owner, branch, reason) so terminal output mirrors
        # `python collab.py active`.
        if owner == DEVELOPER_ID:
            if fp not in _known_remote_locks:
                br = lock.get("branch_name") or "main"
                reason = lock.get("reason") or "No reason"
                msg = f"🔒 [LOCKED] {fp} — @{owner} (branch: {br}, reason: {reason})"
                logger.info(_color(msg, Fore.GREEN) if _HAS_COLORAMA else msg)
            continue

        # For locks owned by others: warn once per lock and include branch/reason
        if owner != DEVELOPER_ID and fp not in _warned_remote_locks:
            _warned_remote_locks.add(fp)
            br = lock.get("branch_name") or "main"
            reason = lock.get("reason") or "No reason"
            warn_msg = (
                f"⚠️ REMOTE LOCK: {fp} — @{owner} (branch: {br}, reason: {reason})"
            )
            logger.warning(warn_msg)
            notify_msg = (
                f"{fp} is locked by @{owner}.\n"
                f"branch: {br}\n"
                f"reason: {reason}\n"
                "Coordinate before editing."
            )
            _notify("File Locked", notify_msg)

    # Clear warnings for locks that were released remotely
    released_warned = _warned_remote_locks - current_remote_all
    if released_warned:
        _warned_remote_locks.difference_update(released_warned)
        for fp in released_warned:
            logger.info("✅ Remote lock cleared: %s", fp)

    # Surface add/remove activity for remote locks (excluding those owned
    # by this watcher which we suppressed above). Do not re-report locks
    # that we already logged above (same-developer) — filter them out.
    added = current_remote_all - _known_remote_locks
    removed = _known_remote_locks - current_remote_all
    # Filter out additions that correspond to locks we just acquired locally
    # or locks owned by this developer (they were already logged as LOCKED).
    # Filter out additions that correspond to locks we just acquired locally
    # or locks owned by this developer (they were already logged as LOCKED).
    # NOTE: owner_map stores the full lock dict, so compare the stored
    # developer_id field rather than the dict object itself (bugfix).
    filtered_added = {
        p
        for p in added
        if p not in _local_owned_locks
        and (owner_map.get(p, {}).get("developer_id") != DEVELOPER_ID)
    }
    if filtered_added:
        for fp in sorted(filtered_added):
            lk = owner_map.get(fp, {})
            owner = lk.get("developer_id") if lk else "unknown"
            br = lk.get("branch_name") if lk else None
            reason = lk.get("reason") if lk else None
            br = br or "main"
            reason = reason or "No reason"
            # Remote additions should be highlighted so they stand out in the
            # terminal. Use yellow when colorama is available (matches
            # WARNING/CONFLICT color), otherwise plain info text.
            msg = (
                f"🔔 Remote lock added: {fp} — @{owner} "
                f"(branch: {br}, reason: {reason})"
            )
            log_msg = _color(msg, Fore.YELLOW) if _HAS_COLORAMA else msg
            logger.info(log_msg)
    if removed:
        for fp in sorted(removed):
            # If we had recorded it locally, ensure it's removed from that set
            if fp in _local_owned_locks:
                _local_owned_locks.discard(fp)
            # Use the same RELEASED log style as the watcher uses for local releases
            release_msg = f"🔓 [RELEASED] {fp}"
            # Use a distinct color for remote releases so they are visually
            # different from local releases in the terminal output.
            log_msg = _color(release_msg, Fore.CYAN) if _HAS_COLORAMA else release_msg
            logger.info(log_msg)
    _known_remote_locks = current_remote_all


def _process_new_files(client, branch: str, new_files: set[str]) -> None:
    """Process newly modified files: attempt to acquire locks and handle conflicts.

    Extracted from the main loop so unit tests can target error/fallback
    branches (e.g. when modifying the local-owned set raises).
    """
    for fp in new_files:
        try:
            if _is_ephemeral_dev(DEVELOPER_ID):
                msg = f"🔒 [EPHEMERAL] {fp} (not written to DB)"
                logger.info(_color(msg, Fore.CYAN) if _HAS_COLORAMA else msg)
                # skip remote RPC for ephemeral/dev prefixes
                continue

            res = client.rpc(
                "acquire_lock",
                {
                    "p_file_path": fp,
                    "p_developer_id": DEVELOPER_ID,
                    "p_branch_name": branch,
                    "p_reason": "Auto-Watch",
                    "p_lock_token": str(__import__("uuid").uuid4()),
                    "p_is_ephemeral": _is_ephemeral_dev(DEVELOPER_ID),
                },
            ).execute()
            data = getattr(res, "data", None) or []
            if isinstance(data, list) and data and data[0].get("status") == "conflict":
                owner = data[0].get("owner", "someone")
                _active_conflicts.add(fp)
                msg = (
                    f"⚠️ CONFLICT: {fp} is locked by @{owner} -- "
                    "your changes may cause a merge conflict."
                )
                log_msg = _color(msg, Fore.YELLOW) if _HAS_COLORAMA else msg
                logger.warning(log_msg)
                notify_msg = (
                    f"{fp} is locked by @{owner}.\n" "Coordinate before committing."
                )
                _notify("Lock Conflict", notify_msg)
            else:
                br_local = branch or "main"
                reason_local = "Auto-Watch"
                msg = (
                    f"🔒 [LOCKED] {fp} — @{DEVELOPER_ID} "
                    f"(branch: {br_local}, reason: {reason_local})"
                )
                log_msg = _color(msg, Fore.GREEN) if _HAS_COLORAMA else msg
                logger.info(log_msg)
                # Track locks this watcher created so remote scans do not
                # report them as 'remote added' later.
                try:
                    _local_owned_locks.add(fp)
                except Exception:
                    pass
        except Exception as e:
            logger.error("Failed to acquire lock for %s: %s", fp, e)


def _process_releases(client, released: set[str]) -> None:
    """Process local releases for files no longer modified.

    Extracted so tests can simulate exceptions when removing locks from the local-owned
    set without running the entire main loop.
    """
    for fp in released:
        # Was this file in conflict?
        if fp in _active_conflicts:
            _active_conflicts.discard(fp)
            msg = f"✅ Conflict cleared: {fp} (file reverted or resolved)"
            logger.info(_color(msg, Fore.BLUE) if _HAS_COLORAMA else msg)
        else:
            try:
                if _is_ephemeral_dev(DEVELOPER_ID):
                    logger.info("🔓 [EPHEMERAL-RELEASE] %s", fp)
                else:
                    client.table("file_locks").delete().eq("file_path", fp).eq(
                        "developer_id", DEVELOPER_ID
                    ).execute()
                    logger.info(
                        _color(f"🔓 [RELEASED] {fp}", Fore.MAGENTA)
                        if _HAS_COLORAMA
                        else f"[RELEASED] {fp}"
                    )
                    # If we released a lock we held locally, remove it
                    # from the local-owned set so remote scans don't keep it there.
                    try:
                        _local_owned_locks.discard(fp)
                    except Exception:
                        pass
            except Exception as e:
                logger.error("Failed to release lock for %s: %s", fp, e)


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
            logger.info("Removed PID file: %s", PID_FILE)
    except OSError:
        pass


def _write_pid_file(pid: int) -> None:
    """Atomically write JSON metadata to the PID file for daemon-status checks.

    Keeps process metadata to aid verification and diagnostics. Writes a JSON object
    containing pid, started_at (UTC ISO), cmdline and cwd.
    """
    meta = {
        "pid": pid,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "entrypoint": "pycharm-watcher",
        "cmdline": " ".join([sys.executable] + sys.argv),
        "cwd": os.getcwd(),
    }
    pid_dir = os.path.dirname(PID_FILE) or "."
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", delete=False, dir=pid_dir, suffix=".pid.tmp", encoding="utf-8"
        )
        tmp.write(json.dumps(meta))
        tmp.flush()
        tmp.close()
        os.replace(tmp.name, PID_FILE)
        logger.info("Wrote PID metadata to %s (PID: %d)", PID_FILE, pid)
    except Exception as exc:
        logger.warning("Failed to write PID metadata to %s: %s", PID_FILE, exc)
        if tmp is not None:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass


def _get_cmdline_for_pid_local(pid: int) -> Optional[str]:
    """Local helper to fetch a process command-line (psutil preferred, then platform-
    specific fallbacks)."""
    try:
        import psutil

        try:
            p = psutil.Process(pid)
            cmd = p.cmdline()
            if isinstance(cmd, (list, tuple)):
                return " ".join(cmd)
            return str(cmd)
        except Exception:
            pass
    except Exception:
        pass

    # Windows fallbacks
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                ["wmic", "process", "where", f"ProcessId={pid}", "get", "CommandLine"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            lines = [line.strip() for line in out.splitlines() if line.strip()]
            if len(lines) >= 2:
                return " ".join(lines[1:]).strip()
        except Exception:
            pass
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
        return None


def _cmdline_matches_watcher_local(cmdline: Optional[str]) -> bool:
    if not cmdline:
        return False
    s = cmdline.lower()
    return (
        "live_locks_watcher" in s
        or ("lock_client.py" in s and "watch" in s)
        or ("collab.core.lock_client" in s and "watch" in s)
    )


def _shorten_process_label(
    label: Optional[str], max_tokens: int = 4, max_len: int = 80
) -> Optional[str]:
    """Return a short, human-friendly label for a process/entrypoint string.

    - Collapse long filesystem paths to their basenames
    - Keep only the first `max_tokens` tokens and append ' ...' if truncated
    - Ensure the returned string is not longer than `max_len` (truncates with ellipsis)
    """
    if not label:
        return None
    try:
        parts = label.split()
        short_parts: list[str] = []
        for p in parts[:max_tokens]:
            # If it's a path-like token, show only the basename for readability
            if ("/" in p) or ("\\" in p):
                try:
                    b = os.path.basename(p)
                    if b:
                        short_parts.append(b)
                        continue
                except Exception:
                    pass
            # Normalize common python executable mention
            low = p.lower()
            if low.endswith("python") or low.endswith("python.exe") or "pythonw" in low:
                short_parts.append("python")
            else:
                short_parts.append(p)

        short = " ".join(short_parts)
        if len(parts) > max_tokens:
            short = short + " ..."
        if len(short) > max_len:
            short = short[: max_len - 3].rstrip() + "..."
        return short
    except Exception:
        # Best-effort: return the original label if shortening fails
        return label if label else None


def _existing_watcher_running() -> tuple[bool, int | None, str | None, str | None]:
    """Check for an existing watcher process via PID file and return (is_running, pid,
    cmdline, entrypoint).

    If no existing PID file or cannot verify, returns (False, None, None, None).
    """
    try:
        if not os.path.exists(PID_FILE):
            return (False, None, None, None)
        with open(PID_FILE, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()
        if not raw:
            return (False, None, None, None)
        pid = None
        cmdline = None
        entrypoint = None
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
                pid = obj.get("pid")
                cmdline = obj.get("cmdline")
                entrypoint = obj.get("entrypoint")
            except Exception:
                return (False, None, None, None)
        else:
            try:
                pid = int(raw)
            except Exception:
                return (False, None, None, None)

        if not pid:
            return (False, None, None, None)

        real_cmd = _get_cmdline_for_pid_local(pid)
        if real_cmd:
            cmdline = real_cmd
        if _cmdline_matches_watcher_local(cmdline):
            return (True, pid, cmdline, entrypoint)
        return (False, pid, cmdline, entrypoint)
    except Exception:
        return (False, None, None, None)


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
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (prints heartbeat and debug details)",
    )
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        logger.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env.\n"
            "See .collab/.env.example for setup."
        )
        sys.exit(1)

    DEVELOPER_ID = _get_developer_id()

    # Optional debug mode: enable verbose logging for diagnostics
    debug_mode = args.debug or os.getenv("COLLAB_DEBUG", "0").lower() in (
        "1",
        "true",
        "yes",
    )
    if debug_mode:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")

    # Write PID file (unified with lock_client daemon)
    # Startup guard: avoid starting a second watcher if one is already active
    running, existing_pid, existing_cmd, existing_entry = _existing_watcher_running()
    if running:
        # Prefer a stable human-facing label when the PID metadata contains an
        # entrypoint. Map well-known entrypoint tokens to a short, descriptive
        # process name so output is consistent for operators.
        label = None
        if existing_entry:
            e = str(existing_entry).lower()
            if e in ("lock-daemon", "lock-client"):
                # Prefer an explicit, familiar invocation instead of a short token
                label = "python lock_client.py"
            elif e == "pycharm-watcher":
                label = "python .collab/pycharm/live_locks_watcher.py"
            else:
                label = _shorten_process_label(existing_entry)
        elif existing_cmd:
            label = _shorten_process_label(existing_cmd)

        if label:
            first_line = f"Watcher already running (PID: {existing_pid}) — {label}."
        else:
            first_line = f"Watcher already running (PID: {existing_pid})."

        # Use multi-line info so the IDE/terminal shows each action on its own line
        msg = (
            first_line
            + "\nTo check status: python collab.py daemon-status\n"
            + "To stop: python collab.py daemon-stop"
        )
        logger.info(msg)
        # Avoid printing a duplicate concise line to the console — the logger
        # output is sufficient and prevents double messages in IDE Run windows.
        sys.exit(0)

    try:
        _write_pid_file(os.getpid())
    except Exception:
        # Best-effort: if writing metadata fails, fall back to plain PID integer
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
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
    if create_client is None:
        logger.error(
            "Supabase client factory is not available. Ensure supabase is installed."
        )
        sys.exit(1)
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
    last_heartbeat = datetime.now()

    # Initial remote lock scan
    _scan_remote_locks(client)

    try:
        while True:

            # Remote lock scan every 30 seconds (independent of git status)
            now = datetime.now()
            # Periodic heartbeat (helps diagnose silent exits)
            if (now - last_heartbeat).total_seconds() > 60:
                last_heartbeat = now
                logger.debug("heartbeat pid=%d", os.getpid())
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
                # Delegate acquire/release logic to helper functions to allow
                # targeted unit tests to exercise error/fallback branches.
                _process_new_files(client, branch, new_files)

                # Files no longer modified locally
                released = last_modified - current_modified
                _process_releases(client, released)

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
    try:
        main()
    except Exception as exc:  # top-level catch to ensure operator sees failures
        # Write full traceback to the daemon log for post-mortem analysis
        log_path = os.path.join(_COLLAB_ROOT, ".daemon.log")
        tb = traceback.format_exc()
        try:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(
                    "["
                    + datetime.now(timezone.utc).isoformat()
                    + "] Unhandled exception in live_locks_watcher: "
                    + str(exc)
                    + "\n"
                )
                fh.write(tb)
                fh.write("\n")
        except Exception:
            # best-effort logging only
            pass

        # Print short, operator-friendly message to stderr so it appears in
        # the IDE/terminal immediately, pointing to the full log for details.
        try:
            file_uri = Path(log_path).resolve().as_uri()
        except Exception:
            file_uri = log_path
        print(f"Unhandled error in watcher. See log: {file_uri}", file=sys.stderr)

        # Attempt graceful cleanup, then exit non-zero
        try:
            _graceful_shutdown()
        except Exception:
            pass
        sys.exit(1)
