import os
import sys
from unittest.mock import MagicMock, patch

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
            patch("apps.planning.src.services.seeding.seed_planning_data"),
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
