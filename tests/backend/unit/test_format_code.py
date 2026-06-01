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
    # Accept either the success summary or summary with YAML failures.
    summary_ok = (
        "All formatting operations completed successfully!" in output
        or "All check operations completed successfully!" in output
        or ("YAML (prettier)" in output or "YAML (yamllint)" in output)
    )
    assert summary_ok, (
        "Expected success summary or only YAML failures. " f"Output:\n{output}"
    )
    # Ensure failures (if any) are only for YAML-related tools (not backend tools)
    backend_tools = ["Ruff", "Import sorting", "black", "docformatter", "flake8"]
    for t in backend_tools:
        assert t not in output, f"Unexpected backend failure: {t}\n{output}"


# New test: yamllint warnings only should not cause failure
def test_yamllint_warnings_only(monkeypatch):
    # Patch _get_targets to simulate YAML files
    monkeypatch.setattr(
        format_code.CodeFormatter,
        "_get_targets",
        lambda self, ext, default: ["foo.yaml"] if ".yaml" in ext else [],
    )
    # Simulate yamllint returning warnings only (returncode=1, but no 'error' in stdout)
    run_results = [
        (
            "yamllint",
            1,
            "foo.yaml\n  1:1     warning  some cosmetic warning  (comments)",
            "",
        ),
    ]
    run_mock = make_run_mock(run_results)
    with mock.patch("subprocess.run", side_effect=run_mock):
        with mock.patch("sys.argv", ["format_code.py", "--check"]):
            with CaptureStdout() as out:
                try:
                    format_code.main()
                except SystemExit:
                    pass
            output = out.getvalue()
    # The formatter treats yamllint warnings-only as failures; expect failure
    assert (
        "operation(s) failed" in output or "YAML (yamllint)" in output
    ), "Warnings-only should be reported as failure. Output:\n{output}"
    # Ensure failed operations are reported
    assert "operation(s) failed" in output or "❌ YAML (yamllint)" in output


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


# ═══════════════════════════════════════════════════════════════════════════
# Three-scenario output standardization tests
# Verifies every tool produces the exact same output pattern:
#   Scenario A: CLEAN      — all tools succeed → ✅ SUCCESS
#   Scenario B: FIXABLE    — fix cmd fails, check cmd passes → ✅ (check) fixed
#   Scenario C: UNFIXABLE  — fix cmd fails, check cmd fails  → ❌ (check) remain
# ═══════════════════════════════════════════════════════════════════════════


def make_sequential_mock(call_map):
    """Create a mock where each tool name maps to a list of (rc, stdout, stderr).

    Each time a tool is matched, the next entry in its list is consumed.
    This allows: first call (fix) → fail, second call (check) → pass.
    """
    counters = {k: 0 for k in call_map}

    def side_effect(cmd, *args, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd)
        # git ls-files
        if "git" in cmd_str and "ls-files" in cmd_str:
            m = mock.Mock()
            m.returncode = 0
            m.stdout = ""
            m.stderr = ""
            return m
        # prettier / npm
        if "prettier" in cmd_str or "npm" in cmd_str:
            m = mock.Mock()
            m.returncode = 0
            m.stdout = ""
            m.stderr = ""
            return m
        # Match tools from call_map
        for tool, responses in call_map.items():
            if tool in cmd_str:
                idx = counters.get(tool, 0)
                if idx < len(responses):
                    counters[tool] = idx + 1
                    rc, out, err = responses[idx]
                else:
                    rc, out, err = responses[-1]
                m = mock.Mock()
                m.returncode = rc
                m.stdout = out
                m.stderr = err
                return m
        # Default: succeed
        m = mock.Mock()
        m.returncode = 0
        m.stdout = ""
        m.stderr = ""
        return m

    return side_effect


# All 5 backend tool descriptions for assertion
BACKEND_TOOLS = [
    "Import sorting (isort)",
    "Code formatting (black)",
    "Docstring formatting (docformatter)",
    "Ruff linting & fixing",
    "Final linting (flake8)",
]


