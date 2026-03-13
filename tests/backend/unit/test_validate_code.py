"""Tests for validation script failure-output formatting."""

import importlib.util
import os
from pathlib import Path
from unittest.mock import MagicMock


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
        """Verify shell=True is only used for npm/npx on Windows."""
        captured = []

        def mock_run(cmd, **kwargs):
            captured.append(kwargs.get("shell", False))
            return MagicMock(returncode=0)

        monkeypatch.setattr(validate_code.subprocess, "run", mock_run)

        # Mocking Windows
        monkeypatch.setattr(validate_code.sys, "platform", "win32")
        validate_code.run_command(["npm", "test"], "npm test")
        assert captured[-1] is True

        validate_code.run_command(["python", "run.py"], "python")
        assert captured[-1] is False

        # Mocking Linux
        monkeypatch.setattr(validate_code.sys, "platform", "linux")
        validate_code.run_command(["npm", "test"], "npm test")
        assert captured[-1] is False
