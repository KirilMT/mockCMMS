#!/usr/bin/env python3
"""Code Formatting Script.

Actively formats code using configured formatters (Black, isort, docformatter).
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
        """Format Python code using isort, black, and docformatter."""
        print("\n" + "=" * 80)
        print("PYTHON CODE FORMATTING")
        print("=" * 80)

        all_passed = True

        # 1. Sort imports (isort)
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

        # Define targets for formatting
        targets = [
            # Frontend Source
            "src/static/**/*.js",
            "src/static/**/*.css",
            # Apps Frontend (EXCLUDED due to risk/lack of tests for now)
            # "apps/**/static/**/*.js",
            # "apps/**/static/**/*.css",
        ]

        # Format with Prettier
        prettier_args = ["npx", "prettier"]
        if self.check_only:
            prettier_args.append("--check")
        else:
            prettier_args.append("--write")

        # Add targets
        prettier_args.extend(targets)

        all_passed &= self.run_command(
            prettier_args, "Prettier formatting (JS/CSS/HTML)"
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
        djlint_args = ["djlint"] + template_paths

        if self.check_only:
            djlint_args.insert(1, "--check")
        else:
            djlint_args.insert(1, "--reformat")

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
        "--frontend", action="store_true", help="Format JavaScript/CSS/HTML code only"
    )
    parser.add_argument(
        "--docs", action="store_true", help="Format Documentation/JSON code only"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check formatting without applying changes"
    )

    args = parser.parse_args()

    # Determine what to format
    # If no specific flags are set, run ALL.
    run_all = not (args.backend or args.frontend or args.docs)

    format_backend = args.backend or run_all
    format_frontend = args.frontend or run_all
    format_docs = args.docs or run_all

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
        all_passed &= formatter.format_frontend()
        all_passed &= formatter.format_templates()  # Should run alongside frontend

    if format_docs:
        all_passed &= formatter.format_docs()

    # Print summary
    formatter.print_summary()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
