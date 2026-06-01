"""Unit tests for ``scripts/doc_dates.py`` (documentation last-updated stamps)."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"


def _load_module():
    """Load scripts/doc_dates.py as a testable module."""
    module_path = _SCRIPTS_DIR / "doc_dates.py"
    spec = importlib.util.spec_from_file_location("doc_dates_ut", module_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


doc_dates = _load_module()


# ── Pure helpers ────────────────────────────────────────────────────────────


def test_today_label_format() -> None:
    """today_label returns a human label like ``June 1, 2026``."""
    value = doc_dates.today_label()
    assert "," in value
    month, _, rest = value.partition(" ")
    assert month.isalpha()
    day, year = rest.replace(",", "").split()
    assert day.isdigit() and len(year) == 4


def test_marker_date_present_and_absent() -> None:
    """marker_date extracts the date from the last marker, or None when absent."""
    assert doc_dates.marker_date("intro\n\n_Updated June 1, 2026_\n") == "June 1, 2026"
    assert doc_dates.marker_date("no marker here") is None


def test_marker_date_uses_last_occurrence() -> None:
    """When several markers exist, the last (footer) one wins."""
    text = "_Updated January 1, 2020_\n\nbody\n\n_Updated June 1, 2026_\n"
    assert doc_dates.marker_date(text) == "June 1, 2026"


def test_stamp_text_appends_when_missing() -> None:
    """stamp_text appends a marker (blank-line separated) when none exists."""
    result = doc_dates.stamp_text("# Title\n\nBody.\n", "June 1, 2026")
    assert result == "# Title\n\nBody.\n\n_Updated June 1, 2026_\n"


def test_stamp_text_updates_existing() -> None:
    """stamp_text replaces an existing marker in place without duplicating."""
    original = "# Title\n\n_Updated January 1, 2020_\n"
    result = doc_dates.stamp_text(original, "June 1, 2026")
    assert result == "# Title\n\n_Updated June 1, 2026_\n"
    assert result.count("_Updated") == 1


def test_stamp_text_preserves_trailing_note() -> None:
    """A trailing editorial note after the marker is preserved."""
    original = "# Roadmap\n\n_Updated May 31, 2026_ (context note)\n"
    result = doc_dates.stamp_text(original, "June 1, 2026")
    assert result == "# Roadmap\n\n_Updated June 1, 2026_ (context note)\n"


def test_stamp_text_strips_legacy_footer() -> None:
    """The legacy ISO footer is removed so no duplicate label remains."""
    original = (
        "# Roadmap\n\n_Updated May 31, 2026_\n\nBody.\n\n_Last updated: 2026-06-01_\n"
    )
    result = doc_dates.stamp_text(original, "June 1, 2026")
    assert "_Last updated:" not in result
    assert result.count("_Updated") == 1
    assert "_Updated June 1, 2026_" in result


def test_stamp_text_migrates_header_style() -> None:
    """A ``_Last Updated: <date>_`` header is renamed to the canonical marker."""
    original = (
        "# Doc\n\n_Created: January 10, 2026_\n_Last Updated: January 10, 2026_\n"
    )
    result = doc_dates.stamp_text(original, "June 1, 2026")
    assert "_Last Updated:" not in result
    assert "_Created: January 10, 2026_" in result
    assert "_Updated June 1, 2026_" in result


# ── git change detection ────────────────────────────────────────────────────


def test_changed_files_parses_git_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """changed_files unions git outputs and normalizes backslashes."""

    def fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(
            cmd, 0, stdout="docs\\a.md\nREADME.md\n", stderr=""
        )

    monkeypatch.setattr(doc_dates.subprocess, "run", fake_run)
    result = doc_dates.changed_files(Path("."))
    assert result == {"docs/a.md", "README.md"}


def test_changed_files_handles_missing_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """changed_files returns an empty set when git is unavailable."""

    def boom(cmd, **kwargs):  # type: ignore[no-untyped-def]
        raise FileNotFoundError("git")

    monkeypatch.setattr(doc_dates.subprocess, "run", boom)
    assert doc_dates.changed_files(Path(".")) == set()


# ── Fixtures for stamp/check ────────────────────────────────────────────────


@pytest.fixture()
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temp repo with two persistent docs and patch the allowlist."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("# Readme\n\nBody.\n", encoding="utf-8")
    (tmp_path / "docs" / "guide.md").write_text("# Guide\n\nText.\n", encoding="utf-8")
    monkeypatch.setattr(doc_dates, "PERSISTENT_DOCS", ("README.md", "docs/guide.md"))
    return tmp_path


# ── stamp ────────────────────────────────────────────────────────────────────


def test_stamp_init_stamps_all(fake_repo: Path) -> None:
    """Init mode stamps every existing persistent doc."""
    stamped = doc_dates.stamp(fake_repo, init=True, today="June 1, 2026")
    assert set(stamped) == {"README.md", "docs/guide.md"}
    assert "_Updated June 1, 2026_" in (fake_repo / "README.md").read_text(
        encoding="utf-8"
    )


def test_stamp_files_scope(fake_repo: Path) -> None:
    """File-scoped stamping only touches the provided persistent docs."""
    stamped = doc_dates.stamp(fake_repo, files=["README.md"], today="June 1, 2026")
    assert stamped == ["README.md"]
    assert (
        doc_dates.marker_date((fake_repo / "docs" / "guide.md").read_text("utf-8"))
        is None
    )


def test_stamp_changed_scope(fake_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Default stamping targets persistent docs reported changed by git."""
    monkeypatch.setattr(doc_dates, "changed_files", lambda root: {"docs/guide.md"})
    stamped = doc_dates.stamp(fake_repo, today="June 1, 2026")
    assert stamped == ["docs/guide.md"]


