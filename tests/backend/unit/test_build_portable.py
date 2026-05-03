"""Tests for scripts/build_portable.py — portable distribution builder.

All network/filesystem side-effects are mocked; no downloads or builds occur.
"""

import importlib.util
import subprocess
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"


def _load_module():
    """Load scripts/build_portable.py as a testable module."""
    module_path = _SCRIPTS_DIR / "build_portable.py"
    spec = importlib.util.spec_from_file_location("build_portable_ut", module_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bp = _load_module()


# ============================================================================
# Constants / Smoke Tests
# ============================================================================


class TestConstants:
    """Verify module-level constants are sane."""

    def test_python_version_set(self):
        assert bp.PYTHON_VERSION
        assert "." in bp.PYTHON_VERSION

    def test_app_version_set(self):
        assert bp.APP_VERSION
        assert "." in bp.APP_VERSION

    def test_paths_are_path_objects(self):
        assert isinstance(bp.REPO_ROOT, Path)
        assert isinstance(bp.DIST_DIR, Path)
        assert isinstance(bp.BUILD_DIR, Path)
        assert isinstance(bp.PYTHON_DIR, Path)
        assert isinstance(bp.APP_DIR, Path)


# ============================================================================
# print_step
# ============================================================================


class TestPrintStep:
    """Tests for the formatted step printer."""

    def test_prints_formatted_message(self, capsys):
        bp.print_step("Hello World")
        out = capsys.readouterr().out
        assert "Hello World" in out
        assert "=" in out


# ============================================================================
# download_python_embeddable
# ============================================================================


class TestDownloadPythonEmbeddable:
    """Tests for the Python downloader (fully mocked)."""

    def test_skip_if_exists(self, tmp_path, monkeypatch, capsys):
        """Should skip download when zip already exists."""
        monkeypatch.setattr(bp, "DIST_DIR", tmp_path)
        zip_path = tmp_path / f"python-{bp.PYTHON_VERSION}-embed-amd64.zip"
        zip_path.write_text("fake")
        bp.download_python_embeddable()
        assert "already downloaded" in capsys.readouterr().out

    def test_downloads_when_missing(self, tmp_path, monkeypatch):
        """Should call _secure_download when zip does not exist."""
        monkeypatch.setattr(bp, "DIST_DIR", tmp_path)
        zip_path = tmp_path / f"python-{bp.PYTHON_VERSION}-embed-amd64.zip"
        calls = []

        def fake_download(url, dest):
            calls.append((url, dest))
            dest.write_text("fake-zip")

        monkeypatch.setattr(bp, "_secure_download", fake_download)
        bp.download_python_embeddable()
        assert len(calls) == 1
        assert zip_path.exists()


# ============================================================================
# _secure_download
# ============================================================================


class TestSecureDownload:
    """Tests for the _secure_download HTTPS downloader (fully mocked)."""

    def _make_mock_conn(self, status=200, body=b"content", location=None):
        """Create a mock HTTPSConnection with a chainable response."""
        mock_resp = MagicMock()
        mock_resp.status = status
        mock_resp.read.return_value = body
        mock_resp.getheader.return_value = location or ""
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_resp
        return mock_conn

    def test_successful_download(self, tmp_path, monkeypatch):
        """Should download content to dest on HTTP 200."""
        mock_conn = self._make_mock_conn(status=200, body=b"fake-data")
        monkeypatch.setattr(
            bp.http.client, "HTTPSConnection", lambda *a, **kw: mock_conn
        )
        dest = tmp_path / "file.zip"
        bp._secure_download("https://example.com/file.zip", dest)
        assert dest.read_bytes() == b"fake-data"
        mock_conn.request.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_rejects_non_https_url(self, tmp_path):
        """Should raise ValueError for non-HTTPS URLs."""
        dest = tmp_path / "file.zip"
        with pytest.raises(ValueError, match="Only HTTPS URLs are allowed"):
            bp._secure_download("http://example.com/file.zip", dest)

    def test_follows_redirects(self, tmp_path, monkeypatch):
        """Should follow 302 redirect and download from new location."""
        redirect_conn = self._make_mock_conn(
            status=302, location="https://cdn.example.com/file.zip"
        )
        final_conn = self._make_mock_conn(status=200, body=b"redirected-data")
        call_count = [0]

        def mock_https_conn(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return redirect_conn
            return final_conn

        monkeypatch.setattr(bp.http.client, "HTTPSConnection", mock_https_conn)
        dest = tmp_path / "file.zip"
        bp._secure_download("https://example.com/file.zip", dest)
        assert dest.read_bytes() == b"redirected-data"
        assert call_count[0] == 2

    def test_http_error_raises(self, tmp_path, monkeypatch):
        """Should raise RuntimeError on non-200/non-redirect status."""
        mock_conn = self._make_mock_conn(status=404)
        monkeypatch.setattr(
            bp.http.client, "HTTPSConnection", lambda *a, **kw: mock_conn
        )
        dest = tmp_path / "file.zip"
        with pytest.raises(RuntimeError, match="Download failed: HTTP 404"):
            bp._secure_download("https://example.com/missing.zip", dest)

    def test_too_many_redirects(self, tmp_path, monkeypatch):
        """Should raise RuntimeError after 5 redirects."""
        mock_conn = self._make_mock_conn(
            status=301, location="https://example.com/loop"
        )
        monkeypatch.setattr(
            bp.http.client, "HTTPSConnection", lambda *a, **kw: mock_conn
        )
        dest = tmp_path / "file.zip"
        with pytest.raises(RuntimeError, match="Too many redirects"):
            bp._secure_download("https://example.com/loop", dest)

    def test_url_with_query_string(self, tmp_path, monkeypatch):
        """Should include query string in the request path."""
        mock_conn = self._make_mock_conn(status=200, body=b"qs-data")
        monkeypatch.setattr(
            bp.http.client, "HTTPSConnection", lambda *a, **kw: mock_conn
        )
        dest = tmp_path / "file.zip"
        bp._secure_download("https://example.com/dl?v=1&t=2", dest)
        # Verify the path included the query string
        call_args = mock_conn.request.call_args
        assert "?v=1&t=2" in call_args[0][1]


# ============================================================================
# extract_python_embeddable
# ============================================================================


class TestExtractPythonEmbeddable:
    """Tests for the Python zip extractor."""

    def test_extracts_zip(self, tmp_path, monkeypatch):
        """Should extract the zip into PYTHON_DIR."""
        monkeypatch.setattr(bp, "DIST_DIR", tmp_path)
        python_dir = tmp_path / "python"
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)

        # Create a real zip
        zip_path = tmp_path / f"python-{bp.PYTHON_VERSION}-embed-amd64.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("python.exe", "fake-exe")
        bp.extract_python_embeddable()
        assert (python_dir / "python.exe").exists()


# ============================================================================
# install_pip
# ============================================================================


class TestInstallPip:
    """Tests for the pip installer (mocked subprocess)."""

    def test_installs_pip_successfully(self, tmp_path, monkeypatch):
        """Successful pip install should not raise."""
        python_dir = tmp_path / "python"
        python_dir.mkdir()
        (python_dir / "python.exe").write_text("fake")
        # Create pth file with commented import site
        pth = python_dir / f"python{bp.PYTHON_VERSION.replace('.', '')[:3]}._pth"
        pth.write_text("#import site\n.\n")
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)
        monkeypatch.setattr(
            bp,
            "_secure_download",
            lambda url, dest: dest.write_text("fake"),
        )
        monkeypatch.setattr(
            bp.subprocess,
            "run",
            lambda *a, **kw: MagicMock(returncode=0, stdout="pip 24.0", stderr=""),
        )
        bp.install_pip()
        # Verify pth was modified
        content = pth.read_text()
        assert "import site" in content
        assert "#import site" not in content

    def test_pth_already_has_import_site(self, tmp_path, monkeypatch):
        """If pth already has 'import site', it should not be duplicated."""
        python_dir = tmp_path / "python"
        python_dir.mkdir()
        (python_dir / "python.exe").write_text("fake")
        pth = python_dir / f"python{bp.PYTHON_VERSION.replace('.', '')[:3]}._pth"
        pth.write_text("import site\n.\n")
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)
        monkeypatch.setattr(
            bp,
            "_secure_download",
            lambda url, dest: dest.write_text("fake"),
        )
        monkeypatch.setattr(
            bp.subprocess,
            "run",
            lambda *a, **kw: MagicMock(returncode=0, stdout="pip 24.0", stderr=""),
        )
        bp.install_pip()
        assert pth.read_text().count("import site") == 1

    def test_pth_missing(self, tmp_path, monkeypatch, capsys):
        """Missing pth file should print a warning."""
        python_dir = tmp_path / "python"
        python_dir.mkdir()
        (python_dir / "python.exe").write_text("fake")
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)
        monkeypatch.setattr(
            bp,
            "_secure_download",
            lambda url, dest: dest.write_text("fake"),
        )
        monkeypatch.setattr(
            bp.subprocess,
            "run",
            lambda *a, **kw: MagicMock(returncode=0, stdout="pip 24.0", stderr=""),
        )
        bp.install_pip()
        assert "not found" in capsys.readouterr().out

    def test_pip_install_failure(self, tmp_path, monkeypatch):
        """Failed pip install should raise RuntimeError."""
        python_dir = tmp_path / "python"
        python_dir.mkdir()
        (python_dir / "python.exe").write_text("fake")
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)
        monkeypatch.setattr(
            bp,
            "_secure_download",
            lambda url, dest: dest.write_text("fake"),
        )
        call_count = [0]

        def mock_run(*a, **kw):
            call_count[0] += 1
            return MagicMock(returncode=1, stdout="error", stderr="fail")

        monkeypatch.setattr(bp.subprocess, "run", mock_run)
        with pytest.raises(RuntimeError, match="pip installation failed"):
            bp.install_pip()

    def test_pip_verify_failure(self, tmp_path, monkeypatch):
        """Failed pip verify should raise RuntimeError."""
        python_dir = tmp_path / "python"
        python_dir.mkdir()
        (python_dir / "python.exe").write_text("fake")
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)
        monkeypatch.setattr(
            bp,
            "_secure_download",
            lambda url, dest: dest.write_text("fake"),
        )
        call_count = [0]

        def mock_run(*a, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(returncode=0, stdout="installed", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="not found")

        monkeypatch.setattr(bp.subprocess, "run", mock_run)
        with pytest.raises(RuntimeError, match="not installed correctly"):
            bp.install_pip()


# ============================================================================
# install_dependencies
# ============================================================================


class TestInstallDependencies:
    """Tests for dependency installation."""

    def test_successful_install(self, tmp_path, monkeypatch):
        """Successful dependency installation should complete."""
        monkeypatch.setattr(bp, "PYTHON_DIR", tmp_path / "python")
        (tmp_path / "python").mkdir()
        (tmp_path / "python" / "python.exe").write_text("fake")
        monkeypatch.setattr(bp, "REPO_ROOT", tmp_path)
        (tmp_path / "requirements.txt").write_text("flask\n")
        monkeypatch.setattr(
            bp.subprocess,
            "run",
            lambda *a, **kw: MagicMock(returncode=0, stdout="ok", stderr=""),
        )
        bp.install_dependencies()

    def test_pip_not_available(self, tmp_path, monkeypatch):
        """Should raise if pip is not available."""
        monkeypatch.setattr(bp, "PYTHON_DIR", tmp_path / "python")
        (tmp_path / "python").mkdir()
        (tmp_path / "python" / "python.exe").write_text("fake")
        monkeypatch.setattr(bp, "REPO_ROOT", tmp_path)
        (tmp_path / "requirements.txt").write_text("flask\n")
        monkeypatch.setattr(
            bp.subprocess,
            "run",
            lambda *a, **kw: MagicMock(returncode=1, stdout="", stderr="err"),
        )
        with pytest.raises(RuntimeError, match="pip is not installed"):
            bp.install_dependencies()

    def test_dependency_install_failure(self, tmp_path, monkeypatch):
        """Should raise if pip install -r fails."""
        monkeypatch.setattr(bp, "PYTHON_DIR", tmp_path / "python")
        (tmp_path / "python").mkdir()
        (tmp_path / "python" / "python.exe").write_text("fake")
        monkeypatch.setattr(bp, "REPO_ROOT", tmp_path)
        (tmp_path / "requirements.txt").write_text("flask\n")
        call_count = [0]

        def mock_run(*a, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(returncode=0, stdout="pip ok", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="install failed")

        monkeypatch.setattr(bp.subprocess, "run", mock_run)
        with pytest.raises(RuntimeError, match="Failed to install"):
            bp.install_dependencies()


# ============================================================================
# copy_application
# ============================================================================


class TestCopyApplication:
    """Tests for application file copying."""

    def test_copies_existing_dirs_and_files(self, tmp_path, monkeypatch):
        """Should copy existing source dirs and root files."""
        repo = tmp_path / "repo"
        repo.mkdir()
        app_dir = tmp_path / "app"
        monkeypatch.setattr(bp, "REPO_ROOT", repo)
        monkeypatch.setattr(bp, "APP_DIR", app_dir)

        # Create a source dir
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("# app")
        # Create a root file
        (repo / "run.py").write_text("# run")
        (repo / ".env.example").write_text("# env")

        bp.copy_application()

        assert (app_dir / "src" / "app.py").exists()
        assert (app_dir / "run.py").exists()


# ============================================================================
# create_env_file, create_launcher_scripts, create_readme
# ============================================================================


class TestFileCreators:
    """Tests for env, launcher, and readme creators."""

    def test_create_env_file(self, tmp_path, monkeypatch):
        """Should create .env with correct content."""
        monkeypatch.setattr(bp, "APP_DIR", tmp_path)
        bp.create_env_file()
        env_content = (tmp_path / ".env").read_text()
        assert "PORTABLE_DISTRIBUTION=true" in env_content
        assert "FLASK_APP=run.py" in env_content

    def test_create_launcher_scripts(self, tmp_path, monkeypatch):
        """Should create START_mockCMMS.bat."""
        monkeypatch.setattr(bp, "BUILD_DIR", tmp_path)
        bp.create_launcher_scripts()
        bat = tmp_path / "START_mockCMMS.bat"
        assert bat.exists()
        content = bat.read_text(encoding="utf-8")
        assert "mockCMMS" in content
        assert "python.exe" in content

    def test_create_readme(self, tmp_path, monkeypatch):
        """Should create README.txt with instructions."""
        monkeypatch.setattr(bp, "BUILD_DIR", tmp_path)
        bp.create_readme()
        readme = tmp_path / "README.txt"
        assert readme.exists()
        content = readme.read_text()
        assert "QUICK START" in content
        assert "admin" in content


# ============================================================================
# seed_databases
# ============================================================================


class TestSeedDatabases:
    """Tests for database seeding step."""

    def test_skips_when_no_seed_script(self, tmp_path, monkeypatch, capsys):
        """Should skip gracefully when seed script is missing."""
        monkeypatch.setattr(bp, "APP_DIR", tmp_path)
        monkeypatch.setattr(bp, "PYTHON_DIR", tmp_path)
        bp.seed_databases()
        assert "not found" in capsys.readouterr().out

    def test_runs_seed_script(self, tmp_path, monkeypatch):
        """Should call seed script via subprocess when it exists."""
        app_dir = tmp_path / "app"
        (app_dir / "src" / "services").mkdir(parents=True)
        (app_dir / "src" / "services" / "db_seeding.py").write_text("# seed")
        python_dir = tmp_path / "python"
        python_dir.mkdir()
        monkeypatch.setattr(bp, "APP_DIR", app_dir)
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)
        monkeypatch.setattr(bp.subprocess, "run", lambda *a, **kw: None)
        bp.seed_databases()

    def test_handles_seed_failure(self, tmp_path, monkeypatch, capsys):
        """CalledProcessError from seeding should be caught."""
        app_dir = tmp_path / "app"
        (app_dir / "src" / "services").mkdir(parents=True)
        (app_dir / "src" / "services" / "db_seeding.py").write_text("# seed")
        python_dir = tmp_path / "python"
        python_dir.mkdir()
        monkeypatch.setattr(bp, "APP_DIR", app_dir)
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)

        def fail(*a, **kw):
            raise subprocess.CalledProcessError(1, "seed")

        monkeypatch.setattr(bp.subprocess, "run", fail)
        bp.seed_databases()
        assert "Seeding failed" in capsys.readouterr().out


