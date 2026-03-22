#!/usr/bin/env python
"""Post-checkout hook to automatically start the Gist lock watcher."""

import subprocess
import sys


def main():
    # We call daemon-start which handles its own running-check and PID file
    cmd = [sys.executable, "-m", "src.services.lock_client", "daemon-start"]
    try:
        # Background process start is handled by the client's daemon_start method
        subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        # Silent failure for hooks to avoid blocking git operations
        pass


if __name__ == "__main__":
    main()
