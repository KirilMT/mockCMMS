"""Tests for validation script failure-output formatting."""

import importlib.util
from pathlib import Path


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
