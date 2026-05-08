#!/usr/bin/env python3
"""Compatibility shim that delegates to the installed collab CLI runtime."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _runtime_candidates() -> list[str]:
    """Return collab executable candidates in resolution order."""
    repo_root = Path(__file__).resolve().parent
    if os.name == "nt":
        return [
            str(repo_root / ".venv" / "Scripts" / "collab.exe"),
            str(repo_root / ".venv" / "Scripts" / "collab.cmd"),
            "collab.exe",
            "collab.cmd",
            "collab",
        ]
    return [str(repo_root / ".venv" / "bin" / "collab"), "collab"]


def _run_runtime(argv: list[str]) -> int:
    """Run the first available collab executable and return its exit code."""
    for candidate in _runtime_candidates():
        try:
            completed = subprocess.run([candidate, *argv], check=False)
            return int(completed.returncode)
        except FileNotFoundError:
            continue

    print(
        "[ERROR] Installed collab runtime was not found.\n"
        "Install it first (for example, in the project venv):\n"
        "  .\\.venv\\Scripts\\pip.exe install collab\n"
        "Then retry with: collab --help",
        file=sys.stderr,
    )
    return 127


if __name__ == "__main__":
    raise SystemExit(_run_runtime(sys.argv[1:]))
