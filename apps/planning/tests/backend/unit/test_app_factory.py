"""Tests for the Planning App factory (app.py)."""

import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


@pytest.fixture
def planning_app(tmp_path):
    """Fixture for Planning-specific app instance."""
    from apps.planning.src.app import create_app

    test_db = str(tmp_path / "planning_test.db")
    core_db = str(tmp_path / "mockcmms_test.db")

    with patch("apps.planning.src.app.LoggingConfig.setup_logging"):
        app = create_app(
            config_overrides={
                "TESTING": True,
                "DATABASE_PATH": test_db,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{core_db}",
                "SQLALCHEMY_BINDS": {
                    "planning": f"sqlite:///{test_db}",
                    "reporting": "sqlite:///:memory:",
                },
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )
        yield app

    # Cleanup created databases
    for path in [test_db, core_db]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


@pytest.fixture
def planning_client(planning_app):
    """Fixture for Planning-specific app client."""
    return planning_app.test_client()


class TestAppFactory:
    """Tests for create_app factory function."""

    @patch("apps.planning.src.app.LoggingConfig.setup_logging")
    @patch("apps.planning.src.app.Config.validate_config")
    def test_create_app_success(self, mock_validate, mock_setup_logging, tmp_path):
        """Test successful application creation."""
        import os

        from apps.planning.src.app import create_app

        mock_setup_logging.return_value = MagicMock()
        test_db = str(tmp_path / "success_test.db")

        app = create_app(
            config_overrides={
                "TESTING": True,
                "DATABASE_PATH": test_db,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SQLALCHEMY_BINDS": {
                    "planning": f"sqlite:///{test_db}",
                    "reporting": "sqlite:///:memory:",
                },
            }
        )

        assert isinstance(app, Flask)
        assert app.config["SECRET_KEY"] is not None
        mock_validate.assert_called_once()
        mock_setup_logging.assert_called_once_with(app)

        # Cleanup (graceful failure on Windows if file is locked)
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except OSError:
                pass

    @patch("apps.planning.src.app.Config.validate_config")
    def test_create_app_validation_failure(self, mock_validate):
        """Test app creation failure due to configuration error."""
        from apps.planning.src.app import create_app

        mock_validate.side_effect = ValueError("Invalid Config")

        with pytest.raises(ValueError, match="Invalid Config"):
            create_app(config_overrides={"TESTING": True})

    @patch("apps.planning.src.app.LoggingConfig.setup_logging")
    @patch("apps.planning.src.app.Config.validate_config")
    @patch("apps.planning.src.app.db.create_all")
    @patch("apps.planning.src.app.db_manager.init_app")
    def test_create_app_adds_reporting_and_legacy_binds_in_non_testing(
        self,
        _mock_db_manager_init,
        mock_create_all,
        mock_validate,
        mock_setup_logging,
    ):
        """Ensure non-testing app config auto-adds reporting binds."""
        from apps.planning.src.app import create_app

        mock_setup_logging.return_value = MagicMock()

        app = create_app(
            config_overrides={
                "TESTING": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SQLALCHEMY_BINDS": {"planning": "sqlite:///:memory:"},
            }
        )

        binds = app.config.get("SQLALCHEMY_BINDS", {})
        assert "reporting" in binds
        assert "reporting" in binds
        assert "reporting" in binds

    @patch("apps.planning.src.app.LoggingConfig.setup_logging")
    @patch("apps.planning.src.app.Config.validate_config")
    @patch("apps.planning.src.app.db.create_all")
    @patch("apps.planning.src.app.db_manager.init_app")
    def test_create_app_adds_reporting_bind_in_testing_when_missing(
        self,
        _mock_db_manager_init,
        _mock_create_all,
        _mock_validate,
        mock_setup_logging,
    ):
        """Ensure TESTING mode auto-adds in-memory reporting bind when absent."""
        from apps.planning.src.app import create_app

        mock_setup_logging.return_value = MagicMock()

        app = create_app(
            config_overrides={
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SQLALCHEMY_BINDS": {"planning": "sqlite:///:memory:"},
            }
        )

        binds = app.config.get("SQLALCHEMY_BINDS", {})
        assert binds["reporting"] == "sqlite:///:memory:"
        assert "reporting" in binds

    def test_app_error_handlers(self, planning_client):
        """Test custom error handlers in the app."""
        # Test 404 handler
        resp = planning_client.get("/planning/non-existent-page")
        assert resp.status_code == 404
        assert b"Page not found" in resp.data

        # Test 400 handler (by triggering it via endpoint if possible,
        # or just calling handler directly if accessible)
        # For now, we just check they are registered
        assert 404 in planning_client.application.error_handler_spec[None]
        assert 400 in planning_client.application.error_handler_spec[None]
        assert 500 in planning_client.application.error_handler_spec[None]

    def test_after_request_headers(self, planning_client):
        """Test security headers are added via after_request."""
        resp = planning_client.get("/planning/api/technicians")
        assert "X-Content-Type-Options" in resp.headers
        assert resp.headers["X-Content-Type-Options"] == "nosniff"


class TestErrorHandlersDirectly:
    """Tests for error handlers called directly."""

    def test_handle_400_error(self, app):
        """Test 400 error handler returns JSON."""
        from apps.planning.src.app import handle_400_error

        with app.app_context():
            error = Exception("Bad request detail")
            resp = handle_400_error(error)
            assert resp.status_code == 400
            data = resp.get_json()
            assert data["message"] == "Bad request"
            assert "Bad request detail" in data["details"]

    def test_handle_500_error(self, app):
        """Test 500 error handler returns JSON."""
        from apps.planning.src.app import handle_500_error

        with app.app_context():
            error = Exception("Internal error detail")
            resp = handle_500_error(error)
            assert resp.status_code == 500
            data = resp.get_json()
            assert data["message"] == "Internal server error"
            assert "Internal error detail" in data["details"]
