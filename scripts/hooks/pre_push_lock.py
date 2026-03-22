#!/usr/bin/env python
"""Pre-push hook to automatically release all Gist locks after a successful push."""

import subprocess
import sys


def main():
    print("\n" + "=" * 60)
    print("🔓 PRE-PUSH: RELEASING ALL YOUR GIST LOCKS")
    print("=" * 60)

    # We use release-all to ensure any locks held by the current developer
    # are cleared once they push their work to the remote.
    cmd = [sys.executable, "-m", "src.services.lock_client", "release-all"]

    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            print(process.stdout.strip())
            print("✅ All locks cleared. Happy collaborating!")
        else:
            print(f"❌ Error releasing locks: {process.stderr.strip()}")
            # We don't block the push even if release fails (fail-open)
    except Exception as e:
        print(f"⚠️  Auto-release failed: {e}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
