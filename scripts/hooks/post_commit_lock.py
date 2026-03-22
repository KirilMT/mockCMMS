#!/usr/bin/env python
"""Post-commit hook to automatically release Gist locks."""

import subprocess
import sys


def get_committed_files():
    try:
        # Get files from the most recent commit
        output = (
            subprocess.check_output(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                stderr=subprocess.STDOUT,
            )
            .decode()
            .strip()
        )
        if not output:
            return []
        return output.split("\n")
    except Exception:
        return []


def main():
    committed_files = get_committed_files()
    if not committed_files:
        sys.exit(0)

    # Filter files to release (only source files)
    ignored_exts = [
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".json",
        ".lock",
        ".png",
        ".jpg",
        ".webp",
    ]
    filtered_files = [
        f for f in committed_files if not any(f.endswith(ext) for ext in ignored_exts)
    ]

    if not filtered_files:
        sys.exit(0)

    print(f"🔓 Releasing locks for {len(filtered_files)} file(s)...")

    cmd = [
        sys.executable,
        "-m",
        "src.services.lock_client",
        "release-batch",
    ] + filtered_files

    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            print(process.stdout.strip())
    except Exception as e:
        print(f"⚠️  Auto-release failed: {e}")

    # Also ensure watcher is running after commit
    try:
        start_cmd = [sys.executable, "-m", "src.services.lock_client", "daemon-start"]
        subprocess.run(start_cmd, capture_output=True, text=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
