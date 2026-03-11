import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import apps.planning.src.config  # Needed for reload
from apps.planning.src.config import Config

# We import the module to patch 'Flask' inside it before it executes


class TestConfigCoverage(unittest.TestCase):
    """Targeted tests to improve coverage of config.py logic branches."""

    def test_config_db_filename_logic(self):
        """Reload config module with different env vars to cover definition time
        logic."""

        # Branch 1: TESTING=1 -> :memory:
        with patch.dict(os.environ, {"TESTING": "1"}, clear=True):
            if "apps.planning.src.config" not in sys.modules:
                importlib.import_module("apps.planning.src.config")
            importlib.reload(apps.planning.src.config)
            # Access module attribute directly
            self.assertEqual(apps.planning.src.config.Config.DATABASE_PATH, ":memory:")

        # Branch 2: FLASK_DEBUG=1 -> planning_test.db
        with patch.dict(os.environ, {"TESTING": "0", "FLASK_DEBUG": "1"}, clear=True):
            if "apps.planning.src.config" not in sys.modules:
                importlib.import_module("apps.planning.src.config")
            importlib.reload(apps.planning.src.config)
            self.assertIn(
                "planning_test.db", apps.planning.src.config.Config.DATABASE_PATH
            )

        # Branch 3: Default -> planning.db (Reset to default)
        with patch.dict(os.environ, {"TESTING": "0", "FLASK_DEBUG": "0"}, clear=True):
            if "apps.planning.src.config" not in sys.modules:
                importlib.import_module("apps.planning.src.config")
            importlib.reload(apps.planning.src.config)
            self.assertIn("planning.db", apps.planning.src.config.Config.DATABASE_PATH)

    @patch("apps.planning.src.config.os.path.exists")
    def test_validate_config_production_db_missing(self, mock_exists):
        # Context manager to safely modify class attributes
        original_debug = Config.FLASK_DEBUG
        Config.FLASK_DEBUG = False
        Config.DATABASE_PATH = "/tmp/nonexistent/db.sqlite"
        mock_exists.return_value = False

        # Ensure we are not in testing mode
        with patch.dict(os.environ, {}, clear=True):
            # Manually reset the flags that config logic might have set
            # Note: Config class body has already run.
            # We are testing validate_config method logic.
            Config.DEBUG_USE_TEST_DB = False

            with self.assertRaises(ValueError) as cm:
                Config.validate_config()
            self.assertIn("Database directory does not exist", str(cm.exception))

        Config.FLASK_DEBUG = original_debug

    def test_get_fixed_datetime(self):
        Config.FLASK_DEBUG = False
        self.assertIsNone(Config.get_fixed_datetime())

        Config.FLASK_DEBUG = True
        Config.DEBUG_FIXED_DATE = None
        dt = Config.get_fixed_datetime()
        self.assertEqual(dt.year, 2025)

        Config.DEBUG_FIXED_DATE = "2099-01-01"
        dt = Config.get_fixed_datetime()
        self.assertEqual(dt.year, 2099)

        Config.DEBUG_FIXED_DATE = "invalid-date"
        dt = Config.get_fixed_datetime()
        self.assertEqual(dt.year, 2025)


class MockConfig(dict):
    """Mock Flask config that acts like a dict but supports from_mapping."""

    def from_mapping(self, *args, **kwargs):
        for arg in args:
            if arg:
                self.update(arg)
        self.update(kwargs)
        return True


