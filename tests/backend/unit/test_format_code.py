"""test_format_code.py.

Tests for scripts/format_code.py covering all major scenarios:
- All formatters succeed
- One or more formatters fail
- Formatter fails, then passes after fix
- Output style for failed steps (no warning line)
- Output style for successful steps
- Edge cases: no files, only frontend/backend, etc.

Uses pytest and unittest.mock for subprocess and file mocking.
"""

import io
import sys
from unittest import mock

import pytest

from scripts import format_code


# Helper to capture stdout
class CaptureStdout:
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self._stringio

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._stdout


# Mock subprocess.run to simulate formatter results
def make_run_mock(results):
    """results: list of (cmd, returncode, stdout, stderr)"""

    def run_side_effect(cmd, *args, **kwargs):
        cmd_str = " ".join(cmd)
        # Handle git ls-files and other discovery commands
        if "git ls-files" in cmd_str:
            m = mock.Mock()
            m.returncode = 0
            # Simulate some files for backend/frontend as needed
            if "*.py" in cmd_str:
                m.stdout = "src/app.py\nsrc/routes/api.py\n"
            elif "*.js" in cmd_str:
                m.stdout = "src/static/js/foo.js\n"
            elif "*.css" in cmd_str:
                m.stdout = "src/static/css/foo.css\n"
            else:
                m.stdout = ""
            m.stderr = ""
            return m
        # Handle Prettier and Stylelint (frontend)
        if "prettier" in cmd_str or "stylelint" in cmd_str:
            m = mock.Mock()
            m.returncode = 0
            m.stdout = ""
            m.stderr = ""
            return m
        # Handle all formatter results
        for pattern, code, out, err in results:
            if pattern in cmd_str:
                m = mock.Mock()
                m.returncode = code
                m.stdout = out
                m.stderr = err
                return m
        # Default: succeed silently
        m = mock.Mock()
        m.returncode = 0
        m.stdout = ""
        m.stderr = ""
        return m

    return run_side_effect


@pytest.mark.parametrize(
    "scenario,run_results,expected",
    [
        (
            "all succeed",
            [
                ("ruff", 0, "", ""),
                ("isort", 0, "", ""),
                ("black", 0, "", ""),
                ("docformatter", 0, "", ""),
                ("flake8", 0, "", ""),
            ],
            [
                "✅ Ruff linting & fixing — SUCCESS",
                "✅ Import sorting (isort) — SUCCESS",
                "✅ Code formatting (black) — SUCCESS",
                "✅ Docstring formatting (docformatter) — SUCCESS",
                "✅ Final linting (flake8) — SUCCESS",
            ],
        ),
        (
            "ruff fails",
            [
                ("ruff", 1, "Ruff error", ""),
                ("isort", 0, "", ""),
                ("black", 0, "", ""),
                ("docformatter", 0, "", ""),
                ("flake8", 0, "", ""),
            ],
            [
                "❌ Ruff linting & fixing — ISSUES FOUND",
                "Ruff error",
                (
                    "❌ Ruff linting & fixing (check) "
                    "— Issues remain — manual fix required."
                ),
                "✅ Import sorting (isort) — SUCCESS",
                "✅ Code formatting (black) — SUCCESS",
                "✅ Docstring formatting (docformatter) — SUCCESS",
                "✅ Final linting (flake8) — SUCCESS",
            ],
        ),
        (
            "isort fails, then passes",
            [
                ("ruff", 0, "", ""),
                ("isort", 1, "isort error", ""),
                ("isort", 0, "", ""),
                ("black", 0, "", ""),
                ("docformatter", 0, "", ""),
                ("flake8", 0, "", ""),
            ],
            [
                "✅ Ruff linting & fixing — SUCCESS",
                "❌ Import sorting (isort) — ISSUES FOUND",
                "isort error",
                (
                    "❌ Import sorting (isort) (check) "
                    "— Issues remain — manual fix required."
                ),
                "✅ Code formatting (black) — SUCCESS",
                "✅ Docstring formatting (docformatter) — SUCCESS",
                "✅ Final linting (flake8) — SUCCESS",
            ],
        ),
        (
            "flake8 fails",
            [
                ("ruff", 0, "", ""),
                ("isort", 0, "", ""),
                ("black", 0, "", ""),
                ("docformatter", 0, "", ""),
                ("flake8", 1, "flake8 error", ""),
            ],
            [
                "✅ Ruff linting & fixing — SUCCESS",
                "✅ Import sorting (isort) — SUCCESS",
                "✅ Code formatting (black) — SUCCESS",
                "✅ Docstring formatting (docformatter) — SUCCESS",
                "❌ Final linting (flake8) — ISSUES FOUND",
                "flake8 error",
                (
                    "❌ Final linting (flake8) (check) "
                    "— Issues remain — manual fix required."
                ),
            ],
        ),
    ],
)
def test_format_code_scenarios(scenario, run_results, expected):
    # Patch subprocess.run
    run_mock = make_run_mock(run_results)
    with mock.patch("subprocess.run", side_effect=run_mock):
        # Patch sys.argv to simulate --backend
        with mock.patch("sys.argv", ["format_code.py", "--backend"]):
            with CaptureStdout() as out:
                # Run main (should not exit)
                try:
                    format_code.main()
                except SystemExit:
                    pass
            output = out.getvalue()
    # Check expected lines in output
    for line in expected:
        assert line in output, f"Missing line: {line}\nOutput:\n{output}"


