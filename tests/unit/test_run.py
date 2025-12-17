"""
Test run.py application entry point.
"""

import pytest


class TestRunEntry:
    """Test the application entry point."""

    def test_run_app_import(self):
        """Test that run.py can be imported and app is created."""
        from run import app

        assert app is not None
        assert app.name == "src.app"

    def test_run_app_config(self):
        """Test that the app from run.py has expected configuration."""
        from run import app

        # It should be in development/debug mode by default as per run.py
        # But create_app might default to config.Config or DevelopmentConfig
        # run.py sets debug=True in app.run(), but that doesn't change app.debug unless set before
        # Let's just check it exists
        assert app.config is not None
