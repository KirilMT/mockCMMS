"""Background watcher daemon for collaborative file locking.

Monitors local git status and automatically acquires/releases Supabase locks.
Can run as a standalone process or be started by the lock_client daemon commands.
"""

from __future__ import annotations

import logging
import os
import sys

# Ensure .collab/core is importable when run as a standalone script
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.join(_THIS_DIR, "..", "core")
if _CORE_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(_THIS_DIR, "..")))

logger = logging.getLogger("collab.watcher")


def main() -> None:
    """Start the watcher using the LockClient.watch() method."""
    # Import here to allow .collab/core to be resolved
    try:
        from core.lock_client import LockClient
    except ImportError:
        # Fallback for when run from project root
        sys.path.insert(0, os.path.abspath(os.path.join(_THIS_DIR, "..", "..")))
        from dotenv import load_dotenv

        load_dotenv()
        # Re-attempt with adjusted path
        from core.lock_client import LockClient  # type: ignore[no-redef]

    import argparse

    parser = argparse.ArgumentParser(description="Collaborative lock watcher daemon")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval (seconds)")
    parser.add_argument("--timeout", type=int, default=60, help="Idle timeout (minutes)")
    parser.add_argument(
        "--open-dashboard", action="store_true", help="Open dashboard on start"
    )
    args = parser.parse_args()

    client = LockClient()
    client.watch(
        interval=args.interval,
        timeout_mins=args.timeout,
        open_dashboard=args.open_dashboard,
    )


if __name__ == "__main__":
    main()
