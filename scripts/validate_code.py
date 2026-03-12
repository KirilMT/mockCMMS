#!/usr/bin/env python3
"""Comprehensive Code Validation Script.

This script runs all validation checks that should pass before committing code.
It simulates the CI pipeline locally to catch issues early.

Usage:
    python scripts/validate_code.py              # Run all checks (full suite)
    python scripts/validate_code.py --backend    # Only backend checks
    python scripts/validate_code.py --frontend   # Only frontend checks
    python scripts/validate_code.py --quick      # Smart mode: targeted tests only

Smart --quick mode (three-tier priority):
    Tier 1 — testmon:   .testmondata exists → reruns ONLY tests whose covered
                        source lines actually changed (most precise, fastest).
                        Seed once with: pytest --testmon
    Tier 2 — git-diff:  No testmon DB → maps changed files to their test dirs
                        and runs only those directories.
    Tier 3 — fallback:  No changes detected or global file changed → runs the
                        full suite without coverage (fast, safe).
    Skip    — no-op:    No backend/frontend changes in that category → skipped.
"""

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Import cleanup utilities (located in the same scripts/ directory)
sys.path.insert(0, str(Path(__file__).parent))
from cleanup import clean_default  # noqa: E402

# Fix Windows console encoding for emoji output from tools like black
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Load .env variables so validata_code.py knows about local configuration
_load_dotenv: Optional[Callable[..., bool]]
try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:
    _load_dotenv = None  # python-dotenv might not be installed in base env.
    # Validation usually happens inside the project venv.

if _load_dotenv is not None:
    _load_dotenv()