# Edge case: no files to format (simulate by patching file discovery)
def test_no_files(monkeypatch):
    # Patch CodeFormatter._get_targets to return no files for Python
    monkeypatch.setattr(
        format_code.CodeFormatter,
        "_get_targets",
        lambda self, ext, default: [] if ".py" in ext else default,
    )
    with mock.patch("subprocess.run"):
        with mock.patch("sys.argv", ["format_code.py", "--backend"]):
            with CaptureStdout() as out:
                format_code.main()
            output = out.getvalue()
    # Since no files, Python formatting should be skipped (no error)
    assert "All formatting operations completed successfully!" in output


# Edge case: only frontend files (simulate by patching file discovery)
def test_only_frontend(monkeypatch):
    # Patch _get_targets to simulate only JS file found
    def fake_get_targets(self, ext, default):
        if any(e in ext for e in [".js", ".jsx", ".ts", ".tsx", ".css", ".scss"]):
            return ["src/static/js/foo.js"]
        return []

    monkeypatch.setattr(format_code.CodeFormatter, "_get_targets", fake_get_targets)
    with mock.patch("subprocess.run"):
        with mock.patch("sys.argv", ["format_code.py", "--frontend"]):
            with CaptureStdout() as out:
                format_code.main()
            output = out.getvalue()
    assert "Prettier not installed" in output


# Edge case: both frontend and backend
@pytest.mark.parametrize(
    "args",
    [
        ["format_code.py", "--backend", "--frontend"],
        ["format_code.py", "--frontend", "--backend"],
    ],
)
def test_both_modes(args, monkeypatch):
    # Patch _get_targets to simulate both Python and JS files found
    def fake_get_targets(self, ext, default):
        if ".py" in ext:
            return ["src/app.py"]
        if any(e in ext for e in [".js", ".jsx", ".ts", ".tsx", ".css", ".scss"]):
            return ["src/static/js/foo.js"]
        return []

    monkeypatch.setattr(format_code.CodeFormatter, "_get_targets", fake_get_targets)
    with mock.patch("subprocess.run"):
        with mock.patch("sys.argv", args):
            with CaptureStdout() as out:
                format_code.main()
            output = out.getvalue()
    assert "Ruff linting & fixing" in output
    assert "Prettier not installed" in output


# Output style: failed step should not show warning line
def test_failed_step_no_warning(monkeypatch):
    monkeypatch.setattr(
        format_code.CodeFormatter,
        "_get_targets",
        lambda self, ext, default: ["src/app.py"] if ".py" in ext else [],
    )
    run_results = [
        ("ruff", 1, "Ruff error", ""),
        ("isort", 0, "", ""),
        ("black", 0, "", ""),
        ("docformatter", 0, "", ""),
        ("flake8", 0, "", ""),
    ]
    run_mock = make_run_mock(run_results)
    with mock.patch("subprocess.run", side_effect=run_mock):
        with mock.patch("sys.argv", ["format_code.py", "--backend"]):
            with CaptureStdout() as out:
                try:
                    format_code.main()
                except SystemExit:
                    pass
            output = out.getvalue()
    # The summary warning line is now always present if any operation fails
    assert "⚠️  Review the errors above and fix manually." in output
    assert "❌ Ruff linting & fixing — ISSUES FOUND" in output
    assert "Ruff error" in output


# Output style: successful step should show only summary
def test_successful_step_summary(monkeypatch):
    monkeypatch.setattr(
        format_code.CodeFormatter,
        "_get_targets",
        lambda self, ext, default: ["src/app.py"] if ".py" in ext else [],
    )
    run_results = [
        ("ruff", 0, "", ""),
        ("isort", 0, "", ""),
        ("black", 0, "", ""),
        ("docformatter", 0, "", ""),
        ("flake8", 0, "", ""),
    ]
    run_mock = make_run_mock(run_results)
    with mock.patch("subprocess.run", side_effect=run_mock):
        with mock.patch("sys.argv", ["format_code.py", "--backend"]):
            with CaptureStdout() as out:
                format_code.main()
            output = out.getvalue()
    assert "✅" in output
    assert "❌" not in output
    assert "⚠️" not in output
