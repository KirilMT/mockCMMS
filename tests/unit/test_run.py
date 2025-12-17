"""
Test run.py application entry point.
"""

import sys
from unittest.mock import patch


class TestRunEntry:
    """Test the application entry point."""

    def setup_method(self):
        """Ensure run module is not in sys.modules so it re-executes."""
        if "run" in sys.modules:
            del sys.modules["run"]

    def teardown_method(self):
        """Clean up run module from sys.modules."""
        if "run" in sys.modules:
            del sys.modules["run"]

    def test_run_app_import(self):
        """Test that run.py can be imported and app is created."""
        # Patch db.create_all to prevent database creation side effects
        # Patch populate_dummy_data to prevent DB access when tables don't exist
        # Patch load_dotenv to prevent environment side effects
        with (
            patch("src.app.db.create_all"),
            patch("src.app.populate_dummy_data"),
            patch("dotenv.load_dotenv"),
        ):
            import run

            assert run.app is not None
            assert run.app.name == "src.app"

    def test_run_app_config(self):
        """Test that the app from run.py has expected configuration."""
        with (
            patch("src.app.db.create_all"),
            patch("src.app.populate_dummy_data"),
            patch("dotenv.load_dotenv"),
        ):
            import run

            assert run.app.config is not None