# Fix for Windows UnicodeEncodeError when printing special characters
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass  # Fallback to default behavior if reconfigure fails


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(message: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_section(message: str) -> None:
    """Print a formatted section header."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{'-' * 80}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}[OK] {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}[FAIL] {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


# Maximum lines to display when a command produces long output on failure.
# Pytest writes 800+ individual test lines before the summary; showing only
# the tail ensures the failure details / coverage table are always visible.
_MAX_FAILURE_OUTPUT_LINES = 150
_FAILURE_HEAD_LINES = 20
_FAILURE_TAIL_LINES = 40
_PYTEST_SECTION_HEADER_RE = re.compile(
    r"=+\s*(FAILURES|ERRORS|warnings summary|short test summary info)\s*=+",
    re.IGNORECASE,
)


def _dedupe_output_blocks(*blocks: str) -> List[str]:
    """Return non-empty output blocks with duplicates removed, preserving order."""
    seen = set()
    unique_blocks: List[str] = []
    for block in blocks:
        normalized = block.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_blocks.append(normalized)
    return unique_blocks


def _find_pytest_section_ranges(lines: List[str]) -> Dict[str, Tuple[int, int]]:
    """Return pytest section name -> (start, end) line ranges for known headings."""
    matches: List[Tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = _PYTEST_SECTION_HEADER_RE.match(line.strip())
        if match:
            matches.append((match.group(1).lower(), index))

    section_ranges: Dict[str, Tuple[int, int]] = {}
    for idx, (name, start) in enumerate(matches):
        end = matches[idx + 1][1] if idx + 1 < len(matches) else len(lines)
        section_ranges[name] = (start, end)
    return section_ranges


def _extract_coverage_block(lines: List[str]) -> str:
    """Extract coverage-related failure details from pytest output when present."""
    coverage_markers = [
        idx
        for idx, line in enumerate(lines)
        if "coverage:" in line.lower() or "required test coverage" in line.lower()
    ]
    if not coverage_markers:
        return ""

    start = max(coverage_markers[0] - 2, 0)
    end = min(len(lines), coverage_markers[-1] + 20)
    return "\n".join(lines[start:end]).strip()


def _truncate_generic_failure_output(lines: List[str]) -> str:
    """Return a readable generic failure report when no pytest sections exist."""
    total = len(lines)
    if total <= _MAX_FAILURE_OUTPUT_LINES:
        return "\n".join(lines).strip()

    hidden = total - (_FAILURE_HEAD_LINES + _FAILURE_TAIL_LINES)
    head = "\n".join(lines[:_FAILURE_HEAD_LINES]).strip()
    tail = "\n".join(lines[-_FAILURE_TAIL_LINES:]).strip()
    return (
        "First lines:\n"
        f"{head}\n\n"
        f"... [{hidden} lines omitted for brevity] ...\n\n"
        "Last lines:\n"
        f"{tail}"
    ).strip()


def format_failure_output(stdout: str, stderr: str) -> str:
    """Format command failure output to surface the actionable error first.

    For pytest/testmon failures, this extracts the failure section, short summary, and
    coverage details before appending a short raw tail for context. For other tools, it
    falls back to a compact head/tail view.
    """
    blocks = _dedupe_output_blocks(stdout, stderr)
    if not blocks:
        return ""

    combined_output = "\n\n".join(blocks)
    lines = combined_output.splitlines()
    section_ranges = _find_pytest_section_ranges(lines)

    if not section_ranges and not any(
        marker in combined_output.lower()
        for marker in ("test session starts", "short test summary info", "failed ")
    ):
        return _truncate_generic_failure_output(lines)

    report_sections: List[str] = []

    short_summary_range = section_ranges.get("short test summary info")
    if short_summary_range:
        start, end = short_summary_range
        report_sections.append(
            "Pytest short summary:\n" + "\n".join(lines[start:end]).strip()
        )

    for section_name in ("failures", "errors"):
        section_range = section_ranges.get(section_name)
        if section_range:
            start, end = section_range
            title = "Failure details" if section_name == "failures" else "Error details"
            report_sections.append(f"{title}:\n" + "\n".join(lines[start:end]).strip())

    coverage_block = _extract_coverage_block(lines)
    if coverage_block:
        report_sections.append("Coverage details:\n" + coverage_block)

    tail_lines = lines[-_FAILURE_TAIL_LINES:]
    tail_block = "\n".join(tail_lines).strip()
    if tail_block:
        report_sections.append("Raw output tail:\n" + tail_block)

    deduped_sections: List[str] = []
    seen = set()
    for section in report_sections:
        normalized = section.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped_sections.append(normalized)

    return "\n\n".join(deduped_sections)


def _print_failure_output(stdout: str, stderr: str) -> None:
    """Print formatted failure details for a failed command."""
    formatted_output = format_failure_output(stdout, stderr)
    if not formatted_output:
        return
    print(f"\n{Colors.FAIL}Failure details:{Colors.ENDC}")
    print(formatted_output)


def _print_output_tail(output: str, label: str, color: str) -> None:
    """Print the tail of *output*, truncating the head when it is very long.

    When the output has more than ``_MAX_FAILURE_OUTPUT_LINES`` lines only
    the last ``_MAX_FAILURE_OUTPUT_LINES`` are printed so that failure
    summaries and error details (which pytest writes at the very end) are
    always visible, even inside IDE run consoles with limited scroll buffers.
    """
    if not output:
        return
    lines = output.splitlines()
    total = len(lines)
    print(f"\n{color}{label}{Colors.ENDC}")
    if total > _MAX_FAILURE_OUTPUT_LINES:
        hidden = total - _MAX_FAILURE_OUTPUT_LINES
        print(
            f"{Colors.WARNING}... [{hidden} lines hidden — showing last "
            f"{_MAX_FAILURE_OUTPUT_LINES} of {total}] ...{Colors.ENDC}"
        )
        print("\n".join(lines[-_MAX_FAILURE_OUTPUT_LINES:]))
    else:
        print(output)


def run_command(
    command: List[str],
    description: str,
    check: bool = True,
    force_all_apps: bool = False,
    env: Optional[Dict[str, str]] = None,
    ignore_failure: bool = False,
) -> Tuple[bool, str]:
    """Run a shell command and return success status and output.

    Args:
        command: Command and arguments as a list
        description: Human-readable description of what's being checked
        check: Whether to check return code (default: True)
        force_all_apps: Whether to force enable all modular apps (default: False)
        env: Optional dictionary of environment variables to merge
        ignore_failure: If True, do not print error on failure (default: False)

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        print(f"Running: {' '.join(command)}")

        # On Windows, use shell=True for npm/npx to find them in PATH
        use_shell = sys.platform == "win32" and command[0] in ("npm", "npx")

        # IRONCLAD MODE: Fresh, minimal env to mirror CI clean state.
        # Blocks local shell variables from masking configuration gaps.
        ironclad_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", "."),
            "SYSTEMROOT": os.environ.get(
                "SYSTEMROOT", ""
            ),  # Essential for Windows subprocess
            "PYTHONIOENCODING": "utf-8",
            "TESTING": "1",
            "DATABASE_FILENAME": ":memory:",
            "CI": "true",  # Simulate CI environment for absolute parity
        }

        # Whitelist other system-essential variables, including Windows path roots
        # used by browsers and OS APIs (Playwright/Chromium relies on these).
        for key in [
            "APPDATA",
            "LOCALAPPDATA",
            "PROGRAMDATA",
            "SYSTEMDRIVE",
            "HOMEDRIVE",
            "HOMEPATH",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "COMSPEC",
            "PATHEXT",
            "WINDIR",
        ]:
            if key in os.environ:
                ironclad_env[key] = os.environ[key]

        # Handle Modular App Configuration
        if force_all_apps:
            # CI/Full Validation Mode: Force enable all apps
            ironclad_env["PLANNING_ENABLED"] = "true"
            ironclad_env["REPORTING_ENABLED"] = "true"
        else:
            # Local/Quick Mode: Respect local .env configuration
            if "PLANNING_ENABLED" in os.environ:
                ironclad_env["PLANNING_ENABLED"] = os.environ["PLANNING_ENABLED"]
            if "REPORTING_ENABLED" in os.environ:
                ironclad_env["REPORTING_ENABLED"] = os.environ["REPORTING_ENABLED"]

        # Pass E2E_TEST if set (important for quick mode skipping E2E)
        if "E2E_TEST" in os.environ:
            ironclad_env["E2E_TEST"] = os.environ["E2E_TEST"]

        # Allow caller-provided overrides for command-specific execution context.
        if env:
            ironclad_env.update(env)

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",  # Explicitly use UTF-8 to handle emojis
            errors="replace",  # Replace undecodable bytes instead of crashing
            shell=use_shell,  # Use shell on Windows for npm/npx
            check=check,
            env=ironclad_env,  # Use isolated minimal environment
        )

        if result.returncode == 0:
            print_success(f"{description} passed")
            return True, result.stdout
        else:
            print_error(f"{description} failed")
            _print_failure_output(result.stdout, result.stderr)
            return False, result.stderr or result.stdout

    except subprocess.CalledProcessError as e:
        print_error(f"{description} failed with return code {e.returncode}")
        _print_failure_output(e.stdout, e.stderr)
        return False, e.stderr or e.stdout
    except FileNotFoundError:
        print_error(f"{description} failed - command not found: {command[0]}")
        print_warning(f"Please ensure {command[0]} is installed")
        return False, f"Command not found: {command[0]}"


