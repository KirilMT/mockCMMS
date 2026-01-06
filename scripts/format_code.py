#!/usr/bin/env python3
"""Code Formatting Script.

Actively formats code using configured formatters:
- Python: ruff (lint fixing), isort (imports), black (code), docformatter (docstrings)
- JavaScript: prettier

This script APPLIES changes, unlike validate_code.py which only checks.

Usage:
    python scripts/format_code.py              # Format all code
    python scripts/format_code.py --backend    # Format Python only
    python scripts/format_code.py --frontend   # Format JavaScript only
    python scripts/format_code.py --check      # Check without applying changes
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

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
        ruff_args = ["ruff", "check", "src", "tests", "scripts", "run.py"]
        if not self.check_only:
            ruff_args.append("--fix")

        all_passed &= self.run_command(ruff_args, "Lint fixing (ruff)")

        # 1. Sort imports (isort) - after ruff removes unused imports
        isort_args = ["isort", "src", "tests", "scripts", "run.py"]
        if self.check_only:
            isort_args.append("--check-only")

        all_passed &= self.run_command(isort_args, "Import sorting (isort)")

        # 2. Format code (Black)
        black_args = ["black", "src", "tests", "scripts", "run.py"]
        if self.check_only:
            black_args.insert(1, "--check")

        all_passed &= self.run_command(black_args, "Code formatting (black)")

        # 3. Format docstrings (docformatter)
        docformatter_args = ["docformatter", "-r", "src", "tests", "scripts", "run.py"]
        if self.check_only:
            docformatter_args.insert(1, "--check")
        else:
            docformatter_args.insert(1, "--in-place")

        all_passed &= self.run_command(
            docformatter_args, "Docstring formatting (docformatter)"
        )

        return all_passed

    def format_javascript(self) -> bool:
        """Format JavaScript code using Prettier (if configured)."""
        print("\n" + "=" * 80)
        print("JAVASCRIPT CODE FORMATTING")
        print("=" * 80)

        all_passed = True

        # Check if Prettier is available
        use_shell = sys.platform == "win32"
        prettier_check = subprocess.run(
            ["npm", "list", "prettier"],
            cwd=self.root_dir,
            capture_output=True,
            shell=use_shell,
            check=False,
        )

        if prettier_check.returncode != 0:
            print("ℹ️  Prettier not installed - skipping JavaScript formatting")
            return True

        # Format with Prettier
        prettier_args = ["npx", "prettier"]
        if self.check_only:
            prettier_args.extend(["--check", "src/static/js/**/*.js"])
        else:
            prettier_args.extend(["--write", "src/static/js/**/*.js"])

        all_passed &= self.run_command(
            prettier_args, "JavaScript formatting (prettier)"
        )

        return all_passed

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
            print("\nℹ️  To apply fixes automatically, run:")
            print("    python scripts/format_code.py")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Format code using configured formatters"
    )
    parser.add_argument(
        "--backend", action="store_true", help="Format Python code only"
    )
    parser.add_argument(
        "--frontend", action="store_true", help="Format JavaScript code only"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check formatting without applying changes"
    )

    args = parser.parse_args()

    # Determine what to format
    format_backend = args.backend or not args.frontend
    format_frontend = args.frontend or not args.backend

    # Update pre-commit hooks first (keeps versions in sync)
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
    except FileNotFoundError:
        print("⚠️  pre-commit not installed - skipping hook update")

    # Create formatter
    formatter = CodeFormatter(check_only=args.check)

    # Run formatting
    all_passed = True

    if format_backend:
        all_passed &= formatter.format_python()

    if format_frontend:
        all_passed &= formatter.format_javascript()

    # Print summary
    formatter.print_summary()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
