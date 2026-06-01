#!/usr/bin/env python3
"""Last-updated date stamping for long-lived documentation.

Maintains a single canonical marker line on persistent docs:

    _Updated June 1, 2026_

ARCHITECTURE (mirrors the repo's fix-vs-check split):
    - ``stamp`` MODIFIES files and is invoked only by ``scripts/format_code.py``
      (the single sanctioned formatter). It refreshes the marker on docs that
      changed in the working tree, so the date is updated automatically without
      manual effort. Stamping also migrates older date styles: it strips any
      legacy ``_Last updated: YYYY-MM-DD_`` footer and renames a
      ``_Last Updated: <Month D, YYYY>_`` header to the canonical marker, so a
      document never carries two competing "updated" labels.
    - ``check`` NEVER modifies files. It is the pre-commit / CI gate
      (``validate_code.py`` and ``format_code.py --check``):
        * Targeted scope (explicit files, e.g. pre-commit staged set): each
          changed persistent doc must carry *today's* date — otherwise the dev
          is told to run ``format_code.py``. This is wall-clock-safe because
          pre-commit runs on the same day as the edit.
        * Full scope (no files, e.g. CI full run): every persistent doc must
          merely carry a present, valid marker. No equality with "today" is
          required, so a CI run on a later day never produces a false failure.

The marker keeps its existing location in a document (top for roadmaps and
bug-trackers, footer elsewhere); ``stamp`` updates the last occurrence and
preserves any trailing editorial note (e.g. ``_Updated June 1, 2026_ (note)``).

The set of persistent docs is the explicit allowlist below: governance files,
READMEs, agent skills, and living roadmaps/bug-trackers. Generated files
(``CHANGELOG.md``), historical ``archive/`` snapshots, and one-off/temporal docs
are intentionally excluded.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Allowlist of long-lived docs that must carry a maintained "last updated" date.
# Paths are repo-root-relative with forward slashes.
PERSISTENT_DOCS: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    ".github/CONTRIBUTING.md",
    ".github/GIT_WORKFLOW.md",
    "tests/README.md",
    "apps/planning/README.md",
    "apps/reporting/README.md",
    ".agents/skills/bug-tracking/SKILL.md",
    ".agents/skills/commit-workflow/SKILL.md",
    ".agents/skills/file-locking/SKILL.md",
    ".agents/skills/new-feature/SKILL.md",
    ".agents/skills/repo-navigation/SKILL.md",
    ".agents/skills/shell-compatibility/SKILL.md",
    ".agents/skills/skills-maintenance/SKILL.md",
    ".agents/skills/testing-workflow/SKILL.md",
    "docs/mockCMMS_roadmap.md",
    "docs/bug_tracking.md",
    "docs/HOW_TO_UPDATE_ROADMAPS.md",
    "apps/planning/docs/planning_roadmap.md",
    "apps/planning/docs/planning_bug_tracking.md",
    "apps/reporting/docs/reporting_roadmap.md",
    "apps/reporting/docs/reporting_bug_tracking.md",
)

_MONTHS = (
    "January|February|March|April|May|June|"
    "July|August|September|October|November|December"
)
# Canonical marker, e.g. ``_Updated June 1, 2026_`` with an optional trailing note.
_MARKER_RE = re.compile(rf"(?m)^_Updated ((?:{_MONTHS}) \d{{1,2}}, \d{{4}})_(.*)$")
# Legacy ISO footer added by the first version of this tool.
_LEGACY_FOOTER_RE = re.compile(r"(?m)^_Last updated: \d{4}-\d{2}-\d{2}_[ \t]*\n?")
# Older header style ``_Last Updated: <Month D, YYYY>_`` (capitalised, with colon).
_HEADER_MIGRATE_RE = re.compile(
    rf"(?m)^_Last Updated: ((?:{_MONTHS}) \d{{1,2}}, \d{{4}})_[ \t]*$"
)


def today_label() -> str:
    """Return today's date as a human label, e.g. ``June 1, 2026``."""
    today = _dt.date.today()
    return f"{today:%B} {today.day}, {today.year}"


def marker_date(text: str) -> Optional[str]:
    """Return the date in the last marker line, or ``None`` if absent."""
    matches = list(_MARKER_RE.finditer(text))
    return matches[-1].group(1) if matches else None


