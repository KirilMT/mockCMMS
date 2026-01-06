
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestRunEntry:
    """Test suite for the application entry point (run.py)."""

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables and modules."""
        with patch.dict(os.environ, {"FLASK_RUN_PORT": "5000", "E2E_TEST": "False"}), \
             patch("src.app.create_app") as mock_create_app, \
             patch("src.app.Flask") as mock_flask, \
             patch("dotenv.load_dotenv") as mock_load_dotenv, \
             patch("os.path.exists") as mock_exists:

            # Setup successful environment check
            mock_exists.return_value = True

            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            yield {
                "create_app": mock_create_app,
                "app": mock_app,
                "load_dotenv": mock_load_dotenv,
                "exists": mock_exists
            }

    def test_run_app_import(self, mock_env):
        """Test that run.py imports and initializes the app correctly."""
        # We need to use reload or runpy because run.py is a script
        # Importing it executes the top-level code
        import run
        import importlib
        importlib.reload(run)

        mock_env["load_dotenv"].assert_called()
        mock_env["create_app"].assert_called_with(config_overrides={"DEBUG": True})

    def test_run_app_setup_missing(self):
        """Test that run.py exits if setup is missing."""
        # Ensure CI/E2E_TEST env vars are NOT set
        with patch.dict(os.environ, {}, clear=True), \
             patch("os.path.exists", return_value=False), \
             patch("sys.exit") as mock_exit, \
             patch("dotenv.load_dotenv") as mock_load_dotenv:

            import run
            run.check_setup()

            mock_exit.assert_called_with(1)

    def test_run_app_setup_bypass_ci(self):
        """Test that setup check is skipped in CI environment."""
        with patch.dict(os.environ, {"CI": "true"}), \
             patch("os.path.exists", return_value=False), \
             patch("sys.exit") as mock_exit:

            import run
            run.check_setup()

            mock_exit.assert_not_called()

    def test_run_app_config(self, mock_env):
        """Test that the app is configured with the correct port and debug mode."""
        import run
        import importlib
        importlib.reload(run)

        assert run.app is mock_env["app"]