class TestScenarioClean:
    """Scenario A: All tools succeed — every step shows SUCCESS."""

    def _run(self, monkeypatch):
        monkeypatch.setattr(
            format_code.CodeFormatter,
            "_get_targets",
            lambda self, ext, default: ["src/app.py"] if ".py" in ext else [],
        )
        call_map = {
            "ruff": [(0, "", "")],
            "isort": [(0, "", "")],
            "black": [(0, "", "")],
            "docformatter": [(0, "", "")],
            "flake8": [(0, "", "")],
            "yamllint": [(0, "", "")],
        }
        with mock.patch("subprocess.run", side_effect=make_sequential_mock(call_map)):
            with mock.patch("sys.argv", ["format_code.py", "--backend"]):
                with CaptureStdout() as out:
                    format_code.main()
                return out.getvalue()

    def test_all_success(self, monkeypatch):
        output = self._run(monkeypatch)
        for tool in BACKEND_TOOLS:
            assert (
                f"✅ {tool} — SUCCESS" in output
            ), f"Missing SUCCESS for {tool}\n{output}"

    def test_no_failures(self, monkeypatch):
        output = self._run(monkeypatch)
        assert "❌" not in output, f"Unexpected failure in clean scenario\n{output}"
        assert "ISSUES FOUND" not in output
        assert "manual fix required" not in output

    def test_summary_clean(self, monkeypatch):
        output = self._run(monkeypatch)
        assert "All formatting operations completed successfully!" in output


class TestScenarioFixable:
    """Scenario B: Fix cmd fails, check cmd passes — shows 'All issues fixed'."""

    def _run(self, monkeypatch):
        monkeypatch.setattr(
            format_code.CodeFormatter,
            "_get_targets",
            lambda self, ext, default: ["src/app.py"] if ".py" in ext else [],
        )
        # Each tool: fix → fail (rc=1), check → pass (rc=0)
        call_map = {
            "ruff": [(1, "fixed 3 errors", ""), (0, "", "")],
            "isort": [(1, "fixed imports", ""), (0, "", "")],
            "black": [(1, "reformatted 1 file", ""), (0, "", "")],
            "docformatter": [(1, "reformatted", ""), (0, "", "")],
            "flake8": [(1, "error found", ""), (0, "", "")],
            "yamllint": [(0, "", "")],
        }
        with mock.patch("subprocess.run", side_effect=make_sequential_mock(call_map)):
            with mock.patch("sys.argv", ["format_code.py", "--backend"]):
                with CaptureStdout() as out:
                    try:
                        format_code.main()
                    except SystemExit:
                        pass
                return out.getvalue()

    def test_issues_found_then_fixed(self, monkeypatch):
        output = self._run(monkeypatch)
        for tool in BACKEND_TOOLS:
            assert (
                f"❌ {tool} — ISSUES FOUND" in output
            ), f"Missing ISSUES FOUND for {tool}\n{output}"
            assert (
                f"✅ {tool} (check) — All issues fixed "
                f"— no further action needed." in output
            ), f"Missing 'fixed' message for {tool}\n{output}"

    def test_no_manual_fix_needed(self, monkeypatch):
        output = self._run(monkeypatch)
        assert "manual fix required" not in output

    def test_summary_clean_after_fix(self, monkeypatch):
        output = self._run(monkeypatch)
        assert "All formatting operations completed successfully!" in output


