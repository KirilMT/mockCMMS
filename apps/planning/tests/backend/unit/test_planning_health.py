import tempfile
from unittest.mock import MagicMock, patch

import pytest

from apps.planning.src.services.health_check import HealthChecker


class TestHealthCoverage:
    """Test suite for health check service."""

    @pytest.fixture
    def app_mock(self):
        """Mock Flask app context."""
        app = MagicMock()
        app.config = {
            "DATABASE_PATH": "test.db",
            "OUTPUT_FOLDER": tempfile.gettempdir(),
            "TEMPLATES_FOLDER": "/templates",
            "STATIC_FOLDER": "/static",
            "SECRET_KEY": "secret",
            "FLASK_DEBUG": False,
        }
        return app

    def test_check_database_health_success(self, app_mock):
        """Test successful database health check."""
        with (
            patch("apps.planning.src.services.health_check.current_app", app_mock),
            patch("os.path.exists", return_value=True),
            patch("sqlite3.connect") as mock_connect,
        ):
            mock_cursor = mock_connect.return_value.cursor.return_value
            mock_cursor.fetchone.return_value = [10]  # > 5 tables

            checker = HealthChecker(app_mock)
            status, msg = checker.check_database_health()

            assert status is True
            assert "Database healthy" in msg

    def test_check_database_health_missing_file(self, app_mock):
        """Test database missing file."""
        with (
            patch("apps.planning.src.services.health_check.current_app", app_mock),
            patch("os.path.exists", return_value=False),
        ):
            checker = HealthChecker(app_mock)
            status, msg = checker.check_database_health()

            assert status is False
            assert "does not exist" in msg

    def test_check_filesystem_health_success(self, app_mock):
        """Test filesystem health."""
        with (
            patch("apps.planning.src.services.health_check.current_app", app_mock),
            patch("os.path.exists", return_value=True),
            patch("os.access", return_value=True),
        ):
            checker = HealthChecker()
            status, msg = checker.check_filesystem_health()
            assert status is True

    def test_check_filesystem_health_failure(self, app_mock):
        """Test filesystem missing paths."""
        with (
            patch("apps.planning.src.services.health_check.current_app", app_mock),
            patch("os.path.exists", return_value=False),
        ):
            checker = HealthChecker()
            status, msg = checker.check_filesystem_health()
            assert status is False
            assert "Missing directory" in msg

    def test_check_configuration_health(self, app_mock):
        """Test configuration validation."""
        with patch("apps.planning.src.services.health_check.current_app", app_mock):
            checker = HealthChecker()

            # Valid config
            status, msg = checker.check_configuration_health()
            assert status is True

            # Missing config
            app_mock.config["SECRET_KEY"] = None
            status, msg = checker.check_configuration_health()
            assert status is False
            assert "Missing configuration" in msg

    def test_get_application_metrics(self, app_mock):
        """Test metrics collection."""
        with (
            patch("apps.planning.src.services.health_check.current_app", app_mock),
            patch("sqlite3.connect") as mock_connect,
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1048576),
        ):  # 1MB
            mock_cursor = mock_connect.return_value.cursor.return_value
            mock_cursor.fetchone.side_effect = [
                [10],
                [5],
                [3],
                [20],
            ]  # Counts for tables

            checker = HealthChecker()
            metrics = checker.get_application_metrics()

            assert metrics["technicians_count"] == 10
            assert metrics["database_size_mb"] == 1.0

    def test_perform_full_health_check(self, app_mock):
        """Test full orchestration."""
        with (
            patch("apps.planning.src.services.health_check.current_app", app_mock),
            patch.object(
                HealthChecker, "check_database_health", return_value=(True, "OK")
            ),
            patch.object(
                HealthChecker, "check_filesystem_health", return_value=(True, "OK")
            ),
            patch.object(
                HealthChecker, "check_configuration_health", return_value=(True, "OK")
            ),
            patch.object(HealthChecker, "get_application_metrics", return_value={}),
        ):
            checker = HealthChecker()
            result = checker.perform_full_health_check()

            assert result["status"] == "healthy"
            assert result["checks"]["database"]["status"] == "healthy"
