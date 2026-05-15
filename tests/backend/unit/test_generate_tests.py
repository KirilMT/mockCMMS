"""Tests for scripts/generate_tests.py — test stub generation tool."""

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loading (follows project pattern for script testing)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"


def _load_module():
    """Load scripts/generate_tests.py as a testable module."""
    module_path = _SCRIPTS_DIR / "generate_tests.py"
    spec = importlib.util.spec_from_file_location("generate_tests_ut", module_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _load_module()


# ============================================================================
# CodeAnalyzer
# ============================================================================


class TestCodeAnalyzer:
    """Tests for the AST-based code analyzer."""

    def test_analyze_finds_public_functions_and_classes(self, tmp_path):
        """Public top-level entities should be returned."""
        src = tmp_path / "sample.py"
        src.write_text(
            "class Foo:\n    pass\n\n"
            "def bar():\n    pass\n\n"
            "def _private():\n    pass\n"
        )
        analyzer = gen.CodeAnalyzer(str(src))
        entities = analyzer.analyze()
        names = [e[0] for e in entities]
        assert "Foo" in names
        assert "bar" in names
        assert "_private" not in names

    def test_analyze_returns_types(self, tmp_path):
        """Each entity should carry its type ('class' or 'function')."""
        src = tmp_path / "typed.py"
        src.write_text("class A:\n    pass\n\ndef b():\n    pass\n")
        entities = gen.CodeAnalyzer(str(src)).analyze()
        types = {e[0]: e[1] for e in entities}
        assert types["A"] == "class"
        assert types["b"] == "function"

    def test_analyze_includes_public_async_functions(self, tmp_path):
        """Public top-level async functions should be returned as functions."""
        src = tmp_path / "async_mod.py"
        src.write_text("async def fetch():\n    return 1\n")
        entities = gen.CodeAnalyzer(str(src)).analyze()
        assert entities == [("fetch", "function")]

    def test_analyze_handles_utf8_bom(self, tmp_path):
        """UTF-8 BOM-prefixed files should parse correctly."""
        src = tmp_path / "bom_mod.py"
        src.write_text("\ufeffdef hello():\n    return 'hi'\n", encoding="utf-8")
        entities = gen.CodeAnalyzer(str(src)).analyze()
        assert entities == [("hello", "function")]

    def test_analyze_empty_file(self, tmp_path):
        """An empty file should return an empty list."""
        src = tmp_path / "empty.py"
        src.write_text("")
        assert gen.CodeAnalyzer(str(src)).analyze() == []

    def test_analyze_syntax_error(self, tmp_path, capsys):
        """A file with syntax errors should return [] and print a warning."""
        src = tmp_path / "bad.py"
        src.write_text("def broken(:\n    pass\n")
        result = gen.CodeAnalyzer(str(src)).analyze()
        assert result == []
        assert "Syntax error" in capsys.readouterr().out


# ============================================================================
# TestGenerator
# ============================================================================


class TestTestGenerator:
    """Tests for the pytest stub generator."""

    def test_detect_category_api(self):
        """api.py maps to 'functional'."""
        tg = gen.TestGenerator("src/routes/api.py")
        assert tg.category == "functional"

    def test_detect_category_services(self):
        """Anything in services/ maps to 'unit'."""
        tg = gen.TestGenerator("src/services/utils.py")
        assert tg.category == "unit"

    def test_detect_category_default(self):
        """Unknown paths fall back to 'unit'."""
        tg = gen.TestGenerator("src/something_else.py")
        assert tg.category == "unit"

    def test_detect_category_explicit(self):
        """Explicit category overrides auto-detection."""
        tg = gen.TestGenerator("src/routes/api.py", category="integration")
        assert tg.category == "integration"

    def test_generate_empty_entities(self):
        """Empty entity list returns empty string."""
        tg = gen.TestGenerator("src/foo.py")
        assert tg.generate([]) == ""

    def test_generate_includes_imports_and_class(self):
        """Generated code should contain an import block and a test class."""
        tg = gen.TestGenerator("src/services/my_module.py")
        code = tg.generate([("MyClass", "class")])
        assert "import pytest" in code
        assert "class TestMyClass:" in code
        assert "my_module" in code

    def test_generate_function_tests(self):
        """Generated code should contain function test stubs."""
        tg = gen.TestGenerator("src/services/util.py")
        code = tg.generate([("do_stuff", "function")])
        assert "test_do_stuff_is_callable" in code
        assert "test_do_stuff" in code

    def test_generate_for_app_source_uses_app_import_path(self):
        """App source files should import from apps.<app>.src...

        paths.
        """
        tg = gen.TestGenerator("apps/reporting/src/services/report_generator.py")
        code = tg.generate([("ReportGenerator", "class")])
        assert "from apps.reporting.src.services.report_generator import (" in code

    def test_generate_for_script_uses_path_loader_block(self):
        """Scripts should use importlib-based loading instead of direct imports."""
        tg = gen.TestGenerator("scripts/cleanup.py")
        code = tg.generate([("clean_default", "function")])
        assert "import importlib.util" in code
        assert "def _find_repo_root() -> Path:" in code
        assert "module_under_test = _load_module()" in code
        assert "clean_default = module_under_test.clean_default" in code

    def test_generate_for_root_module_uses_direct_import(self):
        """Root-level modules should import directly by module name."""
        tg = gen.TestGenerator("run.py")
        code = tg.generate([("main", "function")])
        assert "from run import (" in code

    def test_generate_for_collab_source_uses_path_loader_block(self):
        """Legacy in-repo collab sources should use file loading because they are not
        import packages."""
        tg = gen.TestGenerator(".collab/dashboard/server.py")
        code = tg.generate([("serve", "function")])
        assert "module_path = _find_repo_root()" in code
        assert "server.py" in code
        assert "serve = module_under_test.serve" in code

    def test_get_import_path(self):
        """Import path should be derived from the source file."""
        tg = gen.TestGenerator("src/services/foo.py")
        assert tg._get_import_path() == "services.foo"

    def test_get_import_path_no_src(self):
        """Non-src paths keep their dotted relative path when inside the repo."""
        tg = gen.TestGenerator("other/bar.py")
        assert tg._get_import_path() == "other.bar"

    def test_get_test_file_for_core_source(self):
        """Core src files should map to tests/backend/<category>."""
        tg = gen.TestGenerator("src/services/foo.py")
        expected = Path(gen.ROOT) / "tests" / "backend" / "unit" / "test_foo.py"
        assert tg.get_test_file() == expected

    def test_get_test_file_for_app_source(self):
        """App source files should map to app-local backend tests."""
        tg = gen.TestGenerator("apps/reporting/src/services/report_generator.py")
        expected = (
            Path(gen.ROOT)
            / "apps"
            / "reporting"
            / "tests"
            / "backend"
            / "unit"
            / "test_report_generator.py"
        )
        assert tg.get_test_file() == expected

    def test_get_test_file_for_collab_source(self):
        """Legacy in-repo collab paths should fall back to core backend test roots.

        Strict Phase 4 removes the in-repo collab source tree, so generator outputs for
        those legacy paths now route to tests/backend/<category>.
        """
        tg = gen.TestGenerator(".collab/dashboard/server.py")
        expected = Path(gen.ROOT) / "tests" / "backend" / "unit" / "test_server.py"
        assert tg.get_test_file() == expected

    def test_get_test_file_for_root_source(self):
        """Root-level files should map to tests/backend/<category>."""
        tg = gen.TestGenerator("run.py")
        expected = Path(gen.ROOT) / "tests" / "backend" / "unit" / "test_run.py"
        assert tg.get_test_file() == expected


# ============================================================================
# TestDiscovery
# ============================================================================


class TestTestDiscovery:
    """Tests for the untested-module scanner."""

    def test_find_untested_returns_missing(self, tmp_path, monkeypatch):
        """Modules without corresponding test_*.py should be reported."""
        # Create a source module
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "alpha.py").write_text("x = 1\n")
        (src_dir / "_private.py").write_text("x = 1\n")

        # Create a test dir with one existing test
        test_dir = tmp_path / "tests" / "backend"
        test_dir.mkdir(parents=True)
        (test_dir / "test_alpha.py").write_text("")

        disc = gen.TestDiscovery()
        monkeypatch.setattr(disc, "test_dir", str(test_dir))
        untested = disc.find_untested(str(src_dir))
        # alpha has a test, _private is private → nothing returned
        assert untested == []

    def test_find_untested_with_missing_test(self, tmp_path, monkeypatch):
        """A public module without a test should appear in the list."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "beta.py").write_text("x = 1\n")

        test_dir = tmp_path / "tests" / "backend"
        test_dir.mkdir(parents=True)
        # No test_beta.py

        disc = gen.TestDiscovery()
        monkeypatch.setattr(disc, "test_dir", str(test_dir))
        untested = disc.find_untested(str(src_dir))
        assert any("beta.py" in u for u in untested)

    def test_find_untested_repo_scan_uses_expected_locations(self, tmp_path):
        """Repo scans should check each source file against its expected test path."""
        (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
        (tmp_path / "AGENTS.md").write_text("# repo\n")

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "cleanup.py").write_text(
            "def clean_default():\n    return None\n"
        )

        reporting_src = tmp_path / "apps" / "reporting" / "src" / "services"
        reporting_src.mkdir(parents=True)
        (reporting_src / "report_generator.py").write_text(
            "class ReportGenerator:\n    pass\n"
        )

        run_py = tmp_path / "run.py"
        run_py.write_text("def main():\n    return None\n")

        cleanup_test = tmp_path / "tests" / "backend" / "unit"
        cleanup_test.mkdir(parents=True)
        (cleanup_test / "test_cleanup.py").write_text("# existing\n")

        reporting_test = tmp_path / "apps" / "reporting" / "tests" / "backend" / "unit"
        reporting_test.mkdir(parents=True)
        (reporting_test / "test_report_generator.py").write_text("# existing\n")

        disc = gen.TestDiscovery(repo_root=tmp_path)
        untested = disc.find_untested()

        assert "scripts/cleanup.py" not in untested
        assert "apps/reporting/src/services/report_generator.py" not in untested
        assert "run.py" in untested


# ============================================================================
# main() CLI entry-point
# ============================================================================


class TestMain:
    """Tests for the main() CLI function branches."""

    def test_scan_mode(self, monkeypatch, capsys, tmp_path):
        """--scan should list untested modules and return."""
        monkeypatch.setattr(sys, "argv", ["generate_tests.py", "--scan"])
        # Provide a dummy src dir to avoid scanning real src/
        discovery = gen.TestDiscovery()
        monkeypatch.setattr(discovery, "test_dir", str(tmp_path / "t"))
        monkeypatch.setattr(gen, "TestDiscovery", lambda: discovery)
        gen.main()
        out = capsys.readouterr().out
        assert "Untested modules" in out or "All modules have tests" in out

    def test_no_source_file_prints_help(self, monkeypatch):
        """No source file and no --scan should print help and exit(1)."""
        monkeypatch.setattr(sys, "argv", ["generate_tests.py"])
        with pytest.raises(SystemExit) as exc_info:
            gen.main()
        assert exc_info.value.code == 1

    def test_missing_file_exits(self, monkeypatch):
        """A non-existent source file should exit(1)."""
        monkeypatch.setattr(sys, "argv", ["generate_tests.py", "/nonexistent/file.py"])
        with pytest.raises(SystemExit) as exc_info:
            gen.main()
        assert exc_info.value.code == 1

    def test_no_entities_returns_early(self, monkeypatch, tmp_path, capsys):
        """A file with no public entities should warn and return."""
        src = tmp_path / "empty.py"
        src.write_text("# nothing here\n")
        monkeypatch.setattr(sys, "argv", ["generate_tests.py", str(src)])
        gen.main()
        assert "No testable entities" in capsys.readouterr().out

    def test_directory_without_scan_exits(self, monkeypatch, tmp_path):
        """Directories should require --scan instead of generation mode."""
        monkeypatch.setattr(sys, "argv", ["generate_tests.py", str(tmp_path)])
        with pytest.raises(SystemExit) as exc_info:
            gen.main()
        assert exc_info.value.code == 1

    def test_dry_run(self, monkeypatch, tmp_path, capsys):
        """--dry-run should print the template without creating a file."""
        src = tmp_path / "module.py"
        src.write_text("def hello():\n    pass\n")
        monkeypatch.setattr(sys, "argv", ["generate_tests.py", str(src), "--dry-run"])
        gen.main()
        out = capsys.readouterr().out
        assert "Preview mode" in out
        assert "test_hello" in out

    def test_output_root(self, monkeypatch, tmp_path, capsys):
        """--output-root should control where the test file is written."""
        src = tmp_path / "mod.py"
        src.write_text("def fn():\n    pass\n")
        out_root = tmp_path / "custom_tests"
        monkeypatch.setattr(
            sys,
            "argv",
            ["generate_tests.py", str(src), "--output-root", str(out_root)],
        )
        gen.main()
        # Should have created custom_tests/unit/test_mod.py
        expected = out_root / "unit" / "test_mod.py"
        assert expected.exists()

    def test_file_exists_no_force(self, monkeypatch, tmp_path, capsys):
        """Existing file without --force should warn and return."""
        src = tmp_path / "exists.py"
        src.write_text("def f():\n    pass\n")
        out_root = tmp_path / "tests"
        test_dir = out_root / "unit"
        test_dir.mkdir(parents=True)
        (test_dir / "test_exists.py").write_text("# existing\n")
        monkeypatch.setattr(
            sys,
            "argv",
            ["generate_tests.py", str(src), "--output-root", str(out_root)],
        )
        gen.main()
        assert "File exists" in capsys.readouterr().out

    def test_force_overwrites(self, monkeypatch, tmp_path):
        """--force should overwrite an existing test file."""
        src = tmp_path / "overwrite.py"
        src.write_text("def g():\n    pass\n")
        out_root = tmp_path / "tests"
        test_dir = out_root / "unit"
        test_dir.mkdir(parents=True)
        existing = test_dir / "test_overwrite.py"
        existing.write_text("# old\n")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "generate_tests.py",
                str(src),
                "--output-root",
                str(out_root),
                "--force",
            ],
        )
        gen.main()
        assert "test_g" in existing.read_text()
