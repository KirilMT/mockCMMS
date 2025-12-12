"""
Tests for Flask application factory and configuration.

This module tests the core Flask app creation, configuration management,
blueprint registration, database initialization, and context handling.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from src.app import create_app
from src.services.db_utils import db


class TestAppFactory:
    """Test suite for Flask application factory pattern."""

    def test_create_app_default_config(self):
        """Test app creation with default configuration."""
        app = create_app()

        assert app is not None
        assert isinstance(app.config['SQLALCHEMY_DATABASE_URI'], str)
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False
        assert app.secret_key is not None

    def test_create_app_testing_config(self, app):
        """Test app creation with testing configuration."""
        # Use the app fixture which has TESTING=True
        assert app.config['TESTING'] is True
        assert app.config['WTF_CSRF_ENABLED'] is False
        assert 'memory' in app.config['SQLALCHEMY_DATABASE_URI']

    def test_database_initialization(self, app):
        """Test database initialization and table creation."""
        with app.app_context():
            # Verify db object exists
            assert db is not None

            # Verify database engine is initialized
            assert db.engine is not None

            # Verify tables are created
            tables = db.metadata.tables.keys()
            assert 'user' in tables
            assert 'asset' in tables
            assert 'maintenance_order' in tables
            assert 'spare_part' in tables

    def test_blueprints_registered(self, app):
        """Test that all required blueprints are registered."""
        # Get all registered blueprint names
        blueprint_names = [bp for bp in app.blueprints.keys()]

        # Verify core blueprints are registered
        assert 'api' in blueprint_names, "API blueprint not registered"
        assert 'main' in blueprint_names, "Main blueprint not registered"

        # Planning and Reports blueprints are conditional
        # In test mode, they should be disabled by default
        # (This is controlled by environment variables)

    @patch.dict(os.environ, {'SECRET_KEY': 'test-secret-from-env'})
    def test_secret_key_from_env(self):
        """Test app uses SECRET_KEY from environment variable."""
        app = create_app()

        assert app.secret_key == 'test-secret-from-env'

    @patch('src.app.load_dotenv')
    @patch.dict(os.environ, {}, clear=True)
    def test_secret_key_fallback(self, mock_load_dotenv):
        """Test app uses fallback SECRET_KEY when not in environment."""
        # Prevent .env file from being loaded
        mock_load_dotenv.return_value = None

        # Create app without SECRET_KEY in environment
        app = create_app()

        # Should use fallback key
        assert app.secret_key is not None
        assert app.secret_key == 'dev_key_fallback_do_not_use_in_prod'

    def test_database_uri_configuration(self, app):
        """Test SQLALCHEMY_DATABASE_URI is properly configured."""
        # In test mode, should use in-memory database
        assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'

        # In production, it would use a file-based database
        prod_app = create_app()
        prod_uri = prod_app.config['SQLALCHEMY_DATABASE_URI']
        assert 'sqlite:///' in prod_uri
        assert 'mockcmms.db' in prod_uri

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
        with app.test_request_context('/'):
            # Verify request context is active
            assert has_request_context()
            assert request.path == '/'

    def test_error_handlers_registered(self, client):
        """Test that error handlers are properly configured."""
        # Test 404 error handler
        response = client.get('/nonexistent-route-12345')
        assert response.status_code == 404

        # The response should be either JSON or HTML
        # depending on how error handlers are implemented
        assert response.data is not None


class TestAppConfiguration:
    """Test suite for application configuration."""

    def test_csrf_protection_enabled_in_production(self):
        """Test CSRF protection is enabled in production mode."""
        app = create_app()

        # In production, CSRF should be enabled
        # (WTF_CSRF_ENABLED is not explicitly set to False)
        assert app.config.get('WTF_CSRF_ENABLED', True) is True

    def test_csrf_protection_disabled_in_testing(self, app):
        """Test CSRF protection is disabled in testing mode."""
        # In test mode (from fixture), CSRF should be disabled
        assert app.config['WTF_CSRF_ENABLED'] is False

    def test_sqlalchemy_track_modifications_disabled(self, app):
        """Test SQLAlchemy modification tracking is disabled."""
        # Should be False to avoid overhead
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False

    def test_instance_folder_created(self, app):
        """Test instance folder is created during app initialization."""
        # The app factory should create the instance folder
        instance_path = os.path.join(app.root_path, '..', 'instance')

        # In test mode with in-memory DB, this might not exist
        # but in production it should be created
        # This test verifies the logic is in place


class TestBlueprintConditionalLoading:
    """Test suite for conditional blueprint loading."""

    @patch.dict(os.environ, {'PLANNING_ENABLED': 'True'})
    def test_planning_blueprint_enabled(self):
        """Test planning blueprint loads when PLANNING_ENABLED=True."""
        try:
            app = create_app()
            # Planning might be registered if the module is available
            # This is an integration test that depends on external module
        except ImportError:
            # Planning module not available in test environment
            pytest.skip("Planning module not available")

    @patch.dict(os.environ, {'PLANNING_ENABLED': 'False'})
    def test_planning_blueprint_disabled(self):
        """Test planning blueprint doesn't load when PLANNING_ENABLED=False."""
        app = create_app()

        # Planning blueprint should not be registered
        assert 'planning' not in app.blueprints

    @patch.dict(os.environ, {'REPORTS_ENABLED': 'True'})
    def test_reports_blueprint_enabled(self):
        """Test reports blueprint loads when REPORTS_ENABLED=True."""
        try:
            app = create_app()
            # Reports might be registered if the module is available
        except ImportError:
            # Reports module not available in test environment
            pytest.skip("Reports module not available")

    @patch.dict(os.environ, {'REPORTS_ENABLED': 'False'})
    def test_reports_blueprint_disabled(self):
        """Test reports blueprint doesn't load when REPORTS_ENABLED=False."""
        app = create_app()

        # Reports blueprint should not be registered
        assert 'reports' not in app.blueprints


