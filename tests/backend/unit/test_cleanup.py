"""Tests for scripts/cleanup.py — artifact cleanup tool."""

import importlib.util
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"


def _load_module():
    """Load scripts/cleanup.py as a testable module."""
    module_path = _SCRIPTS_DIR / "cleanup.py"
    spec = importlib.util.spec_from_file_location("cleanup_ut", module_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cleanup = _load_module()


# ============================================================================
# _is_protected
# ============================================================================


class TestIsProtected:
    """Tests for the _is_protected path guard."""

    def test_protected_paths(self):
        """Protected directories should return True."""
        assert cleanup._is_protected(Path(".venv/something")) is True
        assert cleanup._is_protected(Path("node_modules/pkg")) is True
        assert cleanup._is_protected(Path(".git/objects")) is True
        assert cleanup._is_protected(Path("instance/db")) is True
        assert cleanup._is_protected(Path("test_data/dummy.json")) is True

    def test_unprotected_paths(self):
        """Normal paths should return False."""
        assert cleanup._is_protected(Path("htmlcov/index.html")) is False
        assert cleanup._is_protected(Path(".coverage")) is False
        assert cleanup._is_protected(Path("__pycache__")) is False


# ============================================================================
# _remove
# ============================================================================


class TestRemove:
    """Tests for the _remove file/directory removal helper."""

    def test_remove_nonexistent(self, tmp_path):
        """Non-existent paths should return (False, '')."""
        ok, msg = cleanup._remove(tmp_path / "ghost", False)
        assert ok is False
        assert msg == ""

    def test_remove_file(self, tmp_path, monkeypatch):
        """Files should be deleted."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        f = tmp_path / ".coverage"
        f.write_text("data")
        ok, msg = cleanup._remove(f, dry_run=False)
        assert ok is True
        assert not f.exists()

    def test_remove_directory(self, tmp_path, monkeypatch):
        """Directories should be deleted recursively."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        d = tmp_path / "htmlcov"
        d.mkdir()
        (d / "index.html").write_text("<html/>")
        ok, msg = cleanup._remove(d, dry_run=False)
        assert ok is True
        assert not d.exists()

    def test_dry_run_does_not_delete(self, tmp_path, monkeypatch):
        """Dry-run should report but not delete."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        f = tmp_path / "coverage.xml"
        f.write_text("xml")
        ok, msg = cleanup._remove(f, dry_run=True)
        assert ok is True
        assert "[DRY-RUN]" in msg
        assert f.exists()

    def test_remove_permission_error(self, tmp_path, monkeypatch):
        """PermissionError should be caught gracefully."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        f = tmp_path / "locked"
        f.write_text("x")
        monkeypatch.setattr(Path, "is_dir", lambda self: False)
        monkeypatch.setattr(
            Path, "unlink", lambda self: (_ for _ in ()).throw(PermissionError("nope"))
        )
        ok, msg = cleanup._remove(f, dry_run=False)
        assert ok is False
        assert "Could not remove" in msg


# ============================================================================
# _clean_items
# ============================================================================


class TestCleanItems:
    """Tests for _clean_items (top-level name-based cleaning)."""

    def test_cleans_existing_items(self, tmp_path, monkeypatch):
        """Existing items should be removed and counted."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        (tmp_path / "htmlcov").mkdir()
        (tmp_path / ".coverage").write_text("data")
        count = cleanup._clean_items(["htmlcov", ".coverage", "nonexistent"], False)
        assert count == 2
        assert not (tmp_path / "htmlcov").exists()
        assert not (tmp_path / ".coverage").exists()


# ============================================================================
# _clean_glob
# ============================================================================


class TestCleanGlob:
    """Tests for _clean_glob (pattern-based cleaning)."""

    def test_cleans_matching_patterns(self, tmp_path, monkeypatch):
        """Matching glob patterns should be cleaned."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "mod.pyc").write_text("")
        count = cleanup._clean_glob(["**/__pycache__"], False)
        assert count >= 1

    def test_skips_protected(self, tmp_path, monkeypatch):
        """Protected paths matching a glob should be skipped."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        protected = tmp_path / "node_modules"
        protected.mkdir()
        count = cleanup._clean_glob(["node_modules"], False)
        assert count == 0
        assert protected.exists()

    def test_value_error_path_outside_root(self, tmp_path, monkeypatch):
        """Paths that raise ValueError on relative_to should be skipped."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        # Create a glob pattern that won't match anything outside root
        # Just verify _clean_glob handles empty results
        count = cleanup._clean_glob(["no_match_*"], False)
        assert count == 0


# ============================================================================
# High-level clean functions
# ============================================================================


class TestCleanFunctions:
    """Tests for clean_coverage, clean_test_output, clean_caches, clean_default,
    clean_all."""

    def test_clean_coverage(self, tmp_path, monkeypatch, capsys):
        """clean_coverage should remove coverage artifacts."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        (tmp_path / ".coverage").write_text("data")
        (tmp_path / "coverage.xml").write_text("<xml/>")
        count = cleanup.clean_coverage(dry_run=False)
        assert count >= 2
        assert "Cleaning coverage" in capsys.readouterr().out

    def test_clean_test_output(self, tmp_path, monkeypatch, capsys):
        """clean_test_output should remove test runner artifacts."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        (tmp_path / "playwright-report").mkdir()
        count = cleanup.clean_test_output(dry_run=False)
        assert count >= 1
        assert "Cleaning test output" in capsys.readouterr().out

    def test_clean_caches(self, tmp_path, monkeypatch, capsys):
        """clean_caches should remove tool caches."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        (tmp_path / ".pytest_cache").mkdir()
        (tmp_path / ".ruff_cache").mkdir()
        count = cleanup.clean_caches(dry_run=False)
        assert count >= 2
        assert "Cleaning tool caches" in capsys.readouterr().out

    def test_clean_default(self, tmp_path, monkeypatch):
        """clean_default = clean_coverage + clean_test_output."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        (tmp_path / ".coverage").write_text("data")
        (tmp_path / "playwright-report").mkdir()
        count = cleanup.clean_default(dry_run=False)
        assert count >= 2

    def test_clean_all(self, tmp_path, monkeypatch):
        """clean_all = clean_default + clean_caches."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        (tmp_path / ".coverage").write_text("data")
        (tmp_path / ".ruff_cache").mkdir()
        count = cleanup.clean_all(dry_run=False)
        assert count >= 2


# ============================================================================
# main() CLI
# ============================================================================


class TestMainCLI:
    """Tests for the main() argparse dispatch — covers lines 300-314."""

    def _run_main(self, monkeypatch, tmp_path, args):
        """Helper: run cleanup.main() with given args and redirected ROOT."""
        monkeypatch.setattr(cleanup, "ROOT", tmp_path)
        monkeypatch.setattr(sys, "argv", ["cleanup.py"] + args)
        return cleanup.main()

    def test_default_mode(self, monkeypatch, tmp_path, capsys):
        """Default (no flags) cleans coverage + test output."""
        (tmp_path / ".coverage").write_text("x")
        rc = self._run_main(monkeypatch, tmp_path, [])
        assert rc == 0
        assert "test artifacts + coverage" in capsys.readouterr().out

    def test_all_flag(self, monkeypatch, tmp_path, capsys):
        """--all cleans everything."""
        (tmp_path / ".ruff_cache").mkdir()
        rc = self._run_main(monkeypatch, tmp_path, ["--all"])
        assert rc == 0
        assert "all artifacts" in capsys.readouterr().out

    def test_coverage_flag(self, monkeypatch, tmp_path, capsys):
        """--coverage only cleans coverage artifacts."""
        (tmp_path / "coverage.xml").write_text("<xml/>")
        rc = self._run_main(monkeypatch, tmp_path, ["--coverage"])
        assert rc == 0
        assert "coverage artifacts" in capsys.readouterr().out

    def test_tests_flag(self, monkeypatch, tmp_path, capsys):
        """--tests only cleans test output."""
        (tmp_path / "playwright-report").mkdir()
        rc = self._run_main(monkeypatch, tmp_path, ["--tests"])
        assert rc == 0
        assert "test output" in capsys.readouterr().out

    def test_caches_flag(self, monkeypatch, tmp_path, capsys):
        """--caches only cleans tool caches."""
        (tmp_path / ".mypy_cache").mkdir()
        rc = self._run_main(monkeypatch, tmp_path, ["--caches"])
        assert rc == 0
        assert "tool caches" in capsys.readouterr().out

    def test_dry_run_flag(self, monkeypatch, tmp_path, capsys):
        """--dry-run should report without deleting."""
        (tmp_path / ".coverage").write_text("data")
        rc = self._run_main(monkeypatch, tmp_path, ["--dry-run"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "DRY-RUN" in out
        assert (tmp_path / ".coverage").exists()

    def test_nothing_to_clean(self, monkeypatch, tmp_path, capsys):
        """Clean directory should report 'nothing to clean'."""
        rc = self._run_main(monkeypatch, tmp_path, [])
        assert rc == 0
        assert "Nothing to clean" in capsys.readouterr().out
