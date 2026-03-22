#!/usr/bin/env python
"""Post-merge hook to automatically start the Gist lock watcher after a pull/merge."""

import subprocess
import sys


def main():
    cmd = [sys.executable, "-m", "src.services.lock_client", "daemon-start"]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