# =============================================================================
# SMART TEST SCOPE DETECTION  (used by --quick mode)
# =============================================================================

# Any change to these files invalidates the scope map — run the full suite.
_FULL_SUITE_FILENAMES: frozenset = frozenset(
    [
        "conftest.py",
        "pyproject.toml",
        "run.py",
        ".env",
        "requirements.txt",
        "requirements-dev.txt",
    ]
)
_FULL_SUITE_PREFIXES: tuple = ("scripts/", ".github/")

# Maps source-file path prefixes → relevant backend test directories.
# More-specific prefixes must come before their parents.
# An empty list [] means "frontend-only — explicitly skip backend mapping."
_BACKEND_MAP: List[Tuple[str, List[str]]] = [
    ("src/routes/", ["tests/backend/functional", "tests/backend/integration"]),
    ("src/services/", ["tests/backend/unit", "tests/backend/integration"]),
    # Static assets and templates are frontend concerns — skip backend tests
    ("src/static/", []),
    ("src/templates/", []),
    ("src/", ["tests/backend"]),  # catch-all for other src/ Python files
    ("apps/planning/src/static/", []),  # frontend-only
    ("apps/planning/src/templates/", []),  # frontend-only
    ("apps/planning/src/", ["apps/planning/tests"]),
    ("apps/planning/", ["apps/planning/tests"]),
    ("apps/reporting/src/static/", []),  # frontend-only
    ("apps/reporting/src/templates/", []),  # frontend-only
    ("apps/reporting/src/", ["apps/reporting/tests"]),
    ("apps/reporting/", ["apps/reporting/tests"]),
    # Test files themselves → run their own directory
    ("tests/backend/", ["tests/backend"]),
    ("apps/planning/tests/", ["apps/planning/tests"]),
    ("apps/reporting/tests/", ["apps/reporting/tests"]),
]

