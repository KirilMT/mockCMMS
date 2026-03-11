"""Tests for planning app core modules."""

from unittest.mock import MagicMock, patch


class TestPlanningAppConfig:
    """Tests for apps/planning/src/services/config.py."""

    def test_config_singleton(self):
        """Test Config is a singleton."""
        from apps.planning.src.services.config import Config

        c1 = Config()
        c2 = Config()
        assert c1 is c2

    def test_config_validation_error(self):
        """Test ConfigValidationError can be raised."""
        from apps.planning.src.services.config import ConfigValidationError

        try:
            raise ConfigValidationError("Test error")
        except ConfigValidationError as e:
            assert "Test error" in str(e)

    def test_get_ticket_url(self):
        """Test ticket URL generation."""
        from apps.planning.src.services.config import Config

        c = Config()
        url = c.get_ticket_url(123)
        assert "123" in url

    def test_get_maintenance_grid_url(self):
        """Test maintenance grid URL generation."""
        from apps.planning.src.services.config import Config

        c = Config()
        url = c.get_maintenance_grid_url(status="NEW")
        assert "status=NEW" in url

    def test_get_system_name(self):
        """Test system name retrieval."""
        from apps.planning.src.services.config import Config

        c = Config()
        name = c.get_system_name()
        assert isinstance(name, str)

    @patch("apps.planning.src.config.Config.FLASK_DEBUG", False)
    def test_get_fixed_datetime_none(self):
        """Test fixed datetime returns None when not in debug mode."""
        from apps.planning.src.config import Config

        result = Config.get_fixed_datetime()
        # With FLASK_DEBUG=False, should always be None
        assert result is None


class TestTemplateFilters:
    """Tests for template filters."""

    def test_register_filters(self, app):
        """Test that filters are registered."""
        from apps.planning.src.template_filters import register_template_filters

        # Use the app fixture
        register_template_filters(app)
        # Check filters are registered
        assert "system_name" in app.jinja_env.filters
        assert "maintenance_url" in app.jinja_env.filters

    def test_system_name_filter(self, app):
        """Test system_name filter returns a string."""
        from apps.planning.src.template_filters import register_template_filters

        register_template_filters(app)
        # Get the filter function
        filter_func = app.jinja_env.filters["system_name"]
        result = filter_func(None)  # Pass dummy arg
        assert isinstance(result, str)

    def test_maintenance_url_filter(self, app):
        """Test maintenance_url filter returns a URL."""
        from apps.planning.src.template_filters import register_template_filters

        register_template_filters(app)
        filter_func = app.jinja_env.filters["maintenance_url"]
        result = filter_func("Test Task")
        assert isinstance(result, str)


class TestDatabaseManager:
    """Tests for DatabaseManager in extensions.py."""

    def test_database_manager_init(self):
        """Test DatabaseManager initialization."""
        from apps.planning.src.extensions import DatabaseManager

        dm = DatabaseManager()
        assert dm.app is None
        assert dm.database_path is None

    @patch("apps.planning.src.extensions.init_db")
    @patch("apps.planning.src.extensions.get_db_connection")
    @patch("apps.planning.src.extensions.ensure_skill_update_log_table")
    @patch("apps.planning.src.extensions.load_app_config")
    def test_database_manager_init_app(
        self, mock_load, mock_ensure, mock_get_conn, mock_init, app
    ):
        """Test init_app sets up database."""
        from apps.planning.src.extensions import DatabaseManager

        # Create mock connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # Ensure required config keys are present
        app.config["DEBUG_USE_TEST_DB"] = False
        app.config["DATABASE_PATH"] = ":memory:"

        dm = DatabaseManager()
        dm.init_app(app)

        # Verify init_db was called
        mock_init.assert_called_once()
        mock_ensure.assert_called_once()
        mock_load.assert_called_once()
        mock_conn.close.assert_called()  # May be called multiple times
