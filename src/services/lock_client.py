"""lock_client.py.

Python client library for interacting with the lock manager service. Can be used from
CLI scripts, IDE extensions, or other services.
"""

import json
import subprocess
from typing import Dict, List, Optional, Tuple

import requests


class LockClient:
    def __init__(
        self,
        server_url: str = "http://localhost:5001",
        developer_id: Optional[str] = None,
        timeout: int = 5,
    ):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        if not developer_id:
            developer_id = self._get_git_user()
        self.developer_id = developer_id

    def _get_git_user(self) -> str:
        try:
            name = (
                subprocess.check_output(
                    ["git", "config", "user.name"], stderr=subprocess.STDOUT
                )
                .decode()
                .strip()
            )
            return name.replace(" ", "_").lower()
        except Exception:
            return "unknown_user"

    def acquire(
        self,
        file_path: str,
        branch_name: Optional[str] = None,
        reason: Optional[str] = None,
        expires_minutes: int = 480,
    ) -> Tuple[bool, str]:
        """Returns (True, lock_token) on success or (False, error_message) on
        failure."""
        try:
            res = requests.post(
                f"{self.server_url}/api/locks/acquire",
                json={
                    "file_path": file_path,
                    "developer_id": self.developer_id,
                    "branch_name": branch_name,
                    "reason": reason,
                    "expires_minutes": expires_minutes,
                },
                timeout=self.timeout,
            )
            data = res.json()
            if res.status_code == 200:
                return True, data["lock_token"]
            else:
                return False, data.get("message", "Unknown error")
        except Exception as e:
            return False, str(e)

    def release(self, lock_token: str) -> Tuple[bool, str]:
        """Returns (True, 'released') or (False, error_message)."""
        try:
            res = requests.post(
                f"{self.server_url}/api/locks/release",
                json={"lock_token": lock_token},
                timeout=self.timeout,
            )
            data = res.json()
            if res.status_code == 200:
                return True, "released"
            else:
                return False, data.get("message", "Unknown error")
        except Exception as e:
            return False, str(e)

    def status(self, file_path: str) -> Dict:
        """Returns lock status dict.

        Returns {'is_locked': False, 'error': '...'} if server unreachable.
        """
        try:
            res = requests.get(
                f"{self.server_url}/api/locks/status",
                params={"file_path": file_path},
                timeout=self.timeout,
            )
            if res.status_code == 200:
                return res.json()
            return {"is_locked": False, "error": f"Server returned {res.status_code}"}
        except Exception as e:
            return {"is_locked": False, "error": str(e)}

    def active_locks(self) -> List[Dict]:
        """Returns all active locks.

        Returns [] if server unreachable.
        """
        try:
            res = requests.get(
                f"{self.server_url}/api/locks/active", timeout=self.timeout
            )
            if res.status_code == 200:
                return res.json()
            return []
        except Exception:
            return []

    def my_locks(self) -> List[Dict]:
        """Returns all active locks held by this developer."""
        try:
            res = requests.get(
                f"{self.server_url}/api/locks/developer/{self.developer_id}",
                timeout=self.timeout,
            )
            if res.status_code == 200:
                return res.json()
            return []
        except Exception:
            return []

    def release_all_my_locks(self) -> int:
        """Releases all locks held by this developer.

        Returns count released.
        """
        locks = self.my_locks()
        count = 0
        for lock in locks:
            success, _ = self.release(lock["lock_token"])
            if success:
                count += 1
        return count

    def health(self) -> bool:
        """Returns True if lock server is reachable and healthy."""
        try:
            res = requests.get(
                f"{self.server_url}/api/locks/health", timeout=self.timeout
            )
            return res.status_code == 200
        except Exception:
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Lock Manager CLI")
    parser.add_argument(
        "--url", default="http://localhost:5001", help="Lock server URL"
    )
    parser.add_argument("--user", help="Developer ID (default: git user)")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("acquire", help="Acquire lock on a file").add_argument(
        "file_path", help="Path to the file"
    )
    subparsers.add_parser("release", help="Release lock using token").add_argument(
        "token", help="Lock token"
    )
    subparsers.add_parser("status", help="Check lock status of a file").add_argument(
        "file_path", help="Path to the file"
    )
    subparsers.add_parser("active", help="List all active locks")
    subparsers.add_parser("mine", help="List my active locks")
    subparsers.add_parser("release-all", help="Release all my active locks")
    subparsers.add_parser("health", help="Check server health")

    args = parser.parse_args()
    client = LockClient(server_url=args.url, developer_id=args.user)

    if args.command == "acquire":
        success, res = client.acquire(args.file_path)
        print(f"Success: {success}, Result: {res}")
    elif args.command == "release":
        success, res = client.release(args.token)
        print(f"Success: {success}, Result: {res}")
    elif args.command == "status":
        res = client.status(args.file_path)
        print(json.dumps(res, indent=2))
    elif args.command == "active":
        res = client.active_locks()
        print(json.dumps(res, indent=2))
    elif args.command == "mine":
        res = client.my_locks()
        print(json.dumps(res, indent=2))
    elif args.command == "release-all":
        count = client.release_all_my_locks()
        print(f"Released {count} locks")
    elif args.command == "health":
        alive = client.health()
        print(f"Server alive: {alive}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