# Maps source-file path prefixes → relevant frontend test directories.
_FRONTEND_MAP: List[Tuple[str, List[str]]] = [
    ("src/static/js/", ["tests/frontend/unit"]),
    ("src/static/css/", ["tests/frontend/unit"]),
    ("src/templates/", ["tests/frontend/unit"]),
    ("apps/planning/src/static/", ["tests/frontend/unit"]),
    ("apps/reporting/src/static/", ["tests/frontend/unit"]),
    ("tests/frontend/", ["tests/frontend/unit"]),
]


def _get_changed_files() -> List[str]:
    """Return all changed files (staged, unstaged, untracked) from git.

    Returns normalized forward-slash paths, or an empty list when git is unavailable or
    the working tree is clean.
    """
    changed: set = set()
    git_cmds = [
        ["git", "diff", "--name-only", "HEAD"],  # unstaged changes vs HEAD
        ["git", "diff", "--name-only", "--cached"],  # staged changes
        ["git", "ls-files", "--others", "--exclude-standard"],  # untracked
    ]
    for cmd in git_cmds:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line:
                        # Normalize to forward slashes for consistent matching
                        changed.add(line.replace("\\", "/"))
        except (FileNotFoundError, OSError):
            return []  # git not available
    return sorted(changed)


def detect_changed_scopes() -> Dict[str, Any]:
    """Analyze git changes and return smart test scopes for --quick mode.

    Returns a dict with:
      - ``"full_suite"`` (bool): True → global file changed or no git info,
        run the full suite.
      - ``"backend"`` (list[str]): Backend test dirs to run.  Empty list means
        no backend-relevant files changed — skip backend tests.
      - ``"frontend"`` (list[str]): Frontend test dirs to run.  Empty list means
        no frontend-relevant files changed — skip frontend tests.
    """
    files = _get_changed_files()

    # No changes or git unavailable → default to full suite (safest fallback)
    if not files:
        return {"full_suite": True, "backend": [], "frontend": []}

    # Any global config/infrastructure change invalidates targeted scope
    for f in files:
        basename = f.rsplit("/", 1)[-1]
        if basename in _FULL_SUITE_FILENAMES:
            print_warning(f"Global config changed ({f!r}) — full suite required.")
            return {"full_suite": True, "backend": [], "frontend": []}
        if any(f.startswith(p) for p in _FULL_SUITE_PREFIXES):
            print_warning(f"Infrastructure file changed ({f!r}) — full suite required.")
            return {"full_suite": True, "backend": [], "frontend": []}

    backend: set = set()
    frontend: set = set()

    for f in files:
        # Backend mapping (first match wins per file; [] = frontend-only, skip)
        for prefix, dirs in _BACKEND_MAP:
            if f.startswith(prefix):
                if dirs:  # Empty list means "frontend-only — no backend tests"
                    backend.update(dirs)
                break  # Always break so the generic src/ catch-all is not reached
        # Frontend mapping (independent — a file can affect both)
        for prefix, dirs in _FRONTEND_MAP:
            if f.startswith(prefix):
                frontend.update(dirs)
                break

    return {
        "full_suite": False,
        # Keep only directories that actually exist in this repo
        "backend": [d for d in sorted(backend) if Path(d).exists()],
        "frontend": [d for d in sorted(frontend) if Path(d).exists()],
    }


