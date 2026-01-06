#!/usr/bin/env python3
"""Auto-Release Hook for Pre-Push.

Automatically creates a release if the last commit message contains [release].

Usage in commit message:
    git commit -m "feat: add new feature [release:minor]"
    git commit -m "fix: bug fix [release:patch]"
    git commit -m "feat!: breaking change [release:major]"

If no [release] tag is found, the hook passes silently.
"""

import re
import subprocess
import sys
from typing import Optional


def get_last_commit_message() -> str:
    """Get the last commit message."""
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def extract_release_type(commit_msg: str) -> Optional[str]:
    """Extract release type from commit message.

    Patterns:
        [release:patch] or [release:minor] or [release:major]
        [release] defaults to patch
    """
    # Match [release:TYPE] or [release]
    match = re.search(r"\[release(?::(\w+))?\]", commit_msg, re.IGNORECASE)

    if not match:
        return None

    release_type = match.group(1)
    if release_type:
        release_type = release_type.lower()
        if release_type in ["patch", "minor", "major"]:
            return release_type

    # Default to patch if just [release]
    return "patch"


def main() -> int:
    """Main entry point."""
    try:
        commit_msg = get_last_commit_message()
        release_type = extract_release_type(commit_msg)

        if not release_type:
            # No [release] tag found - skip silently
            return 0

        print(f"\n🚀 [release:{release_type}] detected in commit message")
        print(f"Running release manager with bump type: {release_type}\n")

        # Run release manager
        result = subprocess.run(
            ["python", "scripts/release_manager.py", release_type],
            check=False,
        )

        if result.returncode != 0:
            print("\n❌ Release failed!")
            print(
                "Fix the issue and try again, or remove [release] from commit message"
            )
            return 1

        print("\n✅ Release created successfully!")
        print("The release commit and tag will be pushed automatically")
        return 0

    except Exception as e:
        print(f"\n❌ Auto-release hook error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
