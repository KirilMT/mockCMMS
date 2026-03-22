#!/usr/bin/env python
import os
import subprocess
import sys


def get_staged_files():
    try:
        output = (
            subprocess.check_output(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
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
    staged_files = get_staged_files()
    if not staged_files:
        sys.exit(0)

    # Skip non-source files
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
        f for f in staged_files if not any(f.endswith(ext) for ext in ignored_exts)
    ]

    if not filtered_files:
        sys.exit(0)

    print(f"🔒 Checking locks for {len(filtered_files)} file(s)...")

    # Call lock_client.py
    # We use 'python' to ensure we use the environment's python
    cmd = [
        sys.executable,
        "-m",
        "src.services.lock_client",
        "acquire-batch",
    ] + filtered_files

    try:
        # Inherit environment so .env is loaded by lock_client
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            print(process.stdout)
            print(process.stderr)
            print("\n❌ Commit blocked: Lock conflict or API error.")
            print("   Ensure you have the lock for all staged source files.")
            sys.exit(1)
        else:
            print(process.stdout.strip())
            sys.exit(0)
    except Exception as e:
        print(f"⚠️  Lock check failed to execute: {e}")
        # Fail-open by default unless LOCK_STRICT=1
        if os.getenv("LOCK_STRICT") == "1":
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
