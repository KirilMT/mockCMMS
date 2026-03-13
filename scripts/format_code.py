#!/usr/bin/env python3
"""Code Formatting Script — Single Source of Truth for ALL formatting.

Actively formats code using configured formatters:
- Whitespace: trailing whitespace removal, EOF newline normalization (ALL text files)
- Python: ruff (lint fixing), isort (imports), black (code), docformatter (docstrings)
- JavaScript/CSS: prettier
- Documentation: prettier (Markdown, JSON)
- Templates: djlint (Jinja2)

ARCHITECTURE:
    format_code.py  = the ONLY tool that MODIFIES files (formatter).
    pre-commit hooks = CHECK-ONLY gate (--check mode, never modify files).

    This separation prevents stash conflicts during commit/amend workflows.

Usage:
    python scripts/format_code.py              # Format all code
    python scripts/format_code.py --backend    # Format Python only
    python scripts/format_code.py --frontend   # Format JS only
    python scripts/format_code.py --check      # Check only (pre-commit)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Import cleanup utilities (located in the same scripts/ directory)
sys.path.insert(0, str(Path(__file__).parent))
from cleanup import clean_caches  # noqa: E402

# Configure UTF-8 encoding for stdout/stderr to handle unicode on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]


class CodeFormatter:
    """Handles code formatting operations."""

    def __init__(self, check_only: bool = False):
        """Initialize the formatter.

        Args:
            check_only: If True, check formatting without applying changes
        """
        self.check_only = check_only
        self.root_dir = Path(__file__).parent.parent
        self.errors: List[str] = []

    def run_command(self, cmd: List[str], description: str) -> bool:
        """Run a formatting command.

        Args:
            cmd: Command to execute
            description: Human-readable description

        Returns:
            True if command succeeded, False otherwise
        """
        print(f"\n{'[CHECK]' if self.check_only else '[FORMAT]'} {description}...")
        print(f"Command: {' '.join(cmd)}")

        try:
            # Set PYTHONIOENCODING to force UTF-8 for subprocess to avoid cp1252 errors
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # On Windows, use shell=True for npm/npx to find them in PATH
            use_shell = sys.platform == "win32" and cmd[0] in ("npm", "npx")

            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                env=env,
                shell=use_shell,
            )

            if result.returncode == 0:
                print(f"✅ {description} - PASSED")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"❌ {description} - FAILED")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                self.errors.append(description)
                return False

        except FileNotFoundError:
            print(f"❌ {description} - Tool not found")
            self.errors.append(f"{description} (tool not found)")
            return False
        except Exception as e:
            print(f"❌ {description} - Error: {e}")
            self.errors.append(f"{description} ({e})")
            return False

    # Text file extensions eligible for whitespace / EOF normalization.
    # Covers every tracked file type that language-specific formatters may miss.
    TEXT_EXTENSIONS: frozenset = frozenset(
        {
            # Code
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".css",
            ".html",
            ".htm",
            # Config
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".env",
            # Documentation
            ".md",
            ".txt",
            ".rst",
            # Shell / Scripts
            ".sh",
            ".bash",
            ".ps1",
            ".bat",
            ".cmd",
            # Other
            ".sql",
            ".xml",
            ".csv",
        }
    )

    def format_whitespace(self) -> bool:
        """Normalize trailing whitespace and EOF newlines for ALL tracked text files.

        Runs BEFORE language-specific formatters to ensure a clean baseline. Covers
        every file type that black/prettier/djlint do NOT handle (e.g., .ps1, .toml,
        .yaml, nested .json).
        """
        print("\n" + "=" * 80)
        print("WHITESPACE & EOF NORMALIZATION")
        print("=" * 80)

        # Use git to enumerate tracked files (respects .gitignore automatically)
        try:
            proc = subprocess.run(
                ["git", "ls-files"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            tracked_files = [f for f in proc.stdout.strip().split("\n") if f]
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Could not list git-tracked files — skipping whitespace check")
            return True

        dirty_files: List[str] = []

        for rel_path in tracked_files:
            filepath = self.root_dir / rel_path

            if filepath.suffix.lower() not in self.TEXT_EXTENSIONS:
                continue

            if not filepath.is_file():
                continue

            try:
                raw = filepath.read_bytes()
            except OSError:
                continue

            # Skip empty or binary files (null bytes indicate binary)
            if not raw or b"\x00" in raw:
                continue

            fixed = self._normalize_whitespace(raw)

            if fixed == raw:
                continue

            dirty_files.append(rel_path)

            if not self.check_only:
                filepath.write_bytes(fixed)

        if not dirty_files:
            print("✅ Whitespace & EOF — all files clean")
            return True

        if self.check_only:
            print(f"❌ {len(dirty_files)} file(s) have whitespace/EOF issues:")
            for f in dirty_files:
                print(f"  - {f}")
            print("\nℹ️  Run 'python scripts/format_code.py' to fix automatically.")
            self.errors.append("Whitespace/EOF normalization")
            return False

        print(f"✅ Fixed whitespace/EOF in {len(dirty_files)} file(s):")
        for f in dirty_files:
            print(f"  - {f}")
        return True

    @staticmethod
    def _normalize_whitespace(content: bytes) -> bytes:
        """Strip trailing whitespace per line and ensure a single trailing newline.

        Preserves the original line-ending style (CRLF vs LF).
        """
        uses_crlf = b"\r\n" in content

        # Normalize to LF for uniform processing
        normalized = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

        # Strip trailing spaces / tabs from every line
        lines = normalized.split(b"\n")
        stripped = [line.rstrip(b" \t") for line in lines]

        result = b"\n".join(stripped)

        # Ensure exactly one trailing newline
        result = result.rstrip(b"\n") + b"\n"

        # Restore CRLF if the original used it
        if uses_crlf:
            result = result.replace(b"\n", b"\r\n")

        return result

    def format_python(self) -> bool:
        """Format Python code using ruff, isort, black, and docformatter.

        Order is important:
        1. ruff --fix: Auto-fix linting issues (unused imports, etc.)
        2. isort: Sort remaining imports
        3. black: Format code structure
        4. docformatter: Format docstrings
        """
        print("\n" + "=" * 80)
        print("PYTHON CODE FORMATTING")
        print("=" * 80)

        all_passed = True

        # 0. Fix linting issues with ruff (before other formatters)
        # This removes unused imports, fixes simple linting issues, etc.
        ruff_args = ["ruff", "check", "src", "tests", "scripts", "run.py", "apps"]
        if not self.check_only:
            ruff_args.append("--fix")

        all_passed &= self.run_command(ruff_args, "Lint fixing (ruff)")

        # 1. Sort imports (isort) - after ruff removes unused imports
        isort_args = ["isort", "src", "tests", "scripts", "run.py", "apps"]
        if self.check_only:
            isort_args.append("--check-only")

        all_passed &= self.run_command(isort_args, "Import sorting (isort)")

        # 2. Format code (Black)
        black_args = ["black", "src", "tests", "scripts", "run.py", "apps"]
        if self.check_only:
            black_args.insert(1, "--check")

        all_passed &= self.run_command(black_args, "Code formatting (black)")

        # 3. Format docstrings (docformatter)
        docformatter_args = [
            "docformatter",
            "-r",
            "src",
            "tests",
            "scripts",
            "run.py",
            "apps",
        ]
        if self.check_only:
            docformatter_args.insert(1, "--check")
        else:
            docformatter_args.insert(1, "--in-place")

        all_passed &= self.run_command(
            docformatter_args, "Docstring formatting (docformatter)"
        )

        # 4. Linting Fix (Ruff)
        ruff_args = [
            "ruff",
            "check",
            "--fix",
            "src",
            "tests",
            "scripts",
            "run.py",
            "apps",
        ]
        if self.check_only:
            # When checking only, we don't want to fix, just check
            ruff_args = ["ruff", "check", "src", "tests", "scripts", "run.py", "apps"]

        all_passed &= self.run_command(ruff_args, "Linting fixes (ruff)")

        return all_passed

    def _check_prettier(self) -> bool:
        """Check if Prettier is installed."""
        use_shell = sys.platform == "win32"
        prettier_check = subprocess.run(
            ["npm", "list", "prettier"],
            cwd=self.root_dir,
            capture_output=True,
            shell=use_shell,
            check=False,
        )
        return prettier_check.returncode == 0

    def format_frontend(self) -> bool:
        """Format Frontend code (JS, CSS, HTML) using Prettier."""
        print("\n" + "=" * 80)
        print("FRONTEND CODE FORMATTING")
        print("=" * 80)

        all_passed = True

        if not self._check_prettier():
            print("ℹ️  Prettier not installed - skipping frontend formatting")
            return True

        # Format with Prettier
        # Broaden coverage to include apps and tests
        prettier_paths = [
            "src/static/js/**/*.js",
            "apps/**/*.js",
            "tests/**/*.js",
            "src/static/css/**/*.css",
            "apps/**/*.css",
        ]

        prettier_args = ["npx", "prettier"]
        if self.check_only:
            prettier_args.append("--check")
        else:
            prettier_args.append("--write")

        prettier_args.extend(prettier_paths)

        all_passed &= self.run_command(
            prettier_args, "JavaScript/CSS formatting (prettier)"
        )

        return all_passed

    def format_docs(self) -> bool:
        """Format Documentation (MD, JSON) using Prettier."""
        print("\n" + "=" * 80)
        print("DOCUMENTATION FORMATTING")
        print("=" * 80)

        all_passed = True

        if not self._check_prettier():
            print("ℹ️  Prettier not installed - skipping documentation formatting")
            return True

        # Define targets for formatting
        targets = [
            # Documentation
            "docs/**/*.md",
            "*.md",  # Root markdown
            "apps/**/*.md",  # App documentation
            # Context Configuration
            "*.json",
            ".github/**/*.md",
        ]

        # Format with Prettier
        prettier_args = ["npx", "prettier"]
        if self.check_only:
            prettier_args.append("--check")
        else:
            prettier_args.append("--write")

        # Add targets
        prettier_args.extend(targets)

        all_passed &= self.run_command(prettier_args, "Prettier formatting (MD/JSON)")

        return all_passed

    def format_templates(self) -> bool:
        """Format Jinja2 templates using djlint."""
        print("\n" + "=" * 80)
        print("JINJA2 TEMPLATE FORMATTING")
        print("=" * 80)

        # Exclude apps/ templates for now due to risk
        template_paths = ["src/templates"]
        # template_paths = ["src/templates", "apps/**/templates"]
        djlint_args = [sys.executable, "-m", "djlint"] + template_paths

        if self.check_only:
            djlint_args.insert(3, "--check")
        else:
            djlint_args.insert(3, "--reformat")

        return self.run_command(djlint_args, "Template formatting (djlint)")

    def print_summary(self) -> None:
        """Print formatting summary."""
        print("\n" + "=" * 80)
        print("FORMATTING SUMMARY")
        print("=" * 80)

        if not self.errors:
            mode = "check" if self.check_only else "formatting"
            print(f"\n✅ All {mode} operations passed!")
        else:
            print(f"\n❌ {len(self.errors)} operation(s) failed:")
            for error in self.errors:
                print(f"  - {error}")
            if self.check_only:
                print("\nℹ️  To fix all issues automatically, run:")
                print("    python scripts/format_code.py")
            else:
                print("\nℹ️  Review errors above and fix manually if needed.")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Format code using configured formatters"
    )
    parser.add_argument(
        "--backend", action="store_true", help="Format Python code only"
    )
    parser.add_argument(
        "--frontend", action="store_true", help="Format JavaScript/CSS/HTML code only"
    )
    parser.add_argument(
        "--docs", action="store_true", help="Format Documentation/JSON code only"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check formatting without applying changes"
    )
    parser.add_argument(
        "--update-hooks",
        action="store_true",
        help="Run 'pre-commit autoupdate' before formatting (opt-in)",
    )

    args = parser.parse_args()

    # Determine what to format
    # If no specific flags are set, run ALL.
    run_all = not (args.backend or args.frontend or args.docs)

    format_backend = args.backend or run_all
    format_frontend = args.frontend or run_all
    format_docs = args.docs or run_all

    # Updating hook revisions can modify tracked files and often requires network/SSL,
    # so keep this as an explicit maintenance action instead of a default format step.
    if args.update_hooks:
        print("\n" + "=" * 80)
        print("UPDATING PRE-COMMIT HOOKS")
        print("=" * 80)
        use_shell = sys.platform == "win32"
        try:
            result = subprocess.run(
                ["pre-commit", "autoupdate"],
                capture_output=True,
                text=True,
                shell=use_shell,
                check=False,
            )
            if result.returncode == 0:
                print("✅ Pre-commit hooks are up-to-date")
                if result.stdout.strip():
                    print(result.stdout)
            else:
                print("⚠️  Could not update pre-commit hooks (non-critical)")
                if result.stderr.strip():
                    print(result.stderr, file=sys.stderr)
        except FileNotFoundError:
            print("⚠️  pre-commit not installed - skipping hook update")

    # Create formatter
    formatter = CodeFormatter(check_only=args.check)

    # Run formatting
    all_passed = True

    # Whitespace & EOF normalization ALWAYS runs first (covers all file types)
    all_passed &= formatter.format_whitespace()

    if format_backend:
        all_passed &= formatter.format_python()

    if format_frontend:
        all_passed &= formatter.format_frontend()
        all_passed &= formatter.format_templates()  # Should run alongside frontend

    if format_docs:
        all_passed &= formatter.format_docs()

    # Print summary
    formatter.print_summary()

    # Remove __pycache__ and other bytecode left behind by the formatters
    print("\n" + "=" * 80)
    print("CLEANUP")
    print("=" * 80)
    count = clean_caches(dry_run=False)
    if count:
        print(f"\n✅ Removed {count} cache artifact(s) — repo is clean.")
    else:
        print("\n✨ Nothing to clean — repo is already clean.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
