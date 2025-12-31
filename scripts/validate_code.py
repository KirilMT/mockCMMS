#!/usr/bin/env python3
"""
Comprehensive Code Validation Script

This script runs all validation checks that should pass before committing code.
It simulates the CI pipeline locally to catch issues early.

Usage:
    python scripts/validate_code.py              # Run all checks
    python scripts/validate_code.py --backend    # Only backend checks
    python scripts/validate_code.py --frontend   # Only frontend checks
    python scripts/validate_code.py --quick      # Skip slow tests
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_section(message: str) -> None:
    """Print a formatted section header."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{'─' * 80}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{'─' * 80}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def run_command(command: List[str], description: str, check: bool = True) -> Tuple[bool, str]:
    """
    Run a shell command and return success status and output.

    Args:
        command: Command and arguments as a list
        description: Human-readable description of what's being checked
        check: Whether to check return code (default: True)

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        print(f"Running: {' '.join(command)}")

        # On Windows, use shell=True for npm/npx to find them in PATH
        use_shell = sys.platform == 'win32' and command[0] in ('npm', 'npx')

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Explicitly use UTF-8 to handle emojis
            errors='replace',  # Replace undecodable bytes instead of crashing
            shell=use_shell,  # Use shell on Windows for npm/npx
            check=check
        )

        if result.returncode == 0:
            print_success(f"{description} passed")
            return True, result.stdout
        else:
            print_error(f"{description} failed")
            print(f"\n{Colors.WARNING}Output:{Colors.ENDC}")
            print(result.stdout)
            if result.stderr:
                print(f"\n{Colors.FAIL}Errors:{Colors.ENDC}")
                print(result.stderr)
            return False, result.stderr or result.stdout

    except subprocess.CalledProcessError as e:
        print_error(f"{description} failed with return code {e.returncode}")
        print(f"\n{Colors.WARNING}Output:{Colors.ENDC}")
        print(e.stdout)
        if e.stderr:
            print(f"\n{Colors.FAIL}Errors:{Colors.ENDC}")
            print(e.stderr)
        return False, e.stderr or e.stdout
    except FileNotFoundError:
        print_error(f"{description} failed - command not found: {command[0]}")
        print_warning(f"Please ensure {command[0]} is installed")
        return False, f"Command not found: {command[0]}"


def validate_python_backend(quick: bool = False) -> bool:
    """Run all Python backend validation checks."""
    print_header("PYTHON BACKEND VALIDATION")

    checks = []

    # 1. Import sorting (PEP 8)
    print_section("Step 1/9: Import Sorting (isort)")
    success, _ = run_command(
        ["isort", "src/", "tests/", "--check-only"],
        "Import sorting check"
    )
    checks.append(("Import Sorting", success))

    # 2. Code formatting (Black)
    print_section("Step 2/9: Code Formatting (black)")
    success, _ = run_command(
        ["black", "src/", "tests/", "--check"],
        "Code formatting check"
    )
    checks.append(("Code Formatting", success))

    # 3. Docstring formatting (PEP 257)
    print_section("Step 3/9: Docstring Formatting (docformatter)")
    success, _ = run_command(
        ["docformatter", "--check", "-r", "src/", "tests/"],
        "Docstring formatting check"
    )
    checks.append(("Docstring Formatting", success))

    # 4. Linting (Ruff - fast, comprehensive)
    print_section("Step 4/9: Linting (ruff)")
    success, _ = run_command(
        ["ruff", "check", "src/", "tests/"],
        "Ruff linting"
    )
    checks.append(("Ruff Linting", success))

    # 5. Additional linting (Flake8)
    print_section("Step 5/9: Additional Linting (flake8)")
    success, _ = run_command(
        ["flake8", "src/", "tests/"],
        "Flake8 linting"
    )
    checks.append(("Flake8 Linting", success))

    # 6. Type checking (mypy)
    print_section("Step 6/9: Type Checking (mypy)")
    success, _ = run_command(
        ["mypy"],  # Uses pyproject.toml config (files = ["src"])
        "Type checking"
    )
    checks.append(("Type Checking", success))

    # 7. Security scanning (Bandit)
    print_section("Step 7/9: Security Scanning (bandit)")
    success, _ = run_command(
        ["bandit", "-r", "src/", "-ll"],
        "Security scanning"
    )
    checks.append(("Security Scanning", success))

    # 8. Run all tests with coverage
    print_section("Step 8/9: Running Tests with Coverage")
    if quick:
        print_warning("Quick mode: Skipping full test suite")
        success, _ = run_command(
            ["pytest", "tests/", "-x", "--tb=short"],
            "Quick test run"
        )
        checks.append(("Tests", success))
    else:
        success, _ = run_command(
            ["pytest", "tests/", "--cov=src", "--cov-report=term-missing"],
            "Full test suite with coverage"
        )
        checks.append(("Tests with Coverage", success))

    # 9. Coverage validation (must be >= 82%)
    if not quick:
        print_section("Step 9/9: Coverage Validation")
        success, _ = run_command(
            ["pytest", "tests/", "--cov=src", "--cov-fail-under=82", "-q"],
            "Coverage threshold check (>= 82%)"
        )
        checks.append(("Coverage Threshold", success))

    # Print summary
    print_section("Python Backend Validation Summary")
    all_passed = all(success for _, success in checks)
    for check_name, success in checks:
        if success:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")

    return all_passed


def validate_javascript_frontend(quick: bool = False) -> bool:
    """Run all JavaScript frontend validation checks."""
    print_header("JAVASCRIPT FRONTEND VALIDATION")

    # Check if npm is available
    npm_available = shutil.which("npm") is not None

    if not npm_available:
        print_warning(
            "⚠️  npm not found - frontend validation will be skipped locally\n"
            "   This is OK if you didn't modify any .js/.css/.html files\n"
            "   GitHub Actions will run frontend tests with Node.js installed"
        )

    checks = []

    # 1. ESLint - JavaScript linting (SHOULD be in CI but currently missing)
    print_section("Step 1/3: JavaScript Linting (eslint)")
    success, _ = run_command(
        ["npx", "eslint", "src/static/js", "--report-unused-disable-directives"],
        "ESLint check"
    )
    checks.append(("ESLint", success))

    # 2. JavaScript tests (Jest) with coverage - MATCHES CI
    print_section("Step 2/3: JavaScript Tests (jest)")
    success, _ = run_command(
        ["npm", "test", "--", "--coverage",
         "--coverageReporters=text", "--coverageReporters=lcov"],
        "Jest tests with coverage"
    )
    checks.append(("Jest Tests", success))

    # 3. E2E tests (Playwright) - MATCHES CI
    if not quick:
        print_section("Step 3/3: E2E Tests (playwright)")
        success, _ = run_command(
            ["npx", "playwright", "test", "--project=chromium"],
            "Playwright E2E tests (chromium)"
        )
        checks.append(("E2E Tests", success))
    else:
        print_warning("Quick mode: Skipping E2E tests")

    # Print summary
    print_section("JavaScript Frontend Validation Summary")
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
    print_section("Validating JSON Configuration Files")
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
                check=False
            )
            checks.append((f"JSON: {json_file}", success))
        else:
            print_warning(f"File not found: {json_file}")

    # Validate YAML files (if yamllint is available)
    print_section("Validating YAML Configuration Files")
    yaml_files = list(Path(".github/workflows").glob("*.yml"))

    if yaml_files:
        for yaml_file in yaml_files:
            # Try yamllint first, fall back to basic check
            success, _ = run_command(
                ["yamllint", str(yaml_file)],
                f"YAML validation: {yaml_file.name}",
                check=False
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
    python scripts/validate_code.py --quick      # Skip slow tests
        """
    )
    parser.add_argument(
        "--backend",
        action="store_true",
        help="Run only Python backend validation"
    )
    parser.add_argument(
        "--frontend",
        action="store_true",
        help="Run only JavaScript frontend validation"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: Skip slow tests (E2E, visual regression)"
    )
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Skip configuration validation"
    )

    args = parser.parse_args()

    # Determine what to run
    run_backend = args.backend or not args.frontend
    run_frontend = args.frontend or not args.backend
    run_config = not args.no_config

    print_header("MOCKCMMS CODE VALIDATION")
    print(f"{Colors.OKCYAN}This script simulates the CI pipeline locally.{Colors.ENDC}")
    print(f"{Colors.OKCYAN}All checks must pass before committing code.{Colors.ENDC}\n")

    results = []

    # Run validations
    if run_backend:
        backend_passed = validate_python_backend(quick=args.quick)
        results.append(("Backend", backend_passed))

    if run_frontend:
        frontend_passed = validate_javascript_frontend(quick=args.quick)
        results.append(("Frontend", frontend_passed))

    if run_config:
        config_passed = validate_configuration()
        results.append(("Configuration", config_passed))

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
        print_success("All validation checks passed! ✓")
        print(f"{Colors.OKGREEN}You can safely commit your changes.{Colors.ENDC}")
        return 0
    else:
        print_error("Some validation checks failed! ✗")
        print(f"{Colors.FAIL}Please fix the issues before committing.{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Remember:{Colors.ENDC}")
        print(f"{Colors.WARNING}  1. Fix the CODE, not the configuration{Colors.ENDC}")
        print(f"{Colors.WARNING}  2. Do NOT lower coverage thresholds{Colors.ENDC}")
        print(f"{Colors.WARNING}  3. Do NOT disable linting rules{Colors.ENDC}")
        print(f"{Colors.WARNING}  4. Do NOT update visual test screenshots (unless UI was intentionally changed){Colors.ENDC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

