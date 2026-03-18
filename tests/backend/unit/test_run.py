import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest


class TestRunEntry:
    """Test suite for the application entry point (run.py)."""

    def setup_method(self):
        """Ensure run module is not in sys.modules so it re-executes."""
        if "run" in sys.modules:
            del sys.modules["run"]

    def teardown_method(self):
        """Clean up run module from sys.modules."""
        if "run" in sys.modules:
            del sys.modules["run"]

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables and modules."""
        # Combine feature-specific patches with main branch structural patches
        with (
            patch.dict(
                os.environ,
                {"FLASK_RUN_PORT": "5000", "E2E_TEST": "False", "TESTING": "1"},
            ),
            patch("src.app.create_app") as mock_create_app,
            patch("src.app.Flask"),
            patch("dotenv.load_dotenv") as mock_load_dotenv,
            patch("os.path.exists") as mock_exists,
            # Feature-specific patches to prevent DB/Seeding side effects in unit tests
            patch("src.app.db.create_all"),
            patch("src.app.populate_dummy_data"),
            patch("apps.planning.src.services.db_seeding.seed_planning_data"),
            patch("src.app.os.makedirs"),
        ):
            # Setup successful environment check
            mock_exists.return_value = True

            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            yield {
                "create_app": mock_create_app,
                "app": mock_app,
                "load_dotenv": mock_load_dotenv,
                "exists": mock_exists,
            }

    def test_run_app_import(self, mock_env):
        """Test that run.py imports and initializes the app correctly."""
        import importlib

        import run

        importlib.reload(run)

        mock_env["load_dotenv"].assert_called()
        # In testing mode, app is None and create_app is NOT called at import
        assert run.app is None

        # Patch create_app in run module's namespace AFTER reload
        with patch.object(run, "create_app", mock_env["create_app"]):
            # Reset _app to force get_app() to call create_app
            run._app = None
            run.get_app()
            mock_env["create_app"].assert_called()

    def test_run_app_setup_missing(self):
        """Test that run.py exits if setup is missing."""
        # Ensure CI/E2E_TEST env vars are NOT set, but TESTING=1 to prevent DB creation
        with (
            patch.dict(os.environ, {"TESTING": "1"}, clear=True),
            patch("os.path.exists", return_value=False),
            patch("sys.exit") as mock_exit,
            patch("dotenv.load_dotenv"),
            patch("src.app.create_app") as mock_create_app,
        ):
            mock_create_app.return_value = MagicMock()
            # In some versions it might be in sys.modules from other tests
            import importlib

            import run

            importlib.reload(run)

            run.check_setup()
            mock_exit.assert_called_with(1)

    def test_run_app_setup_bypass_ci(self):
        """Test that setup check is skipped in CI environment."""
        with (
            patch.dict(os.environ, {"CI": "true", "TESTING": "1"}, clear=True),
            patch("os.path.exists", return_value=False),
            patch("sys.exit") as mock_exit,
            patch("dotenv.load_dotenv"),
            patch("src.app.create_app") as mock_create_app,
        ):
            mock_create_app.return_value = MagicMock()
            import importlib

            import run

            importlib.reload(run)

            run.check_setup()
            mock_exit.assert_not_called()

    def test_run_app_config(self, mock_env):
        """Test that the app from run.py has expected configuration."""
        import importlib

        import run

        importlib.reload(run)
        # With lazy initialization, get_app() returns the mocked app
        assert run.get_app() is mock_env["app"]


class TestRunRobust:
    """Robust tests for run.py covering various configurations and edge cases."""

    def setup_method(self):
        """Ensure run module is not in sys.modules so it re-executes."""
        if "run" in sys.modules:
            del sys.modules["run"]

    def teardown_method(self):
        """Clean up run module from sys.modules."""
        if "run" in sys.modules:
            del sys.modules["run"]

    @pytest.fixture
    def base_patches(self):
        """Common patches for robust run tests."""
        with (
            patch("src.app.create_app"),
            patch("src.app.Flask"),
            patch("dotenv.load_dotenv"),
            patch("os.path.exists", return_value=True),
            patch("src.app.db.create_all"),
            patch("src.app.populate_dummy_data"),
            patch("src.app.os.makedirs"),
            patch("urllib.request.urlopen"),
            patch("webbrowser.open"),
            patch("threading.Thread") as mock_thread,
            patch("builtins.open", mock_open()),
        ):
            yield {"thread": mock_thread}

    def test_portable_detection_variations(self, base_patches):
        """Test that is_portable correctly detects various env var values."""
        # Test truthy values
        for val in ["true", "1", "yes", "TRUE", "Yes"]:
            with patch.dict(os.environ, {"PORTABLE_DISTRIBUTION": val}):
                if "run" in sys.modules:
                    del sys.modules["run"]
                import run

                assert run.is_portable is True

        # Test falsy values
        for val in ["false", "0", "no", "", "None"]:
            with patch.dict(os.environ, {"PORTABLE_DISTRIBUTION": val}):
                if "run" in sys.modules:
                    del sys.modules["run"]
                import run

                assert run.is_portable is False

    def test_utf8_reconfigure_failure(self, base_patches):
        """Test that UTF-8 reconfiguration handles failures gracefully."""
        mock_stdout = MagicMock()
        mock_stdout.reconfigure.side_effect = ValueError("Mock failure")

        with (
            patch.object(sys, "platform", "win32"),
            patch.object(sys, "stdout", mock_stdout),
        ):
            if "run" in sys.modules:
                del sys.modules["run"]
            import run

            # Should not raise exception
            assert run.script_dir is not None

    def test_portable_startup_sequence_success(self, base_patches):
        """Test the portable startup sequence when server becomes ready."""
        if "run" in sys.modules:
            del sys.modules["run"]
        import run

        # Mock urlopen to succeed immediately
        with (
            patch("urllib.request.urlopen") as mock_url,
            patch("webbrowser.open") as mock_browser,
            patch("time.sleep"),
        ):
            run._portable_startup_sequence()

            mock_url.assert_called()
            mock_browser.assert_called_with(
                "http://127.0.0.1:5000", new=0, autoraise=True
            )

    def test_check_setup_exit_cases(self, base_patches):
        """Test check_setup logic more deeply."""
        import importlib

        import run

        # Case 1: In E2E_TEST -> bypasses
        with (
            patch.dict(os.environ, {"E2E_TEST": "true"}),
            patch("sys.exit") as mock_exit,
        ):
            importlib.reload(run)
            run.check_setup()
            mock_exit.assert_not_called()

        # Case 2: Not in CI/E2E/Portable, .venv exists -> passes
        with (
            patch.dict(
                os.environ,
                {
                    "CI": "",
                    "E2E_TEST": "false",
                    "PORTABLE_DISTRIBUTION": "false",
                },
            ),
            patch("os.path.exists", return_value=True),
            patch("sys.exit") as mock_exit,
        ):
            importlib.reload(run)
            # Manually force False just in case reload missed something
            run.is_portable = False
            run.check_setup()
            mock_exit.assert_not_called()

        # Case 3: Not in CI/E2E/Portable, .venv MISSING -> exits
        with (
            patch.dict(
                os.environ,
                {"CI": "", "E2E_TEST": "", "PORTABLE_DISTRIBUTION": "false"},
            ),
            patch("os.path.exists", return_value=False),
            patch("sys.exit") as mock_exit,
        ):
            importlib.reload(run)
            run.is_portable = False
            run.check_setup()
            mock_exit.assert_called_with(1)

    def test_get_app_debug_logic(self, base_patches):
        """Test debug mode logic in get_app()."""
        import importlib

        import run

        with patch("src.app.create_app") as mock_create:
            # Case 1: Portable -> debug False
            with patch.dict(os.environ, {"PORTABLE_DISTRIBUTION": "true"}):
                importlib.reload(run)
                run._app = None
                run.get_app()
                mock_create.assert_called_with(config_overrides={"DEBUG": False})

            # Case 2: Development -> debug True
            with patch.dict(
                os.environ, {"FLASK_DEBUG": "1", "PORTABLE_DISTRIBUTION": "false"}
            ):
                importlib.reload(run)
                run._app = None
                run.get_app()
                mock_create.assert_called_with(config_overrides={"DEBUG": True})