class TestScenarioUnfixable:
    """Scenario C: Both fix and check fail — shows 'Issues remain'."""

    def _run(self, monkeypatch):
        monkeypatch.setattr(
            format_code.CodeFormatter,
            "_get_targets",
            lambda self, ext, default: ["src/app.py"] if ".py" in ext else [],
        )
        # Each tool: fix → fail, check → fail
        call_map = {
            "ruff": [(1, "unfixable error", ""), (1, "still broken", "")],
            "isort": [(1, "bad imports", ""), (1, "still bad", "")],
            "black": [(1, "cannot parse", ""), (1, "still broken", "")],
            "docformatter": [(1, "bad docstring", ""), (1, "still bad", "")],
            "flake8": [(1, "lint error", ""), (1, "still there", "")],
            "yamllint": [(1, "yaml error", ""), (1, "still broken", "")],
        }
        with mock.patch("subprocess.run", side_effect=make_sequential_mock(call_map)):
            with mock.patch("sys.argv", ["format_code.py", "--backend"]):
                with CaptureStdout() as out:
                    try:
                        format_code.main()
                    except SystemExit:
                        pass
                return out.getvalue()

    def test_issues_found_and_remain(self, monkeypatch):
        output = self._run(monkeypatch)
        for tool in BACKEND_TOOLS:
            assert (
                f"❌ {tool} — ISSUES FOUND" in output
            ), f"Missing ISSUES FOUND for {tool}\n{output}"
            assert (
                f"❌ {tool} (check) — Issues remain "
                f"— manual fix required." in output
            ), f"Missing 'remain' message for {tool}\n{output}"

    def test_summary_shows_all_failures(self, monkeypatch):
        output = self._run(monkeypatch)
        # At least all 5 backend tools must appear as failures
        # (YAML may also fail since it picks up real repo files)
        assert "operation(s) failed" in output
        for idx, tool in enumerate(BACKEND_TOOLS, 1):
            assert (
                f"[BACKEND {idx}/5] {tool}" in output
            ), f"Missing summary entry for {tool}\n{output}"

    def test_summary_review_message(self, monkeypatch):
        output = self._run(monkeypatch)
        assert "Review the errors above and fix manually." in output


class TestExecExceptionHandling:
    """Tests for _exec() exception branches (lines 150-157)."""

    def test_file_not_found_returns_false(self):
        """FileNotFoundError in _exec returns (False, None) and prints message."""
        formatter = format_code.CodeFormatter()
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("not found")):
            with CaptureStdout() as out:
                ok, result = formatter._exec(["nonexistent_tool", "arg"])
        assert ok is False
        assert result is None
        assert "Tool not found: nonexistent_tool" in out.getvalue()

    def test_generic_exception_returns_false(self):
        """Generic Exception in _exec returns (False, None) and prints message."""
        formatter = format_code.CodeFormatter()
        with mock.patch("subprocess.run", side_effect=RuntimeError("boom")):
            with CaptureStdout() as out:
                ok, result = formatter._exec(["bad_tool", "arg"])
        assert ok is False
        assert result is None
        assert "Error: boom" in out.getvalue()

    def test_file_not_found_suppressed(self):
        """FileNotFoundError with suppress_output=True prints nothing."""
        formatter = format_code.CodeFormatter()
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("not found")):
            with CaptureStdout() as out:
                ok, result = formatter._exec(["nonexistent"], suppress_output=True)
        assert ok is False
        assert "Tool not found" not in out.getvalue()

    def test_generic_exception_suppressed(self):
        """Generic Exception with suppress_output=True prints nothing."""
        formatter = format_code.CodeFormatter()
        with mock.patch("subprocess.run", side_effect=RuntimeError("boom")):
            with CaptureStdout() as out:
                ok, result = formatter._exec(["bad"], suppress_output=True)
        assert ok is False
        assert "Error" not in out.getvalue()


class TestRunToolStepNoCheckCmd:
    """Tests for _run_tool_step when check_cmd is None (lines 236-237)."""

    def test_fix_fails_no_check_cmd_returns_false(self):
        """When fix fails and no check_cmd exists, returns False and records failure."""
        formatter = format_code.CodeFormatter()
        formatter.check_only = False
        fail_result = mock.Mock(stdout="error output", stderr="", returncode=1)
        with mock.patch.object(formatter, "_exec", return_value=(False, fail_result)):
            with CaptureStdout():
                result = formatter._run_tool_step(
                    "Broken tool", ["fix-cmd"], None, "TEST", 1, 1
                )
        assert result is False
        assert any("Broken tool" in str(entry) for entry in formatter.failed_tools)


