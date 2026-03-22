"""lock_client.py.

Serverless Python client library for collaborative development. Uses a GitHub Gist as a
persistent backend for file locks.
"""

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

# Load .env for GITHUB_TOKEN and LOCK_GIST_ID
load_dotenv()


class LockClient:
    def __init__(
        self,
        token: Optional[str] = None,
        gist_id: Optional[str] = None,
        developer_id: Optional[str] = None,
        timeout: int = 10,
    ):
        """Initialize the client with GitHub credentials.

        Args:
            token: GitHub PAT with 'gist' scope. Falls back to GITHUB_TOKEN env var.
            gist_id: ID of the secret gist to use. Falls back to LOCK_GIST_ID env var.
            developer_id: Name of the developer. Falls back to git user.name.
            timeout: Network timeout in seconds.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.gist_id = gist_id or os.getenv("LOCK_GIST_ID")
        self.timeout = timeout

        if not self.token or self.token == "your_github_token_here":
            raise ValueError("Missing GITHUB_TOKEN in environment or constructor.")
        if not self.gist_id or self.gist_id == "your_gist_id_here":
            raise ValueError("Missing LOCK_GIST_ID in environment or constructor.")

        if not developer_id:
            developer_id = self._get_git_username()
        self.developer_id = developer_id

        self.api_base = "https://api.github.com"
        # Use Bearer prefix for broader compatibility (Classic + Fine-grained tokens)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.gist_filename = "locks.json"
        self.history_filename = "history.json"
        self.pid_file = ".lock_watcher.pid"

    def _get_pid(self) -> Optional[int]:
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, "r") as f:
                    return int(f.read().strip())
            except Exception:
                pass
        return None

    def _is_running(self, pid: int) -> bool:
        if sys.platform == "win32":
            try:
                # Use tasklist to check if process exists
                out = subprocess.check_output(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"], text=True
                )
                return str(pid) in out
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def daemon_status(self):
        pid = self._get_pid()
        if pid and self._is_running(pid):
            print(f"Lock watcher is RUNNING (PID: {pid})")
            return True
        print("Lock watcher is NOT running.")
        if pid and os.path.exists(self.pid_file):
            os.remove(self.pid_file)
        return False

    def daemon_stop(self):
        pid = self._get_pid()
        if pid and self._is_running(pid):
            print(f"Stopping lock watcher (PID: {pid})...")
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)], capture_output=True
                )
            else:
                os.kill(pid, 9)
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            print("Stopped.")
        else:
            print("No running watcher found.")

    def daemon_start(self, interval: int = 5, timeout_mins: int = 60):
        pid = self._get_pid()
        if pid and self._is_running(pid):
            print(f"Watcher already running (PID: {pid})")
            return

        print("Starting lock watcher in background...")
        # Start as a detached process
        cmd = [
            sys.executable,
            "-m",
            "src.services.lock_client",
            "watch",
            "--interval",
            str(interval),
            "--timeout",
            str(timeout_mins),
        ]

        if sys.platform == "win32":
            # Attempt to find pythonw.exe in the same directory as sys.executable
            pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(pythonw):
                pythonw = "pythonw"  # Fallback to PATH

            # CREATE_NO_WINDOW (0x08000000) + CREATE_NEW_PROCESS_GROUP (0x0200)
            creationflags = 0x08000000 | 0x00000200

            # Update cmd to use pythonw if it's the first element (sys.executable)
            daemon_cmd = [pythonw] + cmd[1:]

            proc = subprocess.Popen(
                daemon_cmd,
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        else:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        with open(self.pid_file, "w") as f:
            f.write(str(proc.pid))
        print(f"Started (PID: {proc.pid})")

    def _get_git_username(self) -> str:
        """Returns git user.name if available, else git user.email prefix."""
        try:
            name = (
                subprocess.check_output(
                    ["git", "config", "user.name"], stderr=subprocess.STDOUT
                )
                .decode()
                .strip()
            )
            if name:
                return name
            return (
                subprocess.check_output(
                    ["git", "config", "user.email"], stderr=subprocess.STDOUT
                )
                .decode()
                .split("@")[0]
            )
        except Exception:
            return os.getenv("USERNAME") or os.getenv("USER") or "unknown_user"

    def _get_current_branch(self) -> Optional[str]:
        """Returns current git branch name."""
        try:
            return (
                subprocess.check_output(
                    ["git", "branch", "--show-current"], stderr=subprocess.STDOUT
                )
                .decode()
                .strip()
            )
        except Exception:
            return None

    def _get_gist_data(self) -> Tuple[Dict, str]:
        """Fetches current locks and the ETag for optimistic locking.

        Returns:
            Tuple of (locks_dict, etag)
        """
        url = f"{self.api_base}/gists/{self.gist_id}"
        res = requests.get(url, headers=self.headers, timeout=self.timeout)
        res.raise_for_status()

        data = res.json()
        etag = res.headers.get("ETag", "")

        if self.gist_filename not in data["files"]:
            return {}, etag

        content = data["files"][self.gist_filename]["content"]
        if not content or content.strip() == "":
            return {}, etag

        return json.loads(content), etag

    def _get_full_gist_data(self) -> Tuple[Dict, List, str]:
        """Fetches both locks and history.

        Returns:
            Tuple of (locks_dict, history_list, etag)
        """
        url = f"{self.api_base}/gists/{self.gist_id}"
        res = requests.get(url, headers=self.headers, timeout=self.timeout)
        res.raise_for_status()

        data = res.json()
        etag = res.headers.get("ETag", "")

        locks = {}
        if self.gist_filename in data["files"]:
            content = data["files"][self.gist_filename]["content"]
            if content and content.strip():
                locks = json.loads(content)

        history = []
        if self.history_filename in data["files"]:
            content = data["files"][self.history_filename]["content"]
            if content and content.strip():
                history = json.loads(content)

        return locks, history, etag

    def _update_full_gist_data(self, locks: Dict, history: List, etag: str) -> bool:
        """Updates both state files in a single call."""
        url = f"{self.api_base}/gists/{self.gist_id}"

        # Limit history to last 50 entries
        history = history[-50:]

        payload = {
            "files": {
                self.gist_filename: {"content": json.dumps(locks, indent=2)},
                self.history_filename: {"content": json.dumps(history, indent=2)},
            }
        }

        res = requests.patch(
            url, headers=self.headers, json=payload, timeout=self.timeout
        )
        if res.status_code == 412:
            return False
        res.raise_for_status()
        return True

    def _update_gist_data(self, locks: Dict, etag: str) -> bool:
        """Updates the gist with new lock data using ETag for safety.

        Returns:
            True if successful, False if ETag mismatch (conflict).
        """
        url = f"{self.api_base}/gists/{self.gist_id}"
        payload = {
            "files": {self.gist_filename: {"content": json.dumps(locks, indent=2)}}
        }

        # For high-reliability, we'll use a retry loop with re-fetch.
        headers = self.headers.copy()
        # if etag: headers["If-Match"] = etag

        res = requests.patch(url, headers=headers, json=payload, timeout=self.timeout)

        if res.status_code == 412:  # Precondition failed
            return False
        res.raise_for_status()
        return True

    def _utcnow_iso(self) -> str:
        """Helper to get current UTC time in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    def acquire(
        self,
        file_path: str,
        branch_name: Optional[str] = None,
        reason: Optional[str] = None,
        expires_minutes: int = 480,
    ) -> Tuple[bool, str]:
        """Acquire a lock via GitHub Gist.

        Returns: (Success, Message/Token)
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                locks, etag = self._get_gist_data()

                # Check for existing active lock
                if file_path in locks:
                    existing = locks[file_path]
                    expiry = datetime.fromisoformat(existing["expires_at"])
                    if expiry > datetime.now(timezone.utc):
                        if existing["developer_id"] == self.developer_id:
                            msg = (
                                f"You hold active lock on {file_path} "
                                f"(Expires: {existing['expires_at']})"
                            )
                            return False, msg
                        msg = (
                            f"File {file_path} is locked by "
                            f"{existing['developer_id']} until {existing['expires_at']}"
                        )
                        return False, msg

                # Create new lock
                token = str(uuid.uuid4())
                now = datetime.now(timezone.utc)
                locks[file_path] = {
                    "file_path": file_path,
                    "developer_id": self.developer_id,
                    "lock_token": token,
                    "branch_name": branch_name or self._get_current_branch(),
                    "reason": reason,
                    "acquired_at": now.isoformat(),
                    "expires_at": (
                        now + timedelta(minutes=expires_minutes)
                    ).isoformat(),
                }

                if self._update_gist_data(locks, etag):
                    return True, token

                # If update failed (conflict), wait and retry
                time.sleep(1)
            except Exception as e:
                if attempt == max_retries - 1:
                    return False, f"API Error: {str(e)}"
                time.sleep(1)

        return (
            False,
            "Failed to acquire lock due to concurrent updates. Please try again.",
        )

    def acquire_multiple(
        self,
        file_paths: List[str],
        branch_name: Optional[str] = None,
        reason: Optional[str] = None,
        expires_minutes: int = 480,
    ) -> Tuple[bool, List[str], str]:
        """Acquire multiple locks in a single Gist update.

        Returns: (Success, List of failed files, Message)
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                locks, etag = self._get_gist_data()
                conflicts = []
                newly_acquired = []

                for file_path in file_paths:
                    if file_path in locks:
                        existing = locks[file_path]
                        expiry = datetime.fromisoformat(existing["expires_at"])
                        if expiry > datetime.now(timezone.utc):
                            if existing["developer_id"] != self.developer_id:
                                conflicts.append(file_path)
                            continue

                    # Create new lock entry
                    now = datetime.now(timezone.utc)
                    locks[file_path] = {
                        "file_path": file_path,
                        "developer_id": self.developer_id,
                        "lock_token": str(uuid.uuid4()),
                        "branch_name": branch_name or self._get_current_branch(),
                        "reason": reason,
                        "acquired_at": now.isoformat(),
                        "expires_at": (
                            now + timedelta(minutes=expires_minutes)
                        ).isoformat(),
                    }
                    newly_acquired.append(file_path)

                if conflicts:
                    # Provide detail for the first conflict found
                    first_file = conflicts[0]
                    locked_by = locks[first_file]["developer_id"]
                    msg = f"Conflicts detected. {first_file} is locked by {locked_by}."
                    return False, conflicts, msg

                if not newly_acquired:
                    return True, [], "No new locks needed."

                if self._update_gist_data(locks, etag):
                    return True, newly_acquired, "Success"

                time.sleep(1)
            except Exception as e:
                if attempt == max_retries - 1:
                    return False, file_paths, f"API Error: {str(e)}"
                time.sleep(1)

        return False, file_paths, "Concurrent update conflict."

    def release_multiple(self, file_paths: List[str]) -> Tuple[bool, int, str]:
        """Release multiple locks in a single Gist update."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                locks, history, etag = self._get_full_gist_data()
                removed_count = 0

                for file_path in file_paths:
                    if file_path in locks:
                        lock = locks[file_path]
                        if lock["developer_id"] == self.developer_id:
                            # Move to history
                            history_entry = lock.copy()
                            history_entry["released_at"] = self._utcnow_iso()
                            history_entry["outcome"] = "released"
                            history.append(history_entry)
                            del locks[file_path]
                            removed_count += 1

                if removed_count == 0:
                    return True, 0, "No locks to release."

                if self._update_full_gist_data(locks, history, etag):
                    return True, removed_count, "Success"

                time.sleep(1)
            except Exception as e:
                if attempt == max_retries - 1:
                    return False, 0, f"API Error: {str(e)}"
                time.sleep(1)
        return False, 0, "Concurrent update conflict."

    def release_by_path(self, file_path: str) -> Tuple[bool, str]:
        """Release a lock by file path."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                locks, history, etag = self._get_full_gist_data()
                if file_path not in locks:
                    return False, f"No active lock found for {file_path}"

                lock = locks[file_path]
                if lock["developer_id"] != self.developer_id:
                    msg = (
                        f"Unauthorised: Lock on {file_path} is held by "
                        f"{lock['developer_id']}"
                    )
                    return False, msg

                # Move to history
                history_entry = lock.copy()
                history_entry["released_at"] = self._utcnow_iso()
                history_entry["outcome"] = "released"
                history.append(history_entry)

                del locks[file_path]

                if self._update_full_gist_data(locks, history, etag):
                    return True, "released"

                time.sleep(1)
            except Exception as e:
                if attempt == max_retries - 1:
                    return False, f"API Error: {str(e)}"
                time.sleep(1)
        return False, "Concurrent update conflict. Try again."

    def status(self, file_path: str) -> Dict:
        """Check lock status of a file."""
        if not os.path.exists(file_path):
            return {
                "is_locked": False,
                "can_edit": False,
                "error": f"File not found locally: {file_path}",
            }

        try:
            locks, _ = self._get_gist_data()
            if file_path not in locks:
                return {"is_locked": False, "can_edit": True}

            lock = locks[file_path]
            expiry = datetime.fromisoformat(lock["expires_at"])
            if expiry < datetime.now(timezone.utc):
                return {"is_locked": False, "can_edit": True, "expired": True}

            return {
                "is_locked": True,
                "locked_by": lock["developer_id"],
                "acquired_at": lock["acquired_at"],
                "expires_at": lock["expires_at"],
                "reason": lock.get("reason"),
                "can_edit": lock["developer_id"] == self.developer_id,
            }
        except Exception as e:
            return {"is_locked": False, "error": str(e)}

    def watch(self, interval: int = 5, timeout_mins: int = 60):
        """Monitor git status and automatically acquire/release locks."""
        # Write own PID just in case we were started manually
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

        print(f"\n{'='*60}")
        print("👀 GIST LOCK WATCHER STARTED")
        print(f"Developer: {self.developer_id}")
        print(f"Interval: {interval}s")
        print(f"Auto-timeout: {timeout_mins}m inactivity")
        print(f"{'='*60}\n")
        print("Monitoring local git changes for automatic locking...")

        last_modified: set[str] = set()
        last_change_time = datetime.now()
        last_reconcile_time = datetime.now()

        # Initial reconciliation to catch stale locks from before watcher started
        last_modified = self.reconcile()

        try:
            while True:
                try:
                    # 1. Get current git status
                    out = self._run_git_status()
                    current_modified = set()
                    if out:
                        for line in out.splitlines():
                            if len(line) > 3:
                                path = line[3:].strip()
                                current_modified.add(path)

                    # 2. Check for changes
                    if current_modified != last_modified:
                        last_change_time = datetime.now()

                        # Identify new files to lock
                        new_files = current_modified - last_modified
                        if new_files:
                            files_list = list(new_files)
                            ts = datetime.now().strftime("%H:%M:%S")
                            print(f"[{ts}] Detected: {files_list}")
                            success, affected, msg = self.acquire_multiple(
                                files_list, reason="Auto-Watch"
                            )
                            if success:
                                if affected:
                                    print(f"✅ Locked: {affected}")
                            else:
                                print(f"⚠️ CONFLICT ALERT: {msg}")

                        # Identify files to release
                        released_files = last_modified - current_modified
                        if released_files:
                            files_list = list(released_files)
                            ts = datetime.now().strftime("%H:%M:%S")
                            print(f"[{ts}] Finalised: {files_list}")
                            success, count, msg = self.release_multiple(files_list)
                            if success and count > 0:
                                print(f"🔓 Released: {count} file(s)")

                        last_modified = current_modified
                    else:
                        # Periodically reconcile anyway (every 15 mins) just in case
                        sync_delta = datetime.now() - last_reconcile_time
                        if sync_delta > timedelta(minutes=15):
                            self.reconcile()
                            last_reconcile_time = datetime.now()

                        # No changes, check for timeout
                        idle_delta = datetime.now() - last_change_time
                        if timeout_mins > 0 and idle_delta > timedelta(
                            minutes=timeout_mins
                        ):
                            print(
                                f"\n🛑 Watcher timed out after "
                                f"{timeout_mins}m inactivity."
                            )
                            break

                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in watcher: {e}")
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Watcher stopped by user.")
        finally:
            if os.path.exists(self.pid_file):
                # Only remove if it's our PID
                current_pid = self._get_pid()
                if current_pid == os.getpid():
                    os.remove(self.pid_file)

    def open_dashboard(self):
        """Open the collaborative explorer in the default browser."""
        html_path = os.path.join(
            os.path.dirname(__file__), "collaborative_explorer.html"
        )
        if not os.path.exists(html_path):
            print(f"Error: Dashboard file not found at {html_path}")
            return

        abs_path = os.path.abspath(html_path)
        import webbrowser

        print(f"Opening Collaborative Explorer: {abs_path}")
        # Use file:// prefix for browser compatibility
        webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")

    def reconcile(self) -> set[str]:
        """Reconcile Gist locks with local git status to fix stale entries.

        Returns:
            set: Final set of modified files after cleanup.
        """
        print("🔄 Reconciling Gist locks with local Git status...")

        # 1. Get current git status
        try:
            out = self._run_git_status()
            git_modified = set()
            if out:
                for line in out.splitlines():
                    if len(line) > 3:
                        git_modified.add(line[3:].strip())
        except Exception as e:
            print(f"Error getting git status: {e}")
            return set()

        # 2. Get my active locks from Gist
        try:
            active = self.active_locks()
            my_gist_locks = [
                lk["file_path"]
                for lk in active
                if lk["developer_id"] == self.developer_id
            ]
            my_gist_set = set(my_gist_locks)
        except Exception as e:
            print(f"Error getting Gist locks: {e}")
            return git_modified

        # 3. Release stale locks (in Gist but not in Git)
        stale = my_gist_set - git_modified
        if stale:
            print(f"🧹 Found {len(stale)} stale lock(s). Releasing...")
            self.release_multiple(list(stale))

        # 4. Acquire missing locks (in Git but not in Gist)
        # Note: We only auto-acquire if there's no conflict.
        # This part is secondary as the watcher loop handles it,
        # but good for initial startup sync.
        missing = git_modified - my_gist_set
        if missing:
            print(f"📦 Synchronizing {len(missing)} missing lock(s)...")
            self.acquire_multiple(list(missing), reason="Auto-Watch Sync")

        print("✅ Reconciliation complete.")
        return git_modified

    def _run_git_status(self) -> str:
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
        return subprocess.check_output(args, stderr=subprocess.DEVNULL).decode().strip()

    def active_locks(self) -> List[Dict]:
        """List all active locks."""
        try:
            locks, _ = self._get_gist_data()
            now = datetime.now(timezone.utc)
            active = []
            for lock in locks.values():
                expiry = datetime.fromisoformat(lock["expires_at"])
                if expiry > now:
                    active.append(lock)
            return active
        except Exception:
            return []

    def release_all_my_locks(self) -> int:
        """Release all locks for the current developer."""
        try:
            locks, etag = self._get_gist_data()
            to_remove = [
                p for p, lk in locks.items() if lk["developer_id"] == self.developer_id
            ]
            if not to_remove:
                return 0

            for p in to_remove:
                del locks[p]

            if self._update_gist_data(locks, etag):
                return len(to_remove)
            return 0
        except Exception:
            return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Serverless Lock Manager (Gist)")
    parser.add_argument("--token", help="GitHub PAT")
    parser.add_argument("--gist", help="Gist ID")
    parser.add_argument("--user", help="Developer ID")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    acq = subparsers.add_parser("acquire", help="Acquire lock")
    acq.add_argument("file_path", help="Path to file")
    acq.add_argument("--reason", help="Reason")
    acq.add_argument("--expires", type=int, default=480, help="Expiry mins")

    subparsers.add_parser("release", help="Release lock").add_argument(
        "file_path", help="Path or token"
    )
    subparsers.add_parser("status", help="Check status").add_argument("file_path")
    subparsers.add_parser("active", help="List all active")
    subparsers.add_parser("mine", help="List my locks")
    subparsers.add_parser("release-all", help="Release all my locks")

    # Batch commands
    acq_batch = subparsers.add_parser("acquire-batch", help="Acquire multiple locks")
    acq_batch.add_argument("file_paths", nargs="+", help="Paths to files")
    acq_batch.add_argument("--reason", help="Reason")

    rel_batch = subparsers.add_parser("release-batch", help="Release multiple locks")
    rel_batch.add_argument("file_paths", nargs="+", help="Paths to files")

    watch_parser = subparsers.add_parser(
        "watch", help="Monitor git changes and auto-lock"
    )
    watch_parser.add_argument("--interval", type=int, default=5, help="Poll interval")
    watch_parser.add_argument(
        "--timeout", type=int, default=60, help="Auto-stop after mins"
    )

    # Also add them to daemon-start so we can pass them through
    dstart = subparsers.add_parser("daemon-start", help="Start watcher in background")
    dstart.add_argument("--interval", type=int, default=5, help="Poll interval")
    dstart.add_argument("--timeout", type=int, default=60, help="Auto-stop after mins")
    subparsers.add_parser("daemon-stop", help="Stop background watcher")
    subparsers.add_parser("daemon-status", help="Check background watcher status")
    subparsers.add_parser("dashboard", help="Open the collaborative explorer")
    subparsers.add_parser("reconcile", help="Sync local git status with Gist")

    args = parser.parse_args()
    try:
        client = LockClient(token=args.token, gist_id=args.gist, developer_id=args.user)
    except Exception as e:
        print(f"Error: {e}")
        return

    if args.command == "acquire":
        success, res = client.acquire(
            args.file_path, reason=args.reason, expires_minutes=args.expires
        )
        print(f"Success: {success}, Result: {res}")
    elif args.command == "acquire-batch":
        success, affected, res = client.acquire_multiple(
            args.file_paths, reason=args.reason
        )
        if not success and affected:
            # Update: Use the detailed message from the client method
            print(f"ERROR: {res}")
            sys.exit(1)
        print(f"Success: {success}, Affected: {len(affected)}, Result: {res}")
    elif args.command == "release":
        success, res = client.release_by_path(args.file_path)
        print(f"Success: {success}, Result: {res}")
    elif args.command == "release-batch":
        success, count, res = client.release_multiple(args.file_paths)
        print(f"Success: {success}, Count: {count}, Result: {res}")
    elif args.command == "status":
        print(json.dumps(client.status(args.file_path), indent=2))
    elif args.command == "active":
        print(json.dumps(client.active_locks(), indent=2))
    elif args.command == "mine":
        my_locks = [
            lk
            for lk in client.active_locks()
            if lk["developer_id"] == client.developer_id
        ]
        print(json.dumps(my_locks, indent=2))
    elif args.command == "release-all":
        count = client.release_all_my_locks()
        print(f"Released {count} locks")
    elif args.command == "watch":
        client.watch(interval=args.interval, timeout_mins=args.timeout)
    elif args.command == "daemon-start":
        client.daemon_start(interval=args.interval, timeout_mins=args.timeout)
    elif args.command == "daemon-stop":
        client.daemon_stop()
    elif args.command == "daemon-status":
        client.daemon_status()
    elif args.command == "dashboard":
        client.open_dashboard()
    elif args.command == "reconcile":
        client.reconcile()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