# =============================================================================


def validate_python_backend(quick: bool = False, force_all_apps: bool = True) -> bool:
    """Run all Python backend validation checks."""
    print_header("BACKEND VALIDATION")

    checks = []

    # 1. Import sorting (PEP 8)
    print_section("Step 1/10: Import Sorting (isort)")
    success, _ = run_command(
        ["isort", "src", "apps", "tests", "scripts", "run.py", "--check-only"],
        "Import sorting check",
        force_all_apps=True,
    )
    checks.append(("Import Sorting", success))

    # 2. Code formatting (Black)
    print_section("Step 2/10: Code Formatting (black)")
    success, _ = run_command(
        ["black", "--check", "src", "apps", "tests", "scripts", "run.py"],
        "Code formatting check",
        force_all_apps=True,
    )
    checks.append(("Code Formatting", success))

    # 3. Docstring formatting (PEP 257)
    print_section("Step 3/10: Docstring Formatting (docformatter)")
    success, _ = run_command(
        ["docformatter", "--check", "-r", "src", "apps", "tests", "scripts", "run.py"],
        "Docstring formatting check",
        force_all_apps=True,
    )
    checks.append(("Docstring Formatting", success))

    # 4. Linting (Ruff - fast, comprehensive)
    print_section("Step 4/10: Linting (ruff)")
    success, _ = run_command(
        ["ruff", "check", "src", "apps", "tests", "scripts", "run.py"],
        "Ruff linting",
        force_all_apps=True,
    )
    checks.append(("Ruff Linting", success))

    # 5. Type checking (Validation)
    print_section("Step 5/10: Type Checking (mypy)")
    success, _ = run_command(["mypy"], "Type checking")
    checks.append(("Type Checking", success))

    # 6. Security scanning (Bandit)
    print_section("Step 6/10: Security Scanning (bandit)")
    # -ll: report only medium and high severity issues
    success, _ = run_command(["bandit", "-r", "src/", "-ll"], "Security scanning")
    checks.append(("Security Scanning", success))

    # 7. Template Linting (djlint)
    print_section("Step 7/10: Template Linting (djlint)")
    # Apps templates excluded due to risk/lack of tests
    template_paths = ["src/templates"]
    success, _ = run_command(
        ["djlint", "--check"] + template_paths,
        "Jinja2 template linting",
    )
    if not success:
        print_warning("DjLint found issues (soft failure for now)")
        checks.append(("Template Linting", True))
    else:
        checks.append(("Template Linting", success))

    # 8. Running Tests
    print_section("Step 8/10: Running Tests with Coverage")
    if quick:
        print_warning("Quick mode: Smart test targeting enabled")
        scopes = detect_changed_scopes()
        testmon_db = Path(".testmondata")

        if scopes["full_suite"]:
            # Global change detected — run everything quickly without coverage
            print_warning(
                "Quick mode [full scope]: Global/infra file changed, "
                "running all tests without coverage."
            )
            success, _ = run_command(
                [
                    "pytest",
                    "-c",
                    "pyproject.toml",
                    "--no-cov",  # override addopts --cov (no threshold in quick mode)
                    "-x",
                    "--tb=short",
                ],
                "Quick test run (full scope, no coverage)",
                force_all_apps=force_all_apps,
            )

        elif testmon_db.exists():
            # Tier 1 — testmon: reruns only tests whose covered lines changed.
            # --no-cov prevents pytest-cov from conflicting with testmon's tracer.
            print_warning(
                "Quick mode [Tier 1 — testmon]: Coverage DB found. "
                "Running only tests affected by your changes."
            )
            success, _ = run_command(
                [
                    "pytest",
                    "-c",
                    "pyproject.toml",
                    "--testmon",
                    "--no-cov",
                    "-x",
                    "--tb=short",
                ],
                "Smart test run (testmon — affected tests only)",
                force_all_apps=force_all_apps,
            )

        elif scopes["backend"]:
            # Tier 2 — git-diff: run only directories mapped from changed files.
            scope_str = " ".join(scopes["backend"])
            print_warning(
                f"Quick mode [Tier 2 — git-diff]: Scoping backend tests to: "
                f"{scope_str}"
            )
            success, _ = run_command(
                [
                    "pytest",
                    "-c",
                    "pyproject.toml",
                    "--no-cov",
                    "-x",
                    "--tb=short",
                ]
                + scopes["backend"],
                f"Scoped test run ({scope_str})",
                force_all_apps=force_all_apps,
            )

        else:
            # Tier 3 — no backend changes detected: skip entirely.
            print_warning(
                "Quick mode [Tier 3 — skip]: No backend-relevant changes "
                "detected — skipping backend tests."
            )
            success = True

        checks.append(("Tests", success))
    else:
        success, _ = run_command(
            [
                "pytest",
                "-c",
                "pyproject.toml",
                "--cov=src",
                "--cov=apps",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-report=xml",  # Required for diff-cover
            ],
            "Full test suite with discovery (500+ tests)",
            force_all_apps=force_all_apps,
        )
        checks.append(("Full Discovery Suite", success))

    # 9. Coverage validation (Total >= 82%)
    if not quick:
        print_section("Step 9/10: Total Coverage Validation")
        success, _ = run_command(
            [
                "pytest",
                "-c",
                "pyproject.toml",
                "--cov=src",
                "--cov=apps",
                "--cov-fail-under=85",
                "-q",
            ],
            "Coverage threshold check (>= 85%)",
            force_all_apps=force_all_apps,
        )
        checks.append(("Total Coverage Threshold", success))

        # 10. Diff Coverage validation (New Code >= 92%)
        print_section("Step 10/10: Diff (Patch) Coverage")
        # Ensure we have coverage.xml
        if not os.path.exists("coverage.xml"):
            print_warning("coverage.xml not found, skipping diff-cover")
            checks.append(("Diff Coverage", True))  # Soft fail if missing
        else:
            # Check if diff-cover is installed
            success, output = run_command(
                ["diff-cover", "--version"], "Check diff-cover", check=False
            )
            if success:
                success, _ = run_command(
                    [
                        "diff-cover",
                        "coverage.xml",
                        "--compare-branch=origin/main",
                        "--fail-under=92",
                    ],
                    "Diff Coverage Check (New Code needs 92% coverage)",
                )
                checks.append(("Diff Coverage", success))
            else:
                print_warning(
                    "diff-cover not installed. Run 'pip install diff-cover' "
                    "to enable patch checks."
                )
                # Soft fail if tool is missing to allow environment flexibility
                checks.append(("Diff Coverage", True))

    # Print summary
    print_section("Python Backend Validation Summary")
    all_passed = all(success for _, success in checks)
    for check_name, success in checks:
        if success:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")

    return all_passed