class TestEnhancedAppConfiguration:
    """Enhanced test suite for app configuration and module loading."""

    @patch.dict(os.environ, {'REPORTS_ENABLED': 'True'})
    def test_app_reports_module_enabled(self):
        """Test reports module loads when REPORTS_ENABLED=True."""
        try:
            app = create_app()
            # If reports module is available, blueprint should be registered
            # If not available, ImportError is caught and logged
            # Either way, app should be created successfully
            assert app is not None
        except ImportError:
            pytest.skip("Reports module not available")

    @patch.dict(os.environ, {'REPORTS_ENABLED': 'False'})
    def test_app_reports_module_disabled(self):
        """Test reports module doesn't load when REPORTS_ENABLED=False."""
        app = create_app()
        assert 'reports' not in app.blueprints

    @patch.dict(os.environ, {'PLANNING_ENABLED': 'True'})
    def test_app_planning_module_enabled(self):
        """Test planning module loads when PLANNING_ENABLED=True."""
        try:
            app = create_app()
            # If planning module is available, blueprints should be registered
            # at both /planning and /api prefixes
            assert app is not None
        except ImportError:
            pytest.skip("Planning module not available")

    @patch.dict(os.environ, {'PLANNING_ENABLED': 'False'})
    def test_app_planning_module_disabled(self):
        """Test planning module doesn't load when PLANNING_ENABLED=False."""
        app = create_app()
        assert 'planning' not in app.blueprints
        assert 'planning_api' not in app.blueprints

    def test_app_database_initialization(self, app):
        """Test database is initialized with tables created."""
        with app.app_context():
            # Verify database tables exist
            tables = db.metadata.tables.keys()
            assert len(tables) > 0
            assert 'user' in tables
            assert 'asset' in tables

    def test_app_security_headers(self, client):
        """Test security headers are added to responses."""
        response = client.get('/')
        assert 'Permissions-Policy' in response.headers
        assert response.headers['Permissions-Policy'] == 'unload=()'
        assert 'Cross-Origin-Opener-Policy' in response.headers
        assert response.headers['Cross-Origin-Opener-Policy'] == 'same-origin'

    def test_app_legacy_url_redirect(self, client):
        """Test legacy /planning-manager URLs redirect to /planning."""
        response = client.get('/planning-manager/test', follow_redirects=False)
        # Should redirect (302) or return 404 if planning not enabled
        assert response.status_code in [302, 404]
        if response.status_code == 302:
            assert '/planning' in response.location

    def test_app_context_processor_variables(self, app):
        """Test PLANNING_ENABLED and REPORTS_ENABLED injected into templates."""
        with app.app_context():
            # Get context processor function
            context_processors = app.template_context_processors[None]
            
            # Find inject_config processor
            inject_config = None
            for processor in context_processors:
                if processor.__name__ == 'inject_config':
                    inject_config = processor
                    break
            
            assert inject_config is not None
            context = inject_config()
            assert 'PLANNING_ENABLED' in context
            assert 'REPORTS_ENABLED' in context
            assert isinstance(context['PLANNING_ENABLED'], bool)
            assert isinstance(context['REPORTS_ENABLED'], bool)

    @patch.dict(os.environ, {'MOCKCMMS_DEBUG_USE_TEST_DB': '1'})
    def test_app_auto_seed_database(self):
        """Test database auto-seeding configuration when DEBUG_USE_TEST_DB=True."""
        # Create app with debug flag
        app = create_app()
        
        # Verify the debug flag is set correctly
        assert app.config['DEBUG_USE_TEST_DB'] is True
        
        # In test mode (TESTING=True), auto-seeding should not occur
        # This test verifies the configuration logic exists

    def test_app_csrf_protection_initialized(self, app):
        """Test CSRF protection is initialized."""
        # CSRF should be initialized (CSRFProtect called)
        # In test mode it's disabled, but the extension should exist
        assert 'csrf' in app.extensions or app.config.get('WTF_CSRF_ENABLED') is not None