def stamp_text(text: str, label: str) -> str:
    """Return ``text`` with a single canonical marker set to ``label``.

    Migrates older styles first (strips the legacy ISO footer, renames a
    ``_Last Updated:`` header), then updates the last canonical marker in place —
    preserving any trailing note — or appends one when the document has none.
    """
    text = _LEGACY_FOOTER_RE.sub("", text)
    text = _HEADER_MIGRATE_RE.sub(r"_Updated \1_", text)

    matches = list(_MARKER_RE.finditer(text))
    if matches:
        last = matches[-1]
        replacement = f"_Updated {label}_{last.group(2)}"
        text = text[: last.start()] + replacement + text[last.end() :]
        return text.rstrip("\n") + "\n"
    body = text.rstrip("\n")
    return f"{body}\n\n_Updated {label}_\n"


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def changed_files(root: Path) -> set[str]:
    """Return repo-relative paths changed in the working tree (git).

    Combines unstaged, staged, and untracked changes. Returns an empty set when git is
    unavailable.
    """
    changed: set[str] = set()
    commands = (
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        except (FileNotFoundError, OSError):
            return set()
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    changed.add(_norm(line))
    return changed


def _existing_docs(root: Path) -> list[str]:
    return [rel for rel in PERSISTENT_DOCS if (root / rel).is_file()]


def _scope(root: Path, files: Optional[list[str]]) -> list[str]:
    """Resolve which persistent docs are in scope for a targeted run."""
    wanted = {_norm(f) for f in files} if files else None
    docs = _existing_docs(root)
    if wanted is None:
        return docs
    return [rel for rel in docs if rel in wanted]


def stamp(
    root: Path,
    files: Optional[list[str]] = None,
    init: bool = False,
    today: Optional[str] = None,
) -> list[str]:
    """Refresh the marker on persistent docs; return the paths that changed.

    Targets, in priority order:
        - ``init``: every persistent doc (used once to add markers).
        - ``files``: the persistent docs among the provided paths.
        - otherwise: persistent docs changed in the working tree (git).
    """
    label = today or today_label()
    if init:
        targets = _existing_docs(root)
    elif files is not None:
        targets = _scope(root, files)
    else:
        changed = changed_files(root)
        targets = [rel for rel in _existing_docs(root) if rel in changed]

    stamped: list[str] = []
    for rel in targets:
        path = root / rel
        original = path.read_text(encoding="utf-8")
        updated = stamp_text(original, label)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            stamped.append(rel)
    return stamped


def check(
    root: Path,
    files: Optional[list[str]] = None,
    today: Optional[str] = None,
) -> list[tuple[str, str]]:
    """Verify persistent-doc markers; return ``(path, reason)`` for failures.

    Targeted scope (``files`` given): each in-scope persistent doc must carry
    *today's* date. Full scope (``files`` is ``None``): every persistent doc
    must carry a present, valid marker (no equality with today).
    """
    label = today or today_label()
    strict = files is not None
    problems: list[tuple[str, str]] = []
    for rel in _scope(root, files):
        text = (root / rel).read_text(encoding="utf-8")
        found = marker_date(text)
        if found is None:
            problems.append((rel, "missing '_Updated <Month D, YYYY>_' marker"))
        elif strict and found != label:
            problems.append((rel, f"marker date '{found}' is not today ({label})"))
    return problems


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point for stamping or checking documentation dates."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--stamp", action="store_true", help="Update markers (modifies files)"
    )
    mode.add_argument("--check", action="store_true", help="Verify markers (read-only)")
    parser.add_argument(
        "--init",
        action="store_true",
        help="With --stamp: add the marker to every persistent doc",
    )
    parser.add_argument("files", nargs="*", help="Limit scope to these paths")

    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    files = args.files or None

    if args.stamp:
        stamped = stamp(root, files=files, init=args.init)
        if stamped:
            print(f"Stamped {len(stamped)} doc(s) with {today_label()}:")
            for rel in stamped:
                print(f"  • {rel}")
        else:
            print("No documentation dates needed updating.")
        return 0

    problems = check(root, files=files)
    if problems:
        print("Documentation date check FAILED:")
        for rel, reason in problems:
            print(f"  • {rel}: {reason}")
        print("\nFix: run 'python scripts/format_code.py' to refresh the dates.")
        return 1
    print("Documentation dates OK.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