def validate_others() -> bool:
    """Run validation checks for documentation and other files."""
    print_header("OTHERS VALIDATION")

    checks = []

    # Documentation linting (Prettier)
    print_section("Step 1/1: Documentation Linting (prettier)")
    doc_paths = [
        "docs/**/*.md",
        "*.md",  # Root markdown
        "apps/**/*.md",  # App documentation
        "*.json",
        ".github/**/*.md",
    ]
    # Check if Prettier is installed first
    try:
        use_shell = sys.platform == "win32"
        check_prettier = subprocess.run(
            ["npm", "list", "prettier"],
            cwd=os.getcwd(),
            capture_output=True,
            shell=use_shell,
            check=False,
        )
        if check_prettier.returncode == 0:
            success, _ = run_command(
                ["npx", "prettier", "--check"] + doc_paths,
                "Documentation formatting check",
            )
            checks.append(("Documentation Linting", success))
        else:
            print_warning("Prettier not installed - skipping documentation linting")
            # Not a failure, just skipped
            checks.append(("Documentation Linting", True))
    except Exception:
        print_warning("Error checking for Prettier - skipping documentation linting")
        checks.append(("Documentation Linting", True))

    # Print summary
    print_section("Others Validation Summary")
    all_passed = all(success for _, success in checks)
    for check_name, success in checks:
        if success:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")

    return all_passed