# ============================================================================
# create_zip_package
# ============================================================================


class TestCreateZipPackage:
    """Tests for zip package creation."""

    def test_creates_zip(self, tmp_path, monkeypatch):
        """Should create a valid zip file."""
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        build_dir = dist_dir / f"mockCMMS-portable-v{bp.APP_VERSION}"
        build_dir.mkdir()
        (build_dir / "file.txt").write_text("hello")
        monkeypatch.setattr(bp, "DIST_DIR", dist_dir)
        monkeypatch.setattr(bp, "BUILD_DIR", build_dir)

        result = bp.create_zip_package()
        assert result.exists()
        assert result.suffix == ".zip"

    def test_removes_existing_zip(self, tmp_path, monkeypatch):
        """Should remove an existing zip before creating a new one."""
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        build_dir = dist_dir / f"mockCMMS-portable-v{bp.APP_VERSION}"
        build_dir.mkdir()
        (build_dir / "f.txt").write_text("x")
        existing = dist_dir / f"mockCMMS-portable-v{bp.APP_VERSION}.zip"
        existing.write_text("old")
        monkeypatch.setattr(bp, "DIST_DIR", dist_dir)
        monkeypatch.setattr(bp, "BUILD_DIR", build_dir)

        result = bp.create_zip_package()
        assert result.exists()
        # Old content should be gone
        with zipfile.ZipFile(result) as zf:
            assert len(zf.namelist()) >= 1


