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

    TEXT_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".css",
            ".html",
            ".htm",
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

    def run_command(
        self,
        cmd: list[str],
        description: str,
        step: Optional[int] = None,
        total_steps: Optional[int] = None,
        suppress_output: bool = False,
        section: Optional[str] = None,
        section_idx: Optional[int] = None,
        section_total: Optional[int] = None,
    ) -> bool:
        """Run command with clean colored output + optional numbering and section
        headers."""
        if section and section_idx is not None and section_total is not None:
            header = (
                f"[{section.upper()} {section_idx}/{section_total}] {description}..."
            )
        elif step is not None and total_steps is not None:
            header = f"[FORMAT {step}/{total_steps}] {description}..."
        else:
            header = (
                "[FORMAT] " + description + "..."
                if not self.check_only
                else "[CHECK] " + description + "..."
            )
        print(f"\n{CYAN}{header}{RESET}")
        print(f"   {MAGENTA}Command: {' '.join(cmd)}{RESET}")

        try:
            env = os.environ.copy()
            scripts_dir = "Scripts" if sys.platform == "win32" else "bin"
            venv_scripts = self.root_dir / ".venv" / scripts_dir
            if venv_scripts.exists():
                path = env.get("PATH", "")
                env["PATH"] = f"{venv_scripts}{os.pathsep}{path}"
            env["PYTHONIOENCODING"] = "utf-8"

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

            if not suppress_output:
                output_printed = False
                if result.stdout.strip():
                    for line in result.stdout.strip().splitlines():
                        print(f"       {line}")
                    output_printed = True
                if result.stderr.strip():
                    for line in result.stderr.strip().splitlines():
                        print(f"       {line}", file=sys.stderr)
                    output_printed = True
                if result.returncode == 0 and not output_printed:
                    print("       All checks passed!")
            if result.returncode == 0:
                print(f"   {GREEN}✅ {description} — SUCCESS{RESET}")
                return True
            else:
                print(f"   {RED}❌ {description} — ISSUES FOUND{RESET}")
                # No warning line here, per user request
                self.errors.append(description)
                return False
        except FileNotFoundError:
            print(f"   {RED}❌ {description} — Tool not found{RESET}")
            self.errors.append(f"{description} (tool not found)")
            return False
        except Exception as e:
            print(f"   {RED}❌ {description} — Error: {e}{RESET}")
            self.errors.append(f"{description} ({e})")
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

    def _print_check_result(self, desc: str, success: bool) -> None:
        """Print standardized check result for every step."""
        if success:
            print(
                f"   {GREEN}✅ {desc} (check) — All issues fixed — "
                f"no further action needed.{RESET}"
            )
        else:
            print(
                f"   {RED}❌ {desc} (check) — Issues remain — "
                f"manual fix required.{RESET}"
            )

    def format_python(self) -> bool:
        """Python formatting with new header format."""
        targets = self._get_targets(
            (".py",), ["src", "tests", "scripts", "run.py", "apps"]
        )
        if not targets:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}BACKEND CODE FORMATTING{RESET}")
        print("=" * 80)
        ruff_cmd = ["ruff", "check"] + targets
        if not self.check_only:
            ruff_cmd.extend(["--fix", "--unsafe-fixes"])
        flake8_exclude = (
            "--exclude="
            ".venv,node_modules,__pycache__,.git,.pytest_cache,"
            "htmlcov,playwright-report"
        )
        steps = [
            ("Ruff linting & fixing", ruff_cmd),
            (
                "Import sorting (isort)",
                ["isort"] + targets + (["--check-only"] if self.check_only else []),
            ),
            (
                "Code formatting (black)",
                ["black"] + (["--check"] if self.check_only else []) + targets,
            ),
            (
                "Docstring formatting (docformatter)",
                ["docformatter"]
                + (["--check"] if self.check_only else ["--in-place"])
                + ["-r"]
                + targets,
            ),
            (
                "Final linting (flake8)",
                ["flake8"]
                + targets
                + [
                    flake8_exclude,
                    "--count",
                    "--show-source",
                    "--statistics",
                    "--max-line-length=88",
                ],
            ),
        ]
        all_passed = True
        failed_steps = []
        for idx, (desc, cmd) in enumerate(steps, 1):
            step_header = f"[BACKEND {idx}/{len(steps)}] {desc}"
            success, result = self._run_formatter_with_output(
                cmd,
                desc,
                idx,
                len(steps),
                indent=0,
                section="BACKEND",
                section_idx=idx,
                section_total=len(steps),
            )

            # Compute the canonical check command for this step (if available).
            check_cmd = self._get_check_cmd(desc, flake8_exclude)
            # If the initial run failed and a check command exists, always
            # print the compact 'check' invocation (Command 2) and the
            # standardized summary. This applies both in format mode and in
            # check-only mode so the user always sees Command 2 when the
            # tool reported issues.
            if not success:
                if check_cmd:
                    print("")
                    # Use the lower-level helper to print only the indented
                    # 'Command:' line (no cyan header) by passing
                    # suppress_summary=True and section=None. Then print the
                    # standardized check result using _print_check_result so
                    # the wording and layout match other tools.
                    check_success, _ = self._run_formatter_with_output(
                        check_cmd,
                        desc,
                        None,
                        None,
                        indent=0,
                        suppress_output=True,
                        print_command=True,
                        section=None,
                        section_idx=None,
                        section_total=None,
                        suppress_summary=True,
                    )
                    # Print standardized check result (indented)
                    self._print_check_result(desc, check_success)
                    if not check_success:
                        failed_steps.append((step_header, desc + " (check)", True))
                    success = check_success
                else:
                    failed_steps.append((step_header, desc, False))
            if not success and not any(s[0] == step_header for s in failed_steps):
                failed_steps.append((step_header, desc, False))
            all_passed &= success
        # Only keep the (check) failure if both main and check failed for a step
        deduped = {}
        for step_header, desc, is_check in failed_steps:
            if step_header not in deduped or is_check:
                deduped[step_header] = (desc, is_check)
        self.failed_tools = [(k, v[0], v[1]) for k, v in deduped.items()]
        return all_passed

    def _run_formatter_with_output(
        self,
        cmd,
        desc,
        step,
        total_steps,
        indent=0,
        suppress_output=False,
        print_command=True,
        section=None,
        section_idx=None,
        section_total=None,
        suppress_summary=False,
    ):
        """Run formatter and return (success, result).

        Handles output and indentation, with section-aware headers.
        """
        prefix = " " * indent
        if section and section_idx is not None and section_total is not None:
            header = f"[{section.upper()} {section_idx}/{section_total}] {desc}..."
            print(f"\n{CYAN}{header}{RESET}")
        elif step is not None and total_steps is not None:
            header = f"[FORMAT {step}/{total_steps}] {desc}..."
            print(f"\n{CYAN}{header}{RESET}")
        if print_command:
            print(f"{prefix}   {MAGENTA}Command: {' '.join(cmd)}{RESET}")
        try:
            env = os.environ.copy()
            scripts_dir = "Scripts" if sys.platform == "win32" else "bin"
            venv_scripts = self.root_dir / ".venv" / scripts_dir
            if venv_scripts.exists():
                path = env.get("PATH", "")
                env["PATH"] = f"{venv_scripts}{os.pathsep}{path}"
            env["PYTHONIOENCODING"] = "utf-8"
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
            if suppress_output:
                return (result.returncode == 0), result
            output_printed = False
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    print(f"{prefix}       {line}")
                output_printed = True
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines():
                    print(f"{prefix}       {line}", file=sys.stderr)
                output_printed = True
            if result.returncode == 0 and not output_printed:
                print(f"{prefix}       All checks passed!")
            is_check = desc.endswith("(check)")
            if not is_check and not suppress_summary:
                if result.returncode == 0:
                    print(f"{prefix}   {GREEN}✅ {desc} — SUCCESS{RESET}")
                else:
                    print(f"{prefix}   {RED}❌ {desc} — ISSUES FOUND{RESET}")
                    self.errors.append(desc)
            return (result.returncode == 0), result
        except Exception as e:
            print(f"{prefix}   {RED}❌ {desc} — ERROR: {e}{RESET}")
            self.errors.append(desc)
            return False, None

    def _get_check_cmd(self, desc, flake8_exclude):
        if desc == "Ruff linting & fixing":
            return ["ruff", "check"] + self._get_targets(
                (".py",), ["src", "tests", "scripts", "run.py", "apps"]
            )
        elif desc == "Import sorting (isort)":
            return (
                ["isort"]
                + self._get_targets(
                    (".py",), ["src", "tests", "scripts", "run.py", "apps"]
                )
                + ["--check-only"]
            )
        elif desc == "Code formatting (black)":
            return ["black", "--check"] + self._get_targets(
                (".py",), ["src", "tests", "scripts", "run.py", "apps"]
            )
        elif desc == "Docstring formatting (docformatter)":
            return ["docformatter", "--check", "-r"] + self._get_targets(
                (".py",), ["src", "tests", "scripts", "run.py", "apps"]
            )
        elif desc == "Final linting (flake8)":
            return (
                ["flake8"]
                + self._get_targets(
                    (".py",), ["src", "tests", "scripts", "run.py", "apps"]
                )
                + [
                    flake8_exclude,
                    "--count",
                    "--show-source",
                    "--statistics",
                    "--max-line-length=88",
                ]
            )
        return None

    def _check_prettier(self) -> bool:
        use_shell = sys.platform == "win32"
        result = subprocess.run(
            ["npm", "list", "prettier"],
            cwd=self.root_dir,
            capture_output=True,
            shell=use_shell,
            check=False,
        )
        if result.returncode != 0:
            return False
        # Check for prettier-plugin-yaml for YAML support
        plugin_result = subprocess.run(
            ["npm", "list", "prettier-plugin-yaml"],
            cwd=self.root_dir,
            capture_output=True,
            shell=use_shell,
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

    def format_frontend(self) -> bool:
        """Frontend formatting with new header format."""
        targets = self._get_targets(
            (".js", ".jsx", ".ts", ".tsx", ".css", ".scss"),
            [
                "src/static/js/**/*.js",
                "apps/**/*.js",
                "tests/**/*.js",
                "src/static/css/**/*.css",
                "apps/**/*.css",
            ],
        )
        if not targets:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}FRONTEND CODE FORMATTING{RESET}")
        print("=" * 80)
        if not self._check_prettier():
            print("   ℹ️  Prettier not installed — skipping frontend")
            return True
        args = ["npx", "prettier"]
        if self.check_only:
            args.append("--check")
        else:
            args.extend(["--write", "--log-level", "silent"])
        args.extend(targets)
        result = self.run_command(
            args,
            "JavaScript/CSS (prettier)",
            step=1,
            total_steps=1,
            section="FRONTEND",
            section_idx=1,
            section_total=1,
        )
        if not result:
            self.failed_tools.append(
                (
                    "[FRONTEND 1/1] JavaScript/CSS (prettier)",
                    "JavaScript/CSS (prettier)",
                    False,
                )
            )
        return result

    def format_docs(self) -> bool:
        """Documentation formatting (Markdown/JSON) with robust check/fix/check pattern
        and restored [DOCS 1/X] header."""
        doc_targets = self._get_targets(
            (".md", ".json"),
            [
                "docs/**/*.md",
                "*.md",
                "apps/**/*.md",
                "*.json",
                ".github/**/*.md",
            ],
        )
        if not doc_targets:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}DOCUMENTATION FORMATTING{RESET}")
        print("=" * 80)
        args_check = ["npx", "prettier", "--check"] + doc_targets
        args_fix = ["npx", "prettier", "--write", "--log-level", "silent"] + doc_targets
        step_header = "[DOCS 1/1] Markdown/JSON (prettier)"
        success = self.run_command(
            args_check,
            "Markdown/JSON (prettier)",
            step=1,
            total_steps=1,
            section="DOCS",
            section_idx=1,
            section_total=1,
        )
        if not success:
            self.run_command(
                args_fix,
                "Markdown/JSON (prettier) (fix)",
                step=1,
                total_steps=1,
                section="DOCS",
                section_idx=1,
                section_total=1,
            )
            print(f"\n   {MAGENTA}Command: {' '.join(args_check)}{RESET}")
            check_result = subprocess.run(
                args_check,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                env=os.environ.copy(),
                shell=(sys.platform == "win32" and args_check[0] in ("npm", "npx")),
            )
            if check_result.returncode == 0:
                print(
                    f"   {GREEN}✅ Markdown/JSON (prettier) — All issues fixed "
                    f"— SUCCESS{RESET}"
                )  # noqa: E501
                return True
            else:
                print(
                    f"   {RED}❌ Markdown/JSON (prettier) — Issues remain — "
                    f"manual fix required.{RESET}"
                )  # noqa: E501
                self.failed_tools.append(
                    (step_header, "Markdown/JSON (prettier)", False)
                )
                return False
        else:
            return True

    def format_yaml(self) -> bool:
        """YAML formatting and linting (Prettier + yamllint) with new header format."""
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
        args_check = ["npx", "prettier", "--check"] + yaml_files
        args_fix = ["npx", "prettier", "--write", "--log-level", "silent"] + yaml_files
        step_header = "[YAML 1/2] YAML (prettier)"
        failed_steps = []
        if self.check_only:
            # In check-only mode we only run the check command (no auto-fix).
            success = self.run_command(
                args_check,
                "YAML (prettier)",
                step=1,
                total_steps=2,
                section="YAML",
                section_idx=1,
                section_total=2,
            )
            if not success:
                failed_steps.append((step_header, "YAML (prettier)", True))
        else:
            # Command 1: run the formatter (write) so the user sees the format
            # step output first (matches other tools where formatting runs
            # before a separate check step).
            fmt_success, fmt_result = self._run_formatter_with_output(
                args_fix,
                "YAML (prettier)",
                1,
                2,
                indent=0,
                section="YAML",
                section_idx=1,
                section_total=2,
            )
            # Command 2: only run the check if the format (write) step reported
            # issues (matches pattern used by other tools: run formatter, then
            # re-check only if the formatter indicated problems).
            if not fmt_success:
                print("")
                prefix = "    "
                # Use run_command to print the standard header/command summary
                check_success = self.run_command(
                    args_check,
                    "YAML (prettier) (check)",
                    step=None,
                    total_steps=None,
                    suppress_output=True,
                    section="YAML",
                    section_idx=1,
                    section_total=2,
                )
                if check_success:
                    msg = "✅ YAML (prettier) — All issues fixed — SUCCESS"
                    print(prefix + GREEN + msg + RESET)
                else:
                    print(
                        f"{prefix}{RED}❌ YAML (prettier) — Issues remain — "
                        f"manual fix required.{RESET}"
                    )
                    failed_steps.append((step_header, "YAML (prettier)", False))
        # Add a blank line so the YAML prettier commands and yamllint are
        # visually separated in the terminal output (Command 1 vs Command 2 style).
        print("")
        yamllint_cmd = ["yamllint"] + yaml_files
        step_header_lint = "[YAML 2/2] YAML (yamllint)"
        # Use the centralized helper so yamllint stdout/stderr are printed
        success, lint_result = self._run_formatter_with_output(
            yamllint_cmd,
            "YAML (yamllint)",
            2,
            2,
            indent=0,
            section="YAML",
            section_idx=2,
            section_total=2,
            suppress_summary=True,
        )

        if lint_result is None:
            # Unexpected error running tool
            failed_steps.append((step_header_lint, "YAML (yamllint)", False))
            self.failed_tools.extend(failed_steps)
            return False

        output = (lint_result.stdout or "").lower()
        # If any 'error' or 'fatal' in output, treat as failure.
        # Otherwise, consider warnings only.
        if lint_result.returncode == 0:
            print(f"   {GREEN}✅ YAML (yamllint) — All issues fixed — SUCCESS{RESET}")
        else:
            has_errors = any(word in output for word in ("error", "fatal"))
            if has_errors or lint_result.returncode != 0:
                # Print a short failure summary for the initial run. The
                # detailed "manual fix required" message will be shown by the
                # compact check invocation (Command 2) below to match other
                # tools' output pattern.
                print(f"   {RED}❌ YAML (yamllint) — ISSUES FOUND{RESET}")
                failed_steps.append((step_header_lint, "YAML (yamllint)", False))
            else:
                print(
                    f"   {MAGENTA}⚠️  YAML (yamllint) — Warnings only (no errors)."
                    f"{RESET}"
                )
            # Print a separate 'check' command (Command 2) with an empty line
            # before it, matching the layout used by other tools: the first
            # run shows full diagnostics, then we show a compact 'check'
            # invocation and a standardized check result line.
            print("")
            # Run the compact 'check' invocation: print only the indented
            # Command: line (no repeated header), then report the standardized
            # check result.
            check_success, _ = self._run_formatter_with_output(
                yamllint_cmd,
                "YAML (yamllint)",
                None,
                None,
                indent=0,
                suppress_output=True,
                print_command=True,
                section=None,
                section_idx=None,
                section_total=None,
            )
            # Print standardized check result (matches other tools)
            self._print_check_result("YAML (yamllint)", check_success)
            if not check_success:
                # Replace any existing failed entry for this step so we don't
                # duplicate the same header in the final summary.
                replaced = False
                for i, (h, d, ic) in enumerate(failed_steps):
                    if h == step_header_lint:
                        failed_steps[i] = (
                            step_header_lint,
                            "YAML (yamllint) (check)",
                            True,
                        )
                        replaced = True
                        break
                if not replaced:
                    failed_steps.append(
                        (step_header_lint, "YAML (yamllint) (check)", True)
                    )
        self.failed_tools.extend(failed_steps)
        return not failed_steps

    def format_templates(self) -> bool:
        """Jinja2 templates with new header format."""
        targets = self._get_targets((".html", ".htm"), ["src/templates"])
        if not targets:
            return True
        print("\n" + "=" * 80)
        print(f"{BOLD}JINJA2 TEMPLATE FORMATTING{RESET}")
        print("=" * 80)
        python = sys.executable
        if self.check_only:
            cmd = [python, "-m", "djlint"] + targets + ["--check"]
        else:
            cmd = [python, "-m", "djlint"] + targets + ["--reformat", "--quiet"]
        return self.run_command(
            cmd,
            "Jinja2 templates (djlint)",
            step=1,
            total_steps=1,
            section="TEMPLATES",
            section_idx=1,
            section_total=1,
        )

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