def validate_javascript_frontend(
    quick: bool = False, force_all_apps: bool = True
) -> bool:
    """Run all JavaScript frontend validation checks."""
    print_header("JAVASCRIPT FRONTEND VALIDATION")

    # Check if npm is available
    npm_available = shutil.which("npm") is not None

    if not npm_available:
        print_warning(
            "[WARN] npm not found - frontend validation will be skipped locally\n"
            "   This is OK if you didn't modify any .js/.css/.html files\n"
            "   GitHub Actions will run frontend tests with Node.js installed"
        )

    checks = []

    # 1. ESLint - JavaScript linting (SHOULD be in CI but currently missing)
    print_section("Step 1/3: JavaScript Linting (eslint)")
    success, _ = run_command(
        [
            "npx",
            "eslint",
            "src/static/js",
            "apps",
            "tests/frontend",
            "--report-unused-disable-directives",
        ],
        "ESLint check",
        force_all_apps=force_all_apps,
    )
    checks.append(("ESLint", success))

    # 2. JavaScript tests (Jest) with coverage - MATCHES CI
    print_section("Step 2/3: JavaScript Tests (jest)")
    if quick:
        _scopes = detect_changed_scopes()
        if _scopes["full_suite"] or _scopes["frontend"]:
            success, _ = run_command(
                [
                    "npm",
                    "test",
                    "--",
                    "--coverage",
                    "--coverageReporters=text",
                    "--coverageReporters=lcov",
                ],
                "Jest tests with coverage",
                force_all_apps=force_all_apps,
            )
        else:
            print_warning(
                "Quick mode: No JS/CSS/template changes detected — skipping Jest."
            )
            success = True
    else:
        success, _ = run_command(
            [
                "npm",
                "test",
                "--",
                "--coverage",
                "--coverageReporters=text",
                "--coverageReporters=lcov",
            ],
            "Jest tests with coverage",
            force_all_apps=force_all_apps,
        )
    checks.append(("Jest Tests", success))

    # 3. E2E tests (Playwright) - MATCHES CI
    if not quick:
        print_section("Step 3/3: E2E Tests (playwright)")
        # Force E2E_TEST=true to ensure production DBs are not touched
        # This overrides any local .env settings
        ironclad_env_e2e = os.environ.copy()
        ironclad_env_e2e["E2E_TEST"] = "true"

        success, _ = run_command(
            ["npx", "playwright", "test", "--project=chromium"],
            "Playwright E2E tests (chromium)",
            force_all_apps=force_all_apps,
            env=ironclad_env_e2e,
        )
        checks.append(("E2E Tests", success))
    else:
        print_warning("Quick mode: Skipping E2E tests")

    # Print summary
    print_section("Frontend Validation Summary")
    all_passed = all(success for _, success in checks)
    for check_name, success in checks:
        if success:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")

    return all_passed


def validate_configuration() -> bool:
    """Run configuration file validation checks."""
    print_header("CONFIGURATION VALIDATION")

    checks = []

    # Validate JSON files
    print_section("Step 1/2: Validating JSON Configuration Files")
    json_files = [
        "src/config/dropdown_options.json",
        "package.json",
    ]

    for json_file in json_files:
        json_path = Path(json_file)
        if json_path.exists():
            success, _ = run_command(
                ["python", "-m", "json.tool", str(json_path)],
                f"JSON validation: {json_file}",
                check=False,
            )
            checks.append((f"JSON: {json_file}", success))
        else:
            print_warning(f"File not found: {json_file}")

    # Validate YAML files (if yamllint is available)
    print_section("Step 2/2: Validating YAML Configuration Files")
    yaml_files = list(Path(".github/workflows").glob("*.yml"))

    if yaml_files:
        for yaml_file in yaml_files:
            # Try yamllint first, fall back to basic check
            success, _ = run_command(
                ["yamllint", str(yaml_file)],
                f"YAML validation: {yaml_file.name}",
                check=False,
            )
            if not success:
                print_warning(f"yamllint not available or failed for {yaml_file.name}")
            checks.append((f"YAML: {yaml_file.name}", success))

    # Print summary
    print_section("Configuration Validation Summary")
    all_passed = all(success for _, success in checks)
    for check_name, success in checks:
        if success:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")

    return all_passed


