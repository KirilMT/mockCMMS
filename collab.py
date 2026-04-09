#!/usr/bin/env python3
"""collab.py — CLI Wrapper for the Collaborative File-Locking System.

Delegates all commands to .collab/core/lock_client.py.
"""

import os
import runpy
import sys

if __name__ == "__main__":
    _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    _CLIENT_PATH = os.path.join(_THIS_DIR, ".collab", "core", "lock_client.py")

    if not os.path.exists(_CLIENT_PATH):
        print(f"[ERROR] Could not find lock client at {_CLIENT_PATH}", file=sys.stderr)
        sys.exit(1)

    # Re-write sys.argv[0] to pretend we invoked the script directly,
    # then execute it in the __main__ namespace.
    sys.argv[0] = _CLIENT_PATH
    # Historically this wrapper attempted to reconfigure stdout/stderr to the
    # parent test harness codepage (cp1252) to prevent UnicodeDecodeError when
    # pytest captured subprocess output on Windows. That approach replaced
    # non-representable characters (including emoji) and caused confusion for
    # operators — we avoid mutating global streams here. The daemon/watcher is
    # started detached and its stdout/stderr are redirected to
    # `.collab/logs/application.log` and `.collab/logs/errors.log` so pytest
    # capture should not encounter background-process bytes. Keep the default
    # system streams untouched.

    runpy.run_path(_CLIENT_PATH, run_name="__main__")