def test_stamp_idempotent(fake_repo: Path) -> None:
    """Re-stamping with the same date reports no further changes."""
    doc_dates.stamp(fake_repo, init=True, today="June 1, 2026")
    again = doc_dates.stamp(fake_repo, init=True, today="June 1, 2026")
    assert again == []


# ── check ────────────────────────────────────────────────────────────────────


def test_check_full_flags_missing_marker(fake_repo: Path) -> None:
    """Full-scope check fails when a persistent doc has no marker."""
    problems = doc_dates.check(fake_repo, today="June 1, 2026")
    assert {rel for rel, _ in problems} == {"README.md", "docs/guide.md"}


def test_check_full_passes_with_any_valid_date(fake_repo: Path) -> None:
    """Full-scope check passes on a present, valid date (no equality to today)."""
    doc_dates.stamp(fake_repo, init=True, today="January 1, 2020")
    assert doc_dates.check(fake_repo, today="June 1, 2026") == []


def test_check_targeted_requires_today(fake_repo: Path) -> None:
    """Targeted check fails when a changed doc's date is not today."""
    doc_dates.stamp(fake_repo, files=["README.md"], today="January 1, 2020")
    problems = doc_dates.check(fake_repo, files=["README.md"], today="June 1, 2026")
    assert problems and problems[0][0] == "README.md"
    assert "not today" in problems[0][1]


def test_check_targeted_passes_when_today(fake_repo: Path) -> None:
    """Targeted check passes when the changed doc carries today's date."""
    doc_dates.stamp(fake_repo, files=["README.md"], today="June 1, 2026")
    assert doc_dates.check(fake_repo, files=["README.md"], today="June 1, 2026") == []


# ── CLI main ──────────────────────────────────────────────────────────────────


def test_main_stamp_init(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Main --stamp --init stamps docs and reports success."""
    monkeypatch.setattr(
        doc_dates,
        "stamp",
        lambda root, files=None, init=False, today=None: ["README.md"],
    )
    assert doc_dates.main(["--stamp", "--init"]) == 0
    assert "Stamped" in capsys.readouterr().out


def test_main_stamp_noop(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Main --stamp reports when nothing needs updating."""
    monkeypatch.setattr(doc_dates, "stamp", lambda *a, **k: [])
    assert doc_dates.main(["--stamp"]) == 0
    assert "No documentation dates" in capsys.readouterr().out


def test_main_check_pass(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Main --check returns 0 and prints OK when there are no problems."""
    monkeypatch.setattr(doc_dates, "check", lambda *a, **k: [])
    assert doc_dates.main(["--check"]) == 0
    assert "OK" in capsys.readouterr().out


def test_main_check_fail(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Main --check returns 1 and lists problems when markers are bad."""
    monkeypatch.setattr(doc_dates, "check", lambda *a, **k: [("README.md", "missing")])
    assert doc_dates.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert "FAILED" in out and "README.md" in out