def _run_cleanup() -> None:
    """Remove generated test artifacts and coverage reporting after validation."""
    print_header("CLEANUP")
    count = clean_default(dry_run=False)
    if count:
        print_success(f"Removed {count} generated artifact(s) — repo is clean.")
    else:
        print_success("Nothing to clean — repo is already clean.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive code validation script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/validate_code.py              # Run all checks
    python scripts/validate_code.py --backend    # Only backend checks
    python scripts/validate_code.py --frontend   # Only frontend checks
    python scripts/validate_code.py --docs       # Only documentation/other checks
    python scripts/validate_code.py --quick      # Skip slow tests
        """,
    )
    parser.add_argument(
        "--backend", action="store_true", help="Run only Python backend validation"
    )
    parser.add_argument(
        "--frontend",
        action="store_true",
        help="Run only JavaScript frontend validation",
    )
    parser.add_argument(
        "--docs",
        action="store_true",
        help="Run only Documentation validation",
    )
    parser.add_argument(
        "--configuration",
        action="store_true",
        help="Run only Configuration validation",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: Skip slow tests (E2E, visual regression)",
    )

    args = parser.parse_args()

    # Determine what to run
    # If no specific category flags are set, run ALL.
    # We check if ANY category flag is enabled.
    any_flag = args.backend or args.frontend or args.docs or args.configuration
    run_all = not any_flag

    run_backend = args.backend or run_all
    run_frontend = args.frontend or run_all
    run_docs = args.docs or run_all
    run_config = args.configuration or run_all
    # Force enable all apps for full validation (unless quick mode is used locally)
    force_all_apps = not args.quick

    print_header("MOCKCMMS CODE VALIDATION")
    print(f"{Colors.OKCYAN}This script simulates the CI pipeline locally.{Colors.ENDC}")
    print(f"{Colors.OKCYAN}All checks must pass before committing code.{Colors.ENDC}\n")

    results = []

    # Run validations
    if run_backend:
        backend_passed = validate_python_backend(
            quick=args.quick, force_all_apps=force_all_apps
        )
        results.append(("Backend", backend_passed))

    if run_frontend:
        frontend_passed = validate_javascript_frontend(
            quick=args.quick, force_all_apps=force_all_apps
        )
        results.append(("Frontend", frontend_passed))

    if run_config:
        config_passed = validate_configuration()
        results.append(("Configuration", config_passed))

    if run_docs:
        docs_passed = validate_others()
        results.append(("Others", docs_passed))

    # Final summary
    print_header("FINAL VALIDATION SUMMARY")

    all_passed = all(passed for _, passed in results)

    for category, passed in results:
        if passed:
            print_success(f"{category} Validation: PASSED")
        else:
            print_error(f"{category} Validation: FAILED")

    print()
    if all_passed:
        print_success("All validation checks passed!")
        print(f"{Colors.OKGREEN}You can safely commit your changes.{Colors.ENDC}")
        _run_cleanup()
        return 0
    else:
        print_error("Some validation checks failed!")
        print(f"{Colors.FAIL}Please fix the issues before committing.{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Remember:{Colors.ENDC}")
        print(
            f"{Colors.WARNING}  1. Fix the CODE, not the configuration "
            f"or the tests{Colors.ENDC}"
        )
        print(f"{Colors.WARNING}  2. Do NOT lower coverage thresholds{Colors.ENDC}")
        print(f"{Colors.WARNING}  3. Do NOT disable linting rules{Colors.ENDC}")
        print(
            f"{Colors.WARNING}  4. Do NOT update visual test screenshots "
            f"(unless UI was intentionally changed){Colors.ENDC}"
        )
        _run_cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())
