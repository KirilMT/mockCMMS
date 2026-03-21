#!/usr/bin/env python3
"""cleanup_locks.py.

Cleanup expired file locks. Run this via cron or manually.

Usage:
    python scripts/cleanup_locks.py
    python scripts/cleanup_locks.py --dry-run
    python scripts/cleanup_locks.py --db-path instance/locks.db
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.services.lock_manager import LockManager  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Cleanup expired file locks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be cleaned, don't actually clean",
    )
    parser.add_argument(
        "--db-path", default="instance/locks.db", help="Path to the locks database"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    manager = LockManager(db_path=args.db_path)

    if args.dry_run:
        session = manager.Session()
        now = datetime.utcnow()
        from src.services.lock_manager import FileLock

        to_clean = (
            session.query(FileLock)
            .filter(FileLock.released_at.is_(None), FileLock.expires_at <= now)
            .all()
        )
        logging.info(f"[DRY RUN] Would clean up {len(to_clean)} expired locks")
        for lock in to_clean:
            logging.info(
                f" - {lock.file_path} (expired at {lock.expires_at.isoformat()})"
            )
        session.close()
    else:
        count = manager.cleanup_expired_locks()
        logging.info(f"Cleaned up {count} expired locks")


if __name__ == "__main__":
    main()
