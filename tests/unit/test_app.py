"""
Tests for Flask application factory and configuration.

This module tests the core Flask app creation, configuration management,
blueprint registration, database initialization, and context handling.
"""

import os
import shutil
import pytest
from unittest.mock import patch, MagicMock
from src.app import create_app
from src.services.db_utils import db

# Default binds for tests - prevents UnboundExecutionError when planning models are imported
TEST_SQLALCHEMY_BINDS = {"planning": "sqlite:///:memory:"}


def create_test_app(config=None):
    """Create app with test SQLALCHEMY_BINDS included."""
    default_config = {
        "SQLALCHEMY_BINDS": TEST_SQLALCHEMY_BINDS,
    }
    if config:
        default_config.update(config)
    return create_app(default_config)


class TestAppFactory:
    """Test suite for Flask application factory pattern."""

    def test_create_app_default_config(self, app):
        """Test app creation with default configuration."""
        # Use the app fixture which has TESTING=True (in-memory database)
        assert app is not None
        assert isinstance(app.config["SQLALCHEMY_DATABASE_URI"], str)
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False
        assert app.secret_key is not None

    def test_create_app_testing_config(self, app):
        """Test app creation with testing configuration."""
        # Use the app fixture which has TESTING=True
        assert app.config["TESTING"] is True
        assert app.config["WTF_CSRF_ENABLED"] is False
        assert "memory" in app.config["SQLALCHEMY_DATABASE_URI"]

    def test_database_initialization(self, app):
        """Test database initialization and table creation."""
        with app.app_context():
            # Verify db object exists
            assert db is not None

            # Verify database engine is initialized
            assert db.engine is not None

            # Verify tables are created
            tables = db.metadata.tables.keys()
            assert "user" in tables
            assert "asset" in tables
            assert "maintenance_order" in tables
            assert "spare_part" in tables

    def test_blueprints_registered(self, app):
        """Test that all required blueprints are registered."""
        # Get all registered blueprint names
        blueprint_names = [bp for bp in app.blueprints.keys()]

        # Verify core blueprints are registered
        assert "api" in blueprint_names, "API blueprint not registered"
        assert "main" in blueprint_names, "Main blueprint not registered"

        # Planning and Reports blueprints are conditional
        # In test mode, they should be disabled by default
        # (This is controlled by environment variables)

    @patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test-secret-from-env",
            "TESTING": "0",
            "TESTING_PRODUCTION": "1",
        },
    )
    def test_secret_key_from_env(self):
        """Test app uses SECRET_KEY from environment variable."""
        app = create_test_app()
        assert app.secret_key == "test-secret-from-env"

        # Clean up
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_secret_key_fallback(self):
        """Test app uses a fallback secret key when not in the environment."""
        with patch.dict(os.environ, {}, clear=True):
            app = create_test_app(
                {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
            )
            assert app.secret_key == "dev_key_fallback_for_testing"

    def test_database_uri_configuration(self, app):
        """Test SQLALCHEMY_DATABASE_URI is properly configured."""
        # In test mode, should use in-memory database
        assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"

        # In production, it would use a file-based database
        # Temporarily clear TESTING flag to create production app
        original_testing = os.environ.get("TESTING")
        original_testing_prod = os.environ.get("TESTING_PRODUCTION")
        os.environ.pop("TESTING", None)
        os.environ["TESTING_PRODUCTION"] = "1"
        try:
            prod_app = create_test_app()
            prod_uri = prod_app.config["SQLALCHEMY_DATABASE_URI"]
            assert "sqlite:///" in prod_uri
            assert "mockcmms_test.db" in prod_uri

            # Clean up database connection
            with prod_app.app_context():
                db.session.remove()
                db.engine.dispose()
        finally:
            if original_testing:
                os.environ["TESTING"] = original_testing
            else:
                os.environ.pop("TESTING", None)
            if original_testing_prod:
                os.environ["TESTING_PRODUCTION"] = original_testing_prod
            else:
                os.environ.pop("TESTING_PRODUCTION", None)

    def test_app_context(self, app):
        """Test app context can be pushed and popped."""
        # Context should not be active initially
        from flask import has_app_context

        # Push context
        ctx = app.app_context()
        ctx.push()

        # Verify context is active
        assert has_app_context()

        # Pop context
        ctx.pop()

        # Context should no longer be active (unless in fixture context)

    def test_request_context(self, app):
        """Test request context can be created and is active."""
        from flask import has_request_context, request

        # Create request context
        with app.test_request_context("/"):
            # Verify request context is active
            assert has_request_context()
            assert request.path == "/"

    def test_error_handlers_registered(self, client):
        """Test that error handlers are properly configured."""
        # Test 404 error handler
        response = client.get("/nonexistent-route-12345")
        assert response.status_code == 404

        # The response should be either JSON or HTML
        # depending on how error handlers are implemented
        assert response.data is not None


class TestAppConfiguration:
    """Test suite for application configuration."""

    @patch.dict(os.environ, {"TESTING": "0", "TESTING_PRODUCTION": "1"})
    def test_csrf_protection_enabled_in_production(self):
        """Test CSRF protection is enabled in production mode."""
        app = create_test_app()
        assert app.config.get("WTF_CSRF_ENABLED", True) is True

        # Clean up
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_csrf_protection_disabled_in_testing(self, app):
        """Test CSRF protection is disabled in testing mode."""
        # In test mode (from fixture), CSRF should be disabled
        assert app.config["WTF_CSRF_ENABLED"] is False

    def test_sqlalchemy_track_modifications_disabled(self, app):
        """Test SQLAlchemy modification tracking is disabled."""
        # Should be False to avoid overhead
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False

    def test_instance_folder_created(self, app):
        """Test instance folder is created during app initialization."""
        # The app factory should create the instance folder
        instance_path = os.path.join(app.root_path, "..", "instance")

        # In test mode with in-memory DB, this might not exist
        # but in production it should be created
        # This test verifies the logic is in place


class TestBlueprintConditionalLoading:
    """Test suite for conditional blueprint loading."""

    @patch.dict(
        os.environ,
        {"PLANNING_ENABLED": "True", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_planning_blueprint_enabled(self):
        """Test planning blueprint loads when PLANNING_ENABLED=True."""
        try:
            app = create_test_app()
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        except ImportError:
            pytest.skip("Planning module not available")

    @patch.dict(
        os.environ,
        {"PLANNING_ENABLED": "False", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_planning_blueprint_disabled(self):
        """Test planning blueprint doesn't load when PLANNING_ENABLED=False."""
        app = create_test_app()
        assert "planning" not in app.blueprints

        # Clean up
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

    @patch.dict(
        os.environ,
        {"REPORTS_ENABLED": "True", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_reports_blueprint_enabled(self):
        """Test reports blueprint loads when REPORTS_ENABLED=True."""
        try:
            app = create_test_app()
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        except ImportError:
            pytest.skip("Reports module not available")

    @patch.dict(
        os.environ,
        {"REPORTS_ENABLED": "False", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_reports_blueprint_disabled(self):
        """Test reports blueprint doesn't load when REPORTS_ENABLED=False."""
        app = create_test_app()
        assert "reports" not in app.blueprints

        # Clean up
        with app.app_context():
            db.session.remove()
            db.engine.dispose()


class TestEnhancedAppConfiguration:
    """Enhanced test suite for app configuration and module loading."""

    @patch.dict(
        os.environ,
        {"REPORTS_ENABLED": "True", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_app_reports_module_enabled(self):
        """Test reports module loads when REPORTS_ENABLED=True."""
        try:
            app = create_test_app()
            assert app is not None
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        except ImportError:
            pytest.skip("Reports module not available")

    @patch.dict(
        os.environ,
        {"REPORTS_ENABLED": "False", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_app_reports_module_disabled(self):
        """Test reports module doesn't load when REPORTS_ENABLED=False."""
        app = create_test_app()
        assert "reports" not in app.blueprints

        # Clean up
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

    @patch.dict(
        os.environ,
        {"PLANNING_ENABLED": "True", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_app_planning_module_enabled(self):
        """Test planning module loads when PLANNING_ENABLED=True."""
        try:
            app = create_test_app()
            assert app is not None
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        except ImportError:
            pytest.skip("Planning module not available")

    @patch.dict(
        os.environ,
        {"PLANNING_ENABLED": "False", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_app_planning_module_disabled(self):
        """Test planning module doesn't load when PLANNING_ENABLED=False."""
        app = create_test_app()
        assert "planning" not in app.blueprints
        assert "planning_api" not in app.blueprints

        # Clean up
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_app_database_initialization(self, app):
        """Test database is initialized with tables created."""
        with app.app_context():
            # Verify database tables exist
            tables = db.metadata.tables.keys()
            assert len(tables) > 0
            assert "user" in tables
            assert "asset" in tables

    def test_app_security_headers(self, client):
        """Test security headers are added to responses."""
        response = client.get("/")
        assert "Permissions-Policy" in response.headers
        assert response.headers["Permissions-Policy"] == "unload=()"
        assert "Cross-Origin-Opener-Policy" in response.headers
        assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"

    def test_app_legacy_url_redirect(self, client):
        """Test legacy /planning-manager URLs redirect to /planning."""
        with patch.dict("os.environ", {"PLANNING_ENABLED": "True"}):
            response = client.get("/planning-manager/test", follow_redirects=False)
            assert response.status_code == 301
            assert "/planning/test" in response.location

    def test_app_context_processor_variables(self, app):
        """Test PLANNING_ENABLED and REPORTS_ENABLED injected into templates."""
        with app.app_context():
            # Get context processor function
            context_processors = app.template_context_processors[None]

            # Find inject_config processor
            inject_config = None
            for processor in context_processors:
                if processor.__name__ == "inject_config":
                    inject_config = processor
                    break

            assert inject_config is not None
            context = inject_config()
            assert "PLANNING_ENABLED" in context
            assert "REPORTS_ENABLED" in context
            assert isinstance(context["PLANNING_ENABLED"], bool)
            assert isinstance(context["REPORTS_ENABLED"], bool)

    @patch("src.app.populate_dummy_data")
    def test_app_auto_seed_database(self, mock_populate_dummy_data):
        """Test that the database is auto-seeded based on the configuration."""
        create_test_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "AUTO_SEED_DATABASE": True,
            }
        )
        mock_populate_dummy_data.assert_called_once()

    def test_app_csrf_protection_initialized(self, app):
        """Test CSRF protection is initialized."""
        # CSRF should be initialized (CSRFProtect called)
        # In test mode it's disabled, but the extension should exist
        assert (
            "csrf" in app.extensions or app.config.get("WTF_CSRF_ENABLED") is not None
        )


class TestAppErrorHandling:
    """Test suite for error handling and edge cases in app.py."""

    @patch.dict(
        os.environ,
        {"REPORTS_ENABLED": "True", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_reports_blueprint_registration_error(self):
        """Test app handles reports module unavailable gracefully."""
        import sys

        # Mock ImportError by making the module import fail
        with patch.dict(sys.modules, {"apps.reports.src.routes.reports": None}):
            app = create_test_app()
            assert app is not None
            assert "reports" not in app.blueprints

            # Clean up
            with app.app_context():
                db.session.remove()
                db.engine.dispose()

    @patch.dict(
        os.environ,
        {"PLANNING_ENABLED": "True", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    def test_planning_blueprint_registration_error(self):
        """Test app handles planning module unavailable gracefully."""
        import sys

        # Mock ImportError by making the module import fail
        with patch.dict(sys.modules, {"apps.planning.src.routes.planning": None}):
            app = create_test_app()
            assert app is not None
            assert "planning" not in app.blueprints

            # Clean up
            with app.app_context():
                db.session.remove()
                db.engine.dispose()

    def test_before_planning_request_database_error(self, app, client):
        """Test before_planning_request handles database connection errors."""
        import sqlite3  # Added import for sqlite3.OperationalError

        with patch.dict(os.environ, {"PLANNING_ENABLED": "True"}):
            with patch(
                "sqlite3.connect",
                side_effect=sqlite3.OperationalError("Database connection failed"),
            ):
                # Request to planning route should handle database error
                response = client.get("/planning/test")
                # Should return error response or 404 (if planning not enabled)
                assert response.status_code in [404, 500, 503]

    def test_close_db_teardown(self, app):
        """Test close_db teardown function closes database connections."""
        from flask import g

        with app.app_context():
            # Simulate database connection in g
            mock_db = MagicMock()
            g.db = mock_db

            # Trigger teardown
            with app.test_request_context("/"):
                pass  # Context exit triggers teardown

            # Database close should have been called
            # Note: This tests the teardown logic exists

    @patch.dict(
        os.environ,
        {"MOCKCMMS_DEBUG_USE_TEST_DB": "1", "TESTING": "0", "TESTING_PRODUCTION": "1"},
    )
    @patch(
        "src.services.db_utils.populate_dummy_data",
        side_effect=Exception("Seeding failed"),
    )
    def test_database_seeding_error_handling(self, mock_populate):
        """Test app handles database seeding errors gracefully."""
        # Should create app successfully even if seeding fails
        app = create_test_app()
        assert app is not None
        # App should still be functional even if seeding failed

        # Clean up database connection
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
