#!/usr/bin/env python3
"""Code Formatting Script — Single Source of Truth for ALL formatting.

REQUIREMENT: For YAML formatting, you must have both 'prettier' and
'prettier-plugin-yaml' installed as dev dependencies:
    npm install --save-dev prettier prettier-plugin-yaml

Actively formats code using configured formatters:
- Whitespace: trailing whitespace removal, EOF newline normalization (ALL text files)
- Python: ruff (lint fixing + unsafe fixes), isort, black, docformatter
- JavaScript/CSS: prettier (quiet in format mode)
- Documentation: prettier (quiet in format mode, with prettier-plugin-yaml for YAML)
- Templates: djlint (Jinja2)

ARCHITECTURE:
    format_code.py  = the ONLY tool that MODIFIES files (formatter).
    pre-commit hooks = CHECK-ONLY gate (--check mode, never modify files).

Usage:
    python scripts/format_code.py              # Format everything
    python scripts/format_code.py --backend    # Python only
    python scripts/format_code.py --frontend   # JS + templates only
    python scripts/format_code.py --check      # Check only (pre-commit)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Import cleanup utilities
sys.path.insert(0, str(Path(__file__).parent))
from cleanup import clean_caches  # noqa: E402

# UTF-8 for Windows + ANSI colors (standardized — matches common setup.ps1 /
# PowerShell colors)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined,union-attr]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined,union-attr]


# ANSI color codes (professional, clean, cross-platform)
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
MAGENTA = "\033[95m"


class CodeFormatter:
    """Handles code formatting with colored, professional, numbered output."""

    # NOTE: .html/.htm are intentionally excluded — djlint is the authoritative
    # formatter for templates and its Jinja2 line-breaking can produce trailing
    # whitespace (e.g. in `{{ expr | join(", ") \n}}`).  Including them here
    # creates an infinite format cycle: whitespace-norm strips → djlint adds back.
    TEXT_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".css",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".env",
            ".md",
            ".txt",
            ".rst",
            ".sh",
            ".bash",
            ".ps1",
            ".bat",
            ".cmd",
            ".sql",
            ".xml",
            ".csv",
        }
    )

    def __init__(self, check_only: bool = False, files: Optional[list[str]] = None):
        self.check_only = check_only
        self.files = files
        self.root_dir = Path(__file__).parent.parent
        self.errors: list[str] = []
        self.failed_tools: list[tuple[str, str, bool]] = (
            []
        )  # (step_header, desc, is_check)

    def _get_targets(
        self, extensions: tuple[str, ...], default: list[str]
    ) -> list[str]:
        """Return files filtered by extension if provided, else return default dirs."""
        if not self.files:
            return default
        return [f for f in self.files if f.lower().endswith(extensions)]

    # ── Low-level execution ──────────────────────────────────────────────

    def _prepare_env(self) -> dict:
        """Prepare environment dict for subprocess calls."""
        env = os.environ.copy()
        scripts_dir = "Scripts" if sys.platform == "win32" else "bin"
        venv_scripts = self.root_dir / ".venv" / scripts_dir
        if venv_scripts.exists():
            env["PATH"] = f"{venv_scripts}{os.pathsep}{env.get('PATH', '')}"
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    def _exec(
        self, cmd: list[str], suppress_output: bool = False
    ) -> tuple[bool, Optional[subprocess.CompletedProcess]]:
        """Run a subprocess and optionally print its output.

        Returns:
            (success, CompletedProcess | None).
        """
        try:
            # On Windows, npm/npx are .cmd files — use cmd /c to execute
            # them without shell=True (avoids B602 security concern).
            if sys.platform == "win32" and cmd[0] in ("npm", "npx"):
                cmd = ["cmd", "/c"] + cmd
            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                env=self._prepare_env(),
            )
            if not suppress_output:
                printed = False
                if result.stdout.strip():
                    for line in result.stdout.strip().splitlines():
                        print(f"       {line}")
                    printed = True
                if result.stderr.strip():
                    for line in result.stderr.strip().splitlines():
                        print(f"       {line}", file=sys.stderr)
                    printed = True
                if result.returncode == 0 and not printed:
                    print("       All checks passed!")
            return result.returncode == 0, result
        except FileNotFoundError:
            if not suppress_output:
                print(f"       Tool not found: {cmd[0]}")
            return False, None
        except Exception as exc:
            if not suppress_output:
                print(f"       Error: {exc}")
            return False, None

    # ── Unified tool step runner ─────────────────────────────────────────

    def _run_tool_step(
        self,
        description: str,
        fix_cmd: Optional[list[str]],
        check_cmd: Optional[list[str]],
        section: str,
        section_idx: int,
        section_total: int,
    ) -> bool:
        """Run one formatting tool step with fully standardized output.

        Fix mode (default):
            [SECTION X/Y] Description...
               Command: <fix_cmd>
                   <output>
               ✅ Description — SUCCESS
            OR on failure:
               ❌ Description — ISSUES FOUND

               Command: <check_cmd>
               ✅ Description (check) — All issues fixed — no further action needed.
               ❌ Description (check) — Issues remain — manual fix required.

        Check mode (--check): single command, no fix attempt.

        For check-only tools (fix_cmd is None), the check_cmd is used
        as the primary command in both modes.
        """
        step_header = f"[{section.upper()} {section_idx}/{section_total}] {description}"
        print(f"\n{CYAN}{step_header}...{RESET}")

        # ── Check-only mode ──
        if self.check_only:
            cmd = check_cmd or fix_cmd
            assert cmd is not None, "At least one of fix_cmd or check_cmd required"
            print(f"   {MAGENTA}Command: {' '.join(cmd)}{RESET}")
            success, _ = self._exec(cmd)
            if success:
                print(f"   {GREEN}✅ {description} — SUCCESS{RESET}")
            else:
                print(f"   {RED}❌ {description} — ISSUES FOUND{RESET}")
                self.failed_tools.append((step_header, description, False))
            return success

        # ── Fix mode: Command 1 (fix) ──
        primary_cmd = fix_cmd if fix_cmd is not None else check_cmd
        assert primary_cmd is not None, "At least one of fix_cmd or check_cmd required"
        print(f"   {MAGENTA}Command: {' '.join(primary_cmd)}{RESET}")
        success, _ = self._exec(primary_cmd)

        if success:
            print(f"   {GREEN}✅ {description} — SUCCESS{RESET}")
            return True

        # Command 1 failed
        print(f"   {RED}❌ {description} — ISSUES FOUND{RESET}")

        # ── Fix mode: Command 2 (check) ──
        if check_cmd:
            print(f"\n   {MAGENTA}Command: {' '.join(check_cmd)}{RESET}")
            check_ok, _ = self._exec(check_cmd, suppress_output=True)
            if check_ok:
                print(
                    f"   {GREEN}✅ {description} (check) — All issues fixed — "
                    f"no further action needed.{RESET}"
                )
            else:
                print(
                    f"   {RED}❌ {description} (check) — Issues remain — "
                    f"manual fix required.{RESET}"
                )
                self.failed_tools.append((step_header, description, True))
            return check_ok

        # No check command available
        self.failed_tools.append((step_header, description, False))
        return False

    def normalize_whitespace(self) -> bool:
        """Whitespace & EOF normalization with clean output."""
        print("\n" + "=" * 80)
        print(f"{BOLD}WHITESPACE & EOF NORMALIZATION{RESET}")
        print("=" * 80)

        if self.files:
            tracked_files = self.files
        else:
            try:
                proc = subprocess.run(
                    ["git", "ls-files"],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=True,
                )
                tracked_files = [f for f in proc.stdout.strip().split("\n") if f]
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("   ⚠️  Could not list git files — skipping whitespace")
                return True

        issues: list[str] = []
        fix = not self.check_only

        for rel_path in tracked_files:
            filepath = self.root_dir / rel_path
            if (
                filepath.suffix.lower() not in self.TEXT_EXTENSIONS
                or not filepath.is_file()
            ):
                continue

            try:
                raw = filepath.read_bytes()
            except OSError:
                continue
            if not raw or b"\x00" in raw:
                continue

            fixed = self._normalize_whitespace(raw)
            if fixed != raw:
                issues.append(rel_path)
                if fix:
                    filepath.write_bytes(fixed)

        if not issues:
            print(f"   {GREEN}✅ Whitespace & EOF — all files clean{RESET}")
            return True

        if fix:
            print(f"   {GREEN}✅ Fixed whitespace/EOF in {len(issues)} file(s){RESET}")
            return True
        else:
            print(f"   {RED}❌ {len(issues)} file(s) have whitespace/EOF issues{RESET}")
            for f in issues[:10]:
                print(f"      • {f}")
            if len(issues) > 10:
                print(f"      ... and {len(issues)-10} more")
            return False

    @staticmethod
    def _normalize_whitespace(content: bytes) -> bytes:
        uses_crlf = b"\r\n" in content
        normalized = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        lines = normalized.split(b"\n")
        stripped = [line.rstrip(b" \t") for line in lines]
        result = b"\n".join(stripped).rstrip(b"\n") + b"\n"
        if uses_crlf:
            result = result.replace(b"\n", b"\r\n")
        return result

    # ── Backend (Python) formatting ─────────────────────────────────────

    def format_python(self) -> bool:
        """Python formatting: ruff, isort, black, docformatter, flake8."""
        targets = self._get_targets(
            (".py",),
            [
                "src",
                "tests",
                "scripts",
                "run.py",
                "collab.py",
                "conftest.py",
                "apps",
                ".collab",
            ],
        )
        if not targets:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}BACKEND CODE FORMATTING{RESET}")
        print("=" * 80)
        flake8_exclude = (
            "--exclude="
            ".venv,node_modules,__pycache__,.git,.pytest_cache,"
            "htmlcov,playwright-report"
        )
        flake8_opts = [
            flake8_exclude,
            "--count",
            "--show-source",
            "--statistics",
            "--max-line-length=88",
        ]
        # Each tuple: (description, fix_cmd, check_cmd)
        steps: list[tuple[str, Optional[list[str]], list[str]]] = [
            (
                "Ruff linting & fixing",
                ["ruff", "check"] + targets + ["--fix", "--unsafe-fixes"],
                ["ruff", "check"] + targets,
            ),
            (
                "Import sorting (isort)",
                ["isort"] + targets,
                ["isort"] + targets + ["--check-only"],
            ),
            (
                "Code formatting (black)",
                ["black"] + targets,
                ["black", "--check"] + targets,
            ),
            (
                "Docstring formatting (docformatter)",
                ["docformatter", "--in-place", "-r"] + targets,
                ["docformatter", "--check", "-r"] + targets,
            ),
            (
                "Final linting (flake8)",
                None,  # Check-only tool — no auto-fix
                ["flake8"] + targets + flake8_opts,
            ),
        ]
        all_passed = True
        for idx, (desc, fix_cmd, check_cmd) in enumerate(steps, 1):
            all_passed &= self._run_tool_step(
                desc, fix_cmd, check_cmd, "BACKEND", idx, len(steps)
            )
        return all_passed

    def _check_prettier(self) -> bool:
        # On Windows, npm is a .cmd file — use cmd /c to avoid shell=True.
        npm_cmd = ["cmd", "/c", "npm"] if sys.platform == "win32" else ["npm"]
        result = subprocess.run(
            npm_cmd + ["list", "prettier"],
            cwd=self.root_dir,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        # Check for prettier-plugin-yaml for YAML support
        plugin_result = subprocess.run(
            npm_cmd + ["list", "prettier-plugin-yaml"],
            cwd=self.root_dir,
            capture_output=True,
            check=False,
        )
        if plugin_result.returncode != 0:
            print(
                "   ⚠️  prettier-plugin-yaml not installed — YAML files will NOT be "
                "formatted!\n"
                "      Run: npm install --save-dev prettier-plugin-yaml"
            )
            return False
        return True

    def _filter_glob_targets(self, patterns: list[str]) -> list[str]:
        """Filter glob patterns to only include those that match real files.

        Prettier exits with error code 2 for patterns matching zero files. This guard
        ensures we only pass patterns that resolve to at least one file, applied
        consistently across all sections.
        """
        return [p for p in patterns if list(self.root_dir.glob(p))]

    # ── Frontend (JS/CSS) formatting ────────────────────────────────────

    def format_frontend(self) -> bool:
        """Frontend formatting: prettier for JS/CSS."""
        base_targets = self._filter_glob_targets(
            [
                "src/static/js/**/*.js",
                "apps/**/*.js",
                "tests/**/*.js",
                "src/static/css/**/*.css",
                "apps/**/*.css",
                ".collab/**/*.js",
                ".collab/**/*.css",
            ]
        )

        targets = self._get_targets(
            (".js", ".jsx", ".ts", ".tsx", ".css", ".scss"),
            base_targets,
        )
        if not targets:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}FRONTEND CODE FORMATTING{RESET}")
        print("=" * 80)
        if not self._check_prettier():
            print("   ℹ️  Prettier not installed — skipping frontend")
            return True
        return self._run_tool_step(
            "JavaScript/CSS (prettier)",
            ["npx", "prettier", "--write", "--log-level", "silent"] + targets,
            ["npx", "prettier", "--check"] + targets,
            "FRONTEND",
            1,
            1,
        )

    # ── Documentation formatting ────────────────────────────────────────

    def format_docs(self) -> bool:
        """Documentation formatting: prettier for Markdown/JSON."""
        doc_targets = self._get_targets(
            (".md", ".json"),
            self._filter_glob_targets(
                [
                    "docs/**/*.md",
                    "*.md",
                    "apps/**/*.md",
                    "*.json",
                    ".github/**/*.md",
                    ".collab/**/*.md",
                    ".collab/**/*.json",
                    "tests/**/*.md",
                    ".agents/**/*.md",
                ]
            ),
        )
        if not doc_targets:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}DOCUMENTATION FORMATTING{RESET}")
        print("=" * 80)
        return self._run_tool_step(
            "Markdown/JSON (prettier)",
            ["npx", "prettier", "--write", "--log-level", "silent"] + doc_targets,
            ["npx", "prettier", "--check"] + doc_targets,
            "DOCS",
            1,
            1,
        )

    # ── YAML formatting & linting ──────────────────────────────────────

    def format_yaml(self) -> bool:
        """YAML formatting (prettier) and linting (yamllint)."""
        exclude_dirs = {".venv", "node_modules", ".git", "__pycache__"}
        yaml_files = []
        for ext in ("*.yaml", "*.yml"):
            for p in self.root_dir.rglob(ext):
                if not any(part in exclude_dirs for part in p.parts):
                    yaml_files.append(str(p))
        if not yaml_files:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}YAML FORMATTING & LINTING{RESET}")
        print("=" * 80)
        all_passed = True
        # Step 1: Prettier formatting
        all_passed &= self._run_tool_step(
            "YAML (prettier)",
            ["npx", "prettier", "--write", "--log-level", "silent"] + yaml_files,
            ["npx", "prettier", "--check"] + yaml_files,
            "YAML",
            1,
            2,
        )
        # Step 2: yamllint (check-only, no fix mode)
        all_passed &= self._run_tool_step(
            "YAML (yamllint)",
            None,
            ["yamllint", "--strict"] + yaml_files,
            "YAML",
            2,
            2,
        )
        return all_passed

    # ── Template formatting ────────────────────────────────────────────

    def format_templates(self) -> bool:
        """Jinja2 template formatting: djlint."""
        # Discover all template directories (src + modular apps)
        template_dirs = ["src/templates"]
        for app_tpl in sorted(self.root_dir.glob("apps/*/src/templates")):
            template_dirs.append(str(app_tpl.relative_to(self.root_dir)))
        targets = self._get_targets((".html", ".htm"), template_dirs)
        if not targets:
            return True

        print("\n" + "=" * 80)
        print(f"{BOLD}JINJA2 TEMPLATE FORMATTING{RESET}")
        print("=" * 80)

        python = sys.executable
        description = "Jinja2 templates (djlint)"
        step_header = "[TEMPLATES 1/1] Jinja2 templates (djlint)"
        fix_cmd = [python, "-m", "djlint"] + targets + ["--reformat", "--quiet"]
        check_cmd = [python, "-m", "djlint"] + targets + ["--check"]

        print(f"\n{CYAN}{step_header}...{RESET}")
        print(f"   {MAGENTA}Command: {' '.join(fix_cmd)}{RESET}")

        # Suppress djlint progress bars; we'll print concise status messages instead.
        fix_ok, _ = self._exec(fix_cmd, suppress_output=True)
        if fix_ok:
            print("       All checks passed!")
            print(f"   {GREEN}✅ {description} — SUCCESS{RESET}")
            return True

        print(
            f"   {CYAN}ℹ️  {description} — changes applied; "
            f"running verification check...{RESET}"
        )
        print(f"\n   {MAGENTA}Command: {' '.join(check_cmd)}{RESET}")
        check_ok, _ = self._exec(check_cmd, suppress_output=True)

        if check_ok:
            print(
                f"   {GREEN}✅ {description} — All issues fixed — "
                f"no further action needed.{RESET}"
            )
            return True

        print(
            f"   {RED}❌ {description} (check) — Issues remain — "
            f"manual fix required.{RESET}"
        )
        # Re-run once with output so user sees actionable details.
        self._exec(check_cmd, suppress_output=False)
        self.failed_tools.append((step_header, description, True))
        return False

    def print_summary(self) -> None:
        """Final colored summary."""
        print("\n" + "=" * 80)
        print(f"{BOLD}FORMATTING SUMMARY{RESET}")
        print("=" * 80)
        failed_tools = getattr(self, "failed_tools", [])
        if not failed_tools:
            mode = "check" if self.check_only else "formatting"
            print(f"   {GREEN}✅ All {mode} operations completed successfully!{RESET}")
        else:
            print(f"   {RED}❌ {len(failed_tools)} operation(s) failed{RESET}")
            for step_header, desc, is_check in failed_tools:
                # Show step number and title as in the step header
                print(f"      • {step_header}")
            print(f"\n   {RED}⚠️  Review the errors above and fix manually.{RESET}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Format code using configured formatters"
    )
    parser.add_argument("--backend", action="store_true", help="Python only")
    parser.add_argument(
        "--frontend", action="store_true", help="JS/CSS + templates only"
    )
    parser.add_argument("--docs", action="store_true", help="Markdown/JSON only")
    parser.add_argument("--check", action="store_true", help="Check only (pre-commit)")
    parser.add_argument(
        "--update-hooks", action="store_true", help="pre-commit autoupdate"
    )
    parser.add_argument("files", nargs="*", help="Specific files to format")

    args = parser.parse_args()

    run_all = not (args.backend or args.frontend or args.docs)
    format_backend = args.backend or run_all
    format_frontend = args.frontend or run_all
    format_docs = args.docs or run_all

    formatter = CodeFormatter(
        check_only=args.check, files=args.files if args.files else None
    )

    # Clear failed_tools at the start of a run
    formatter.failed_tools = []
    all_passed = True

    # Whitespace always first
    all_passed &= formatter.normalize_whitespace()

    if format_backend:
        all_passed &= formatter.format_python()

    if format_frontend:
        all_passed &= formatter.format_frontend()
        all_passed &= formatter.format_templates()

    if format_docs:
        all_passed &= formatter.format_docs()
    all_passed &= formatter.format_yaml()

    formatter.print_summary()

    # Cleanup
    print("\n" + "=" * 80)
    print(f"{BOLD}CLEANUP{RESET}")
    print("=" * 80)
    count = clean_caches(dry_run=False)
    if count:
        print(f"   {GREEN}✅ Removed {count} cache artifact(s){RESET}")
    else:
        print(f"   ✨ Repo already clean{RESET}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