# ============================================================================
# cleanup_build_directory
# ============================================================================


class TestCleanupBuildDirectory:
    """Tests for build directory cleanup."""

    def test_removes_build_dir(self, tmp_path, monkeypatch):
        """Should remove the build directory."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "file.txt").write_text("x")
        monkeypatch.setattr(bp, "BUILD_DIR", build_dir)
        bp.cleanup_build_directory()
        assert not build_dir.exists()


# ============================================================================
# main()
# ============================================================================


class TestMain:
    """Tests for the main() build orchestrator."""

    def test_main_success(self, tmp_path, monkeypatch, capsys):
        """Successful build should print BUILD SUCCESSFUL."""
        dist_dir = tmp_path / "dist"
        build_dir = dist_dir / f"mockCMMS-portable-v{bp.APP_VERSION}"
        python_dir = build_dir / "python"
        app_dir = build_dir / "app"

        monkeypatch.setattr(bp, "DIST_DIR", dist_dir)
        monkeypatch.setattr(bp, "BUILD_DIR", build_dir)
        monkeypatch.setattr(bp, "PYTHON_DIR", python_dir)
        monkeypatch.setattr(bp, "APP_DIR", app_dir)
        monkeypatch.setattr(bp, "REPO_ROOT", tmp_path)

        # Create requirements.txt
        (tmp_path / "requirements.txt").write_text("flask\n")
        (tmp_path / "run.py").write_text("# run")

        # Mock all network + subprocess calls
        monkeypatch.setattr(
            bp,
            "_secure_download",
            lambda url, dest: dest.write_text("fake"),
        )
        monkeypatch.setattr(
            bp.subprocess,
            "run",
            lambda *a, **kw: MagicMock(returncode=0, stdout="ok", stderr=""),
        )

        # Mock extract to create python dir
        def fake_extract():
            python_dir.mkdir(parents=True, exist_ok=True)
            (python_dir / "python.exe").write_text("fake")

        monkeypatch.setattr(bp, "extract_python_embeddable", fake_extract)

        bp.main()
        out = capsys.readouterr().out
        assert "BUILD SUCCESSFUL" in out

    def test_main_failure(self, tmp_path, monkeypatch, capsys):
        """Build failure should print BUILD FAILED and exit(1)."""
        monkeypatch.setattr(bp, "DIST_DIR", tmp_path / "dist")

        def fail():
            raise RuntimeError("Boom")

        monkeypatch.setattr(bp, "download_python_embeddable", fail)

        with pytest.raises(SystemExit) as exc:
            bp.main()
        assert exc.value.code == 1
        assert "BUILD FAILED" in capsys.readouterr().out
