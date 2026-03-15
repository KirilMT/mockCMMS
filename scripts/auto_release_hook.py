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
from pathlib import Path
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


def safe_print(msg: str, fallback: Optional[str] = None):
    """Print with emoji if possible, fallback to plain text if UnicodeEncodeError
    occurs."""
    try:
        print(msg)
    except UnicodeEncodeError:
        if fallback is not None:
            print(fallback)
        else:
            # Remove all non-ascii characters
            print(msg.encode("ascii", errors="ignore").decode())


def main() -> int:
    """Main entry point."""
    try:
        commit_msg = get_last_commit_message()
        release_type = extract_release_type(commit_msg)

        if not release_type:
            # No [release] tag found - skip silently
            return 0

        safe_print(
            f"\n🚀 [release:{release_type}] detected in commit message",
            f"\n[release:{release_type}] detected in commit message",
        )
        safe_print(f"Running release manager with bump type: {release_type}\n")

        # Use venv python if available
        root_dir = Path(__file__).parent.parent
        scripts_dir = "Scripts" if sys.platform == "win32" else "bin"
        py_name = "python.exe" if sys.platform == "win32" else "python"
        python_exe = root_dir / ".venv" / scripts_dir / py_name

        if not python_exe.exists():
            python_exe = Path(sys.executable)

        # Run release manager
        result = subprocess.run(
            [str(python_exe), "scripts/release_manager.py", release_type],
            cwd=str(root_dir),
            check=False,
        )

        if result.returncode != 0:
            safe_print("\n❌ Release failed!", "\nRelease failed!")
            safe_print(
                "Fix the issue and try again, or remove [release] from commit message"
            )
            return 1

        safe_print(
            "\n✅ Release created successfully!", "\nRelease created successfully!"
        )
        safe_print("The release commit and tag will be pushed automatically")
        return 0

    except Exception as e:
        safe_print(
            f"\n❌ Auto-release hook error: {e}", f"\nAuto-release hook error: {e}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