class TestAppFactoryCoverage(unittest.TestCase):
    """Targeted tests for app.py factory logic using pure mocks."""

    @patch("src.app.Flask")
    @patch("src.app.Limiter")
    @patch("src.app.CSRFProtect")
    @patch("src.app.LoggingConfig")
    @patch("src.app.db")
    @patch("src.app._register_blueprints")
    @patch("src.app.os.makedirs")
    @patch("src.app.populate_dummy_data")
    def test_create_app_directory_creation_logic(
        self,
        mock_populate,
        mock_makedirs,
        mock_blueprints,
        mock_db,
        mock_logger,
        mock_csrf,
        mock_limiter,
        mock_flask_cls,
    ):
        """Test directory creation logic by mocking Flask entirely."""
        from src.app import create_app

        # Setup Mock App
        mock_app = MagicMock()
        mock_flask_cls.return_value = mock_app

        # Use helper class for config
        mock_app.config = MockConfig()

        # Test Case: File-based URI triggers makedirs
        with patch.dict(os.environ, {"TESTING": "0", "E2E_TEST": "0"}):
            create_app(
                {
                    "TESTING": False,
                    "SQLALCHEMY_DATABASE_URI": "sqlite:///D:/custom/path/db.sqlite",
                    "SQLALCHEMY_BINDS": {},
                }
            )

            # Verify makedirs logic
            mock_makedirs.assert_any_call("D:/custom/path", exist_ok=True)

    @patch("src.app.Flask")
    @patch("src.app.Limiter")
    @patch("src.app.CSRFProtect")
    @patch("src.app.LoggingConfig")
    @patch("src.app.db")
    @patch("src.app._register_blueprints")
    @patch("src.app.os.makedirs")
    @patch("src.app.populate_dummy_data")
    def test_create_app_testing_production(
        self,
        mock_populate,
        mock_makedirs,
        mock_blueprints,
        mock_db,
        mock_logger,
        mock_csrf,
        mock_limiter,
        mock_flask_cls,
    ):
        """Test create_app with TESTING_PRODUCTION env var."""
        from src.app import create_app

        # Setup Mock App
        mock_app = MagicMock()
        mock_flask_cls.return_value = mock_app
        mock_app.config = MockConfig()

        # Set TESTING_PRODUCTION
        with patch.dict(os.environ, {"TESTING_PRODUCTION": "1", "TESTING": "0"}):
            create_app()
            # Verify SQLALCHEMY_DATABASE_URI logic hit mockcmms_test.db
            # We can't verify local variable db_name easily, but verify final config
            uri = mock_app.config.get("SQLALCHEMY_DATABASE_URI")
            self.assertIn("mockcmms_test.db", uri)

    @patch("src.app.Flask")
    @patch("src.app.Limiter")
    @patch("src.app.CSRFProtect")
    @patch("src.app.LoggingConfig")
    @patch("src.app.db")
    @patch("src.app._register_blueprints")
    @patch("src.app.populate_dummy_data")
    @patch("src.app.sqlite3.connect")
    def test_before_planning_request_hook(
        self,
        mock_connect,
        mock_populate,
        mock_blueprints,
        mock_db,
        mock_logger,
        mock_csrf,
        mock_limiter,
        mock_flask_cls,
    ):
        """Test the request hook by capturing it from the mock app."""
        import src.app
        from src.app import create_app

        # Manual Monkeypatching to avoid unittest.mock inspection on LocalProxy
        original_request = src.app.request
        original_g = src.app.g

        # Monkeypatch os.path.exists manually to avoid signature issues
        # that plagued previous runs
        original_exists = src.app.os.path.exists

        mock_request = MagicMock()
        mock_g = MagicMock()
        mock_exists = MagicMock(return_value=True)

        src.app.request = mock_request
        src.app.g = mock_g
        src.app.os.path.exists = mock_exists

        try:
            # Setup Mock App
            mock_app = MagicMock()
            mock_flask_cls.return_value = mock_app

            # Use helper class for config
            mock_app.config = MockConfig({"SQLALCHEMY_BINDS": {}})

            # Run Factory
            create_app({"TESTING": True, "PLANNING_ENABLED": True})

            # Find the registered hook
            hook_func = None
            for call_args in mock_app.before_request.call_args_list:
                arg = call_args[0][0]  # The function passed to decorator
                if arg.__name__ == "before_planning_request":
                    hook_func = arg
                    break

            if not hook_func:
                self.fail("before_planning_request hook passed not registered properly")

            # --- Test the Hook Logic ---

            # Ensure path exists check passes
            mock_exists.return_value = True

            # Setup Context Mocks
            mock_request.path = "/planning/dashboard"

            # Scenario 1: File based DB (Explicit Path) -> connects
            mock_app.config["SQLALCHEMY_BINDS"][
                "planning"
            ] = "sqlite:///D:/mock/planning.db"
            mock_app.config["DATABASE_PATH"] = "D:/mock/planning.db"

            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            hook_func()

            mock_connect.assert_called()
            self.assertEqual(mock_g.db, mock_conn)
            mock_connect.reset_mock()

            # Scenario 2: In-memory DB -> no connect
            mock_app.config["SQLALCHEMY_BINDS"]["planning"] = "sqlite:///:memory:"

            hook_func()
            mock_connect.assert_not_called()
            mock_connect.reset_mock()

            # Scenario 3: Derived Path from URI (DATABASE_PATH missing)
            del mock_app.config["DATABASE_PATH"]
            mock_app.config["SQLALCHEMY_BINDS"][
                "planning"
            ] = "sqlite:///D:/derived/planning.db"

            hook_func()
            # Should connect to D:/derived/planning.db
            mock_connect.assert_called()
            # Verify call args?
            args, _ = mock_connect.call_args
            self.assertIn("planning.db", args[0])
            mock_connect.reset_mock()

            # Scenario 4: No URI, No Path (Defaults)
            mock_app.config["SQLALCHEMY_BINDS"]["planning"] = ""  # Or missing
            # And db_path missing from config
            # app.config.get("DATABASE_PATH") is None

            # Need to mock app.root_path properly for join
            mock_app.root_path = "D:/app/src"

            hook_func()
            mock_connect.assert_called()
            args, _ = mock_connect.call_args
            self.assertIn("planning_test.db", args[0])  # Because app.testing is True

        finally:
            # Restore original LocalProxies and functions
            src.app.request = original_request
            src.app.g = original_g
            src.app.os.path.exists = original_exists


if __name__ == "__main__":
    unittest.main()
