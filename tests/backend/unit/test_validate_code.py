"""Tests for validation script failure-output formatting."""

import importlib.util
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _load_validate_code_module():
    """Load scripts/validate_code.py as a testable module."""
    module_path = Path(__file__).resolve().parents[3] / "scripts" / "validate_code.py"
    spec = importlib.util.spec_from_file_location(
        "validate_code_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


validate_code = _load_validate_code_module()


def test_format_failure_output_prioritizes_pytest_failure_sections():
    """Pytest failures should show summaries and traceback, not just passing noise."""
    noisy_stdout = "\n".join(
        [f"test_{index:03d} PASSED" for index in range(120)]
        + [
            "============================= FAILURES =============================",
            "__________________________ test_example ___________________________",
            "    def test_example():",
            ">       assert 1 == 2",
            "E       AssertionError: assert 1 == 2",
            (
                "======================= short test summary info "
                "======================="
            ),
            (
                "FAILED tests/backend/unit/test_example.py::test_example - "
                "AssertionError: assert 1 == 2"
            ),
        ]
    )

    formatted = validate_code.format_failure_output(noisy_stdout, "")

    assert "Pytest short summary:" in formatted
    assert "FAILED tests/backend/unit/test_example.py::test_example" in formatted
    assert "Failure details:" in formatted
    assert "AssertionError: assert 1 == 2" in formatted
    assert "test_000 PASSED" not in formatted


def test_format_failure_output_includes_coverage_details():
    """Coverage threshold failures should remain visible in the formatted output."""
    stdout = "\n".join(
        [
            (
                "============================= test session starts "
                "============================="
            ),
            "tests/backend/unit/test_something.py::test_ok PASSED [100%]",
            (
                "________________________ coverage: platform win32 "
                "_________________________"
            ),
            "TOTAL                                              6096   4145  32.00%",
            (
                "FAIL Required test coverage of 85% not reached. "
                "Total coverage: 32.00%"
            ),
        ]
    )

    formatted = validate_code.format_failure_output(stdout, "")

    assert "Coverage details:" in formatted
    assert "FAIL Required test coverage of 85% not reached." in formatted
    assert (
        "TOTAL                                              6096   4145  32.00%"
        in formatted
    )


def test_format_failure_output_falls_back_to_compact_generic_view():
    """Non-pytest failures should still show a readable head/tail summary."""
    stdout = "\n".join([f"line {index}" for index in range(220)])

    formatted = validate_code.format_failure_output(stdout, "")

    assert "First lines:" in formatted
    assert "Last lines:" in formatted
    assert "... [160 lines omitted for brevity] ..." in formatted
    assert "line 0" in formatted
    assert "line 219" in formatted


def test_run_command_merges_explicit_env_overrides(monkeypatch):
    """run_command should apply explicit env overrides on top of ironclad defaults."""

    captured = {}

    class _Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(*_args, **kwargs):
        captured["env"] = kwargs["env"]
        return _Result()

    monkeypatch.setattr(validate_code.subprocess, "run", _fake_run)

    success, _ = validate_code.run_command(
        ["python", "-V"],
        "python version",
        check=False,
        env={"E2E_TEST": "true", "CUSTOM_FLAG": "enabled"},
    )

    assert success is True
    assert captured["env"]["E2E_TEST"] == "true"
    assert captured["env"]["CUSTOM_FLAG"] == "enabled"


def test_run_command_preserves_windows_root_env_vars(monkeypatch):
    """run_command should propagate SYSTEMDRIVE/PROGRAMDATA into subprocess env."""

    captured = {}

    class _Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(*_args, **kwargs):
        captured["env"] = kwargs["env"]
        return _Result()

    monkeypatch.setattr(validate_code.subprocess, "run", _fake_run)
    monkeypatch.setenv("SYSTEMDRIVE", "C:")
    monkeypatch.setenv("PROGRAMDATA", r"C:\ProgramData")
    monkeypatch.setenv("HOMEDRIVE", "C:")
    monkeypatch.setenv("HOMEPATH", r"\Users\tester")

    success, _ = validate_code.run_command(
        ["python", "-V"],
        "python version",
        check=False,
    )

    assert success is True
    assert captured["env"]["SYSTEMDRIVE"] == os.environ["SYSTEMDRIVE"]
    assert captured["env"]["PROGRAMDATA"] == os.environ["PROGRAMDATA"]
    assert captured["env"]["HOMEDRIVE"] == os.environ["HOMEDRIVE"]
    assert captured["env"]["HOMEPATH"] == os.environ["HOMEPATH"]


class TestValidateCodeRobust:
    """Robust tests for validate_code.py logic and environment management."""

    def test_dedupe_output_blocks_handles_none_and_whitespace(self):
        """Verify _dedupe_output_blocks is resilient to various inputs."""
        inputs = ["block1", None, "  ", "block1", "block2\n", "block2"]
        # normalized "block2\n" is "block2", so it's a duplicate
        expected = ["block1", "block2"]
        assert validate_code._dedupe_output_blocks(*inputs) == expected

    def test_extract_coverage_block_variations(self):
        """Test coverage extraction with different output patterns."""
        lines = [
            "some output",
            "TOTAL                                              100     10  90%",
            "coverage: platform win32",
            "more lines",
            "Required test coverage of 85% reached.",
        ]
        extracted = validate_code._extract_coverage_block(lines)
        assert "TOTAL" in extracted
        assert "90%" in extracted

        # Empty case
        assert validate_code._extract_coverage_block(["no coverage info"]) == ""

    def test_run_command_environment_sanitization(self, monkeypatch):
        """Verify that ironclad environment sanitizes sensitive variables."""
        captured_env = {}

        def mock_run(cmd, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            return MagicMock(returncode=0, stdout="success", stderr="")

        monkeypatch.setattr(validate_code.subprocess, "run", mock_run)

        # Set a "poison" variable in current environment
        monkeypatch.setenv("PORTABLE_DISTRIBUTION", "true")

        validate_code.run_command(["ls"], "test")

        # Ironclad should have forced it to false
        assert captured_env["PORTABLE_DISTRIBUTION"] == "false"
        assert captured_env["CI"] == "true"
        assert captured_env["TESTING"] == "1"

    def test_format_failure_output_max_lines_limit(self):
        """Test truncation logic for very long generic failure output."""
        long_output = "\n".join([f"line {i}" for i in range(500)])
        formatted = validate_code.format_failure_output(long_output, "")

        assert "First lines:" in formatted
        assert "Last lines:" in formatted
        assert "line 0" in formatted
        assert "line 499" in formatted
        assert "lines omitted for brevity" in formatted

    def test_pytest_section_parsing_complex(self):
        """Test parsing of multiple pytest sections."""
        output = [
            "============================= FAILURES =============================",
            "fail1",
            "============================= ERRORS ===============================",
            "error1",
            "====================== short test summary info ======================",
            "summary1",
        ]
        ranges = validate_code._find_pytest_section_ranges(output)
        assert "failures" in ranges
        assert "errors" in ranges
        assert "short test summary info" in ranges

        assert ranges["failures"] == (0, 2)
        assert ranges["errors"] == (2, 4)
        assert ranges["short test summary info"] == (4, 6)

    def test_run_command_shell_selection(self, monkeypatch):
        """Verify npm/npx commands are prefixed with 'cmd /c' on Windows."""
        captured = []

        def mock_run(cmd, **kwargs):
            captured.append(cmd)
            return MagicMock(returncode=0, stdout="ok", stderr="")

        monkeypatch.setattr(validate_code.subprocess, "run", mock_run)

        # Mocking Windows — npm should be prefixed with cmd /c
        monkeypatch.setattr(validate_code.sys, "platform", "win32")
        validate_code.run_command(["npm", "test"], "npm test")
        assert captured[-1][:2] == ["cmd", "/c"]

        validate_code.run_command(["python", "run.py"], "python")
        assert captured[-1][0] == "python"
        assert "cmd" not in captured[-1]

        # Mocking Linux — npm should NOT be prefixed
        monkeypatch.setattr(validate_code.sys, "platform", "linux")
        validate_code.run_command(["npm", "test"], "npm test")
        assert captured[-1][0] == "npm"
        assert "cmd" not in captured[-1]


class TestValidatePythonBackendPaths:
    """Tests covering all branch paths in validate_python_backend.

    Exercises every combination of quick/full mode, files/no-files, and scope detection
    so that diff-cover sees 92%+ coverage for new lines.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch):
        """Mock run_command to always succeed and fake coverage.xml."""
        monkeypatch.setattr(
            validate_code,
            "run_command",
            lambda cmd, desc, **kwargs: (True, ""),
        )
        _orig_exists = os.path.exists
        monkeypatch.setattr(
            os.path,
            "exists",
            lambda p: True if p == "coverage.xml" else _orig_exists(p),
        )

    def test_full_mode_no_files(self):
        """Full mode: default targets, full suite, coverage threshold, diff-cover."""
        result = validate_code.validate_python_backend(quick=False, files=None)
        assert result is True

    def test_quick_with_test_files(self):
        """Quick mode with test files runs targeted tests and scoped diff-cover."""
        result = validate_code.validate_python_backend(
            quick=True,
            files=["tests/backend/unit/test_foo.py", "src/app.py"],
        )
        assert result is True

    def test_quick_source_only_full_suite(self, monkeypatch):
        """Quick + source files + full_suite scope triggers global test run."""
        monkeypatch.setattr(
            validate_code,
            "detect_changed_scopes",
            lambda: {"full_suite": True, "backend": [], "frontend": []},
        )
        result = validate_code.validate_python_backend(
            quick=True,
            files=["src/app.py"],
        )
        assert result is True

    def test_quick_source_only_backend_scope(self, monkeypatch):
        """Quick + source files + backend scope targets specific test dirs."""
        monkeypatch.setattr(
            validate_code,
            "detect_changed_scopes",
            lambda: {
                "full_suite": False,
                "backend": ["tests/backend"],
                "frontend": [],
            },
        )
        result = validate_code.validate_python_backend(
            quick=True,
            files=["src/app.py"],
        )
        assert result is True

    def test_quick_no_files_full_suite(self, monkeypatch):
        """Quick without files + full_suite runs all tests."""
        monkeypatch.setattr(
            validate_code,
            "detect_changed_scopes",
            lambda: {"full_suite": True, "backend": [], "frontend": []},
        )
        result = validate_code.validate_python_backend(quick=True, files=None)
        assert result is True

    def test_quick_no_files_backend_scope(self, monkeypatch):
        """Quick without files + backend scope targets specific dirs."""
        monkeypatch.setattr(
            validate_code,
            "detect_changed_scopes",
            lambda: {
                "full_suite": False,
                "backend": ["tests/backend"],
                "frontend": [],
            },
        )
        result = validate_code.validate_python_backend(quick=True, files=None)
        assert result is True

    def test_quick_only_test_files_skips_diff_cover(self):
        """Quick with only test files has no source → skips diff-cover."""
        result = validate_code.validate_python_backend(
            quick=True,
            files=["tests/backend/unit/test_foo.py"],
        )
        assert result is True

    def test_quick_no_relevant_scopes_skips_tests(self, monkeypatch):
        """Quick + source files + empty scopes skips test execution."""
        monkeypatch.setattr(
            validate_code,
            "detect_changed_scopes",
            lambda: {"full_suite": False, "backend": [], "frontend": []},
        )
        result = validate_code.validate_python_backend(
            quick=True,
            files=["src/app.py"],
        )
        assert result is True

    def test_quick_no_files_no_scopes(self, monkeypatch):
        """Quick without files + no scopes → skip tests entirely."""
        monkeypatch.setattr(
            validate_code,
            "detect_changed_scopes",
            lambda: {"full_suite": False, "backend": [], "frontend": []},
        )
        result = validate_code.validate_python_backend(quick=True, files=None)
        assert result is True


class TestValidatePythonBackendEdgeCases:
    """Edge-case tests that need different fixture setup."""

    def test_full_mode_no_coverage_xml(self, monkeypatch):
        """Full mode without coverage.xml skips diff-cover gracefully."""
        monkeypatch.setattr(
            validate_code,
            "run_command",
            lambda cmd, desc, **kwargs: (True, ""),
        )
        # coverage.xml does NOT exist → diff-cover is skipped
        _orig_exists = os.path.exists
        monkeypatch.setattr(
            os.path,
            "exists",
            lambda p: False if p == "coverage.xml" else _orig_exists(p),
        )
        result = validate_code.validate_python_backend(quick=False, files=None)
        assert result is True


class TestValidateOthersPrettierNotInstalled:
    """Test validate_others when Prettier is not installed."""

    def test_prettier_not_installed_skips_gracefully(self, monkeypatch):
        """validate_others skips linting when npm list prettier returns non-zero."""
        monkeypatch.setattr(
            validate_code.subprocess,
            "run",
            lambda *a, **kw: MagicMock(returncode=1),
        )
        result = validate_code.validate_others(files=["docs/readme.md"])
        assert result is True


class TestValidateOthersPrettierInstalled:
    """Test validate_others when Prettier IS installed (line 1023+)."""

    def test_prettier_installed_runs_check(self, monkeypatch):
        """validate_others runs prettier check when npm list returns 0."""
        call_log = []

        def mock_subprocess_run(*args, **kwargs):
            call_log.append(args)
            return MagicMock(returncode=0, stdout="ok", stderr="")

        monkeypatch.setattr(validate_code.subprocess, "run", mock_subprocess_run)
        monkeypatch.setattr(
            validate_code,
            "run_command",
            lambda cmd, desc, **kw: (True, ""),
        )
        result = validate_code.validate_others(files=["docs/readme.md"])
        assert result is True

    def test_prettier_check_exception_skips(self, monkeypatch):
        """validate_others skips when subprocess raises an exception."""

        def boom(*a, **kw):
            raise OSError("npm not found")

        monkeypatch.setattr(validate_code.subprocess, "run", boom)
        result = validate_code.validate_others(files=["docs/readme.md"])
        assert result is True


class TestDiffCoverNotInstalled:
    """Test diff-cover not installed path (lines 964-971)."""

    def test_diff_cover_not_installed_soft_passes(self, monkeypatch):
        """When diff-cover --version fails, should soft-pass."""
        _orig_exists = os.path.exists
        monkeypatch.setattr(
            os.path,
            "exists",
            lambda p: True if p == "coverage.xml" else _orig_exists(p),
        )

        call_count = [0]

        def mock_run(cmd, desc, **kwargs):
            call_count[0] += 1
            # Make diff-cover --version fail
            if "diff-cover" in cmd and "--version" in cmd:
                return (False, "not found")
            return (True, "")

        monkeypatch.setattr(validate_code, "run_command", mock_run)
        result = validate_code.validate_python_backend(quick=False, files=None)
        assert result is True


class TestDiffCoverFailure:
    """Test diff-cover execution failure path (line 961)."""

    def test_diff_cover_fails_reports_failure(self, monkeypatch):
        """When diff-cover check fails, the overall result should be False."""
        _orig_exists = os.path.exists
        monkeypatch.setattr(
            os.path,
            "exists",
            lambda p: True if p == "coverage.xml" else _orig_exists(p),
        )

        def mock_run(cmd, desc, **kwargs):
            # diff-cover --version succeeds
            if "diff-cover" in cmd and "--version" in cmd:
                return (True, "diff-cover 1.0")
            # diff-cover check FAILS
            if "diff-cover" in cmd and "coverage.xml" in cmd:
                return (False, "Coverage below 92%")
            return (True, "")

        monkeypatch.setattr(validate_code, "run_command", mock_run)
        result = validate_code.validate_python_backend(quick=False, files=None)
        # Should be False because diff-cover failed
        assert result is False


class TestSummaryPrintsErrors:
    """Test the summary loop prints errors for failed checks (line 976+)."""

    def test_failed_check_prints_error(self, monkeypatch, capsys):
        """When a linting step fails, the summary should print FAIL."""
        _orig_exists = os.path.exists
        monkeypatch.setattr(
            os.path,
            "exists",
            lambda p: True if p == "coverage.xml" else _orig_exists(p),
        )

        call_count = [0]

        def mock_run(cmd, desc, **kwargs):
            call_count[0] += 1
            # Make the first check (isort) fail
            if "isort" in cmd:
                return (False, "unsorted imports")
            return (True, "")

        monkeypatch.setattr(validate_code, "run_command", mock_run)
        result = validate_code.validate_python_backend(quick=False, files=None)
        assert result is False
        out = capsys.readouterr().out
        assert "FAIL" in out


class TestValidateJsFrontend:
    """Test validate_javascript_frontend branches."""

    def test_npm_not_available_skips(self, monkeypatch):
        """When npm is not found, frontend validation should pass (skip)."""
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = validate_code.validate_javascript_frontend(quick=False, files=None)
        assert result is True

    def test_no_frontend_files_returns_true(self, monkeypatch):
        """When given files with no frontend targets, should return True early."""
        monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/npm")
        result = validate_code.validate_javascript_frontend(
            quick=False, files=["src/app.py"]
        )
        assert result is True


class TestValidateConfiguration:
    """Tests for validate_configuration."""

    def test_validates_json_files(self, monkeypatch):
        """Should validate JSON files that exist."""
        monkeypatch.setattr(
            validate_code,
            "run_command",
            lambda cmd, desc, **kw: (True, ""),
        )
        result = validate_code.validate_configuration()
        assert isinstance(result, bool)


class TestDetectChangedScopes:
    """Tests for detect_changed_scopes edge cases."""

    def test_global_config_file_triggers_full_suite(self, monkeypatch):
        """Changes to conftest.py trigger full suite."""
        monkeypatch.setattr(
            validate_code, "_get_changed_files", lambda: ["conftest.py"]
        )
        scopes = validate_code.detect_changed_scopes()
        assert scopes["full_suite"] is True

    def test_infrastructure_prefix_triggers_full_suite(self, monkeypatch):
        """Changes to scripts/ trigger full suite."""
        monkeypatch.setattr(
            validate_code, "_get_changed_files", lambda: ["scripts/validate.py"]
        )
        scopes = validate_code.detect_changed_scopes()
        assert scopes["full_suite"] is True

    def test_frontend_only_change(self, monkeypatch):
        """CSS changes should map to frontend only, not backend."""
        monkeypatch.setattr(
            validate_code, "_get_changed_files", lambda: ["src/static/css/style.css"]
        )
        scopes = validate_code.detect_changed_scopes()
        assert scopes["full_suite"] is False
        assert scopes["backend"] == []
        assert len(scopes["frontend"]) > 0
