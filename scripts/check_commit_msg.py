#!/usr/bin/env python3
"""Check commit message length for Conventional Commits alignment."""

import sys


def check_msg(commit_msg_file):
    with open(commit_msg_file, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # 1. Check subject line (first line)
    if not lines:
        return 0

    subject = lines[0]
    if len(subject) > 88:
        print(f"ERROR: Commit subject is too long ({len(subject)} > 88 characters).")
        print(f"Subject: {subject}")
        return 1

    # 2. Check body lines
    for i, line in enumerate(lines[1:], start=2):
        if len(line) > 88:
            print(
                f"ERROR: Line {i} too long ({len(line)} > 88 chars)."
            )
            print(f"Line: {line}")
            return 1

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_commit_msg.py <commit_msg_file>")
        sys.exit(1)

    sys.exit(check_msg(sys.argv[1]))