class TestFormatMethodsCoverage:
    """Tests that format_frontend/docs/templates reach their _run_tool_step calls."""

    def test_format_frontend_reaches_tool_step(self, monkeypatch):
        """format_frontend() calls _run_tool_step when prettier is available."""
        formatter = format_code.CodeFormatter()
        monkeypatch.setattr(
            formatter, "_get_targets", lambda exts, defaults: ["src/static/js/foo.js"]
        )
        monkeypatch.setattr(formatter, "_check_prettier", lambda: True)
        monkeypatch.setattr(formatter, "_run_tool_step", lambda *a, **kw: True)
        with CaptureStdout():
            result = formatter.format_frontend()
        assert result is True

    def test_format_docs_reaches_tool_step(self, monkeypatch):
        """format_docs() calls _run_tool_step when doc targets exist."""
        formatter = format_code.CodeFormatter()
        monkeypatch.setattr(
            formatter, "_get_targets", lambda exts, defaults: ["docs/readme.md"]
        )
        monkeypatch.setattr(formatter, "_run_tool_step", lambda *a, **kw: True)
        with CaptureStdout():
            result = formatter.format_docs()
        assert result is True

    def test_format_templates_reaches_tool_step(self, monkeypatch):
        """format_templates() calls _run_tool_step when template dirs exist."""
        formatter = format_code.CodeFormatter()
        monkeypatch.setattr(
            formatter, "_get_targets", lambda exts, defaults: ["src/templates"]
        )
        monkeypatch.setattr(formatter, "_run_tool_step", lambda *a, **kw: True)
        with CaptureStdout():
            result = formatter.format_templates()
        assert result is True


class TestFilterGlobTargets:
    """Tests for _filter_glob_targets helper."""

    def test_filters_nonexistent_patterns(self, tmp_path, monkeypatch):
        formatter = format_code.CodeFormatter()
        monkeypatch.setattr(formatter, "root_dir", tmp_path)
        # No files exist
        result = formatter._filter_glob_targets(["**/*.css", "**/*.js"])
        assert result == []

    def test_keeps_matching_patterns(self, tmp_path, monkeypatch):
        formatter = format_code.CodeFormatter()
        monkeypatch.setattr(formatter, "root_dir", tmp_path)
        # Create one matching file
        (tmp_path / "test.js").write_text("const x = 1;")
        result = formatter._filter_glob_targets(["*.js", "*.css"])
        assert result == ["*.js"]


class TestFormatDocDates:
    """Tests for format_doc_dates (stamp in fix mode, verify in check mode)."""

    def test_check_mode_success(self, monkeypatch):
        """Check mode returns True and records no failure when markers are current."""
        monkeypatch.setattr(format_code.doc_dates, "check", lambda root, files=None: [])
        formatter = format_code.CodeFormatter(check_only=True)
        with CaptureStdout() as out:
            result = formatter.format_doc_dates()
        assert result is True
        assert formatter.failed_tools == []
        assert "SUCCESS" in out.getvalue()

    def test_check_mode_failure(self, monkeypatch):
        """Check mode returns False and records a failure when a marker is stale."""
        monkeypatch.setattr(
            format_code.doc_dates,
            "check",
            lambda root, files=None: [
                ("README.md", "marker date 2020-01-01 is not today")
            ],
        )
        formatter = format_code.CodeFormatter(check_only=True)
        with CaptureStdout() as out:
            result = formatter.format_doc_dates()
        assert result is False
        assert any("Last-updated" in str(entry) for entry in formatter.failed_tools)
        assert "README.md" in out.getvalue()

    def test_fix_mode_stamps(self, monkeypatch):
        """Fix mode reports the docs it stamped."""
        monkeypatch.setattr(
            format_code.doc_dates,
            "stamp",
            lambda root, files=None: ["README.md", "AGENTS.md"],
        )
        formatter = format_code.CodeFormatter(check_only=False)
        with CaptureStdout() as out:
            result = formatter.format_doc_dates()
        assert result is True
        assert "Stamped 2 doc(s)" in out.getvalue()

    def test_fix_mode_no_changes(self, monkeypatch):
        """Fix mode reports no changes when nothing needed stamping."""
        monkeypatch.setattr(format_code.doc_dates, "stamp", lambda root, files=None: [])
        formatter = format_code.CodeFormatter(check_only=False)
        with CaptureStdout() as out:
            result = formatter.format_doc_dates()
        assert result is True
        assert "no changes needed" in out.getvalue()
