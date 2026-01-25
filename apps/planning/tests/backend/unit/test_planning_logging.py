import json
import logging
from unittest.mock import patch

import pytest
from flask import Flask

from apps.planning.src.services.logging_config import (
    LoggingConfig,
    MetricsCollector,
    StructuredFormatter,
    performance_monitor,
)


class TestLoggingCoverage:
    """Test suite for logging configuration and utilities."""

    def test_structured_formatter(self):
        """Test JSON formatting of log records."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_func"

        json_output = formatter.format(record)
        data = json.loads(json_output)

        assert data["logger"] == "test_logger"
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["function"] == "test_func"
        assert "timestamp" in data

    def test_structured_formatter_with_exception(self):
        """Test formatting includes exception info."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test_path.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

        json_output = formatter.format(record)
        data = json.loads(json_output)
        assert "exception" in data
        assert "Test error" in data["exception"]

    def test_metrics_collector(self):
        """Test metrics aggregation."""
        collector = MetricsCollector()

        # Test request metrics
        collector.record_request_metric("index", "GET", 0.5, 200)
        collector.record_request_metric("index", "GET", 0.3, 200)
        collector.record_request_metric("index", "POST", 0.4, 400)

        metrics = collector.get_all_metrics()
        req_metrics = metrics["requests"]

        assert "GET_index" in req_metrics
        assert req_metrics["GET_index"]["count"] == 2
        assert req_metrics["GET_index"]["total_duration"] == 0.8
        assert req_metrics["GET_index"]["avg_duration"] == 0.4
        assert req_metrics["GET_index"]["status_codes"][200] == 2

        # Test DB metrics
        collector.record_database_metric("query_users", 0.1, success=True)
        collector.record_database_metric("query_users", 0.2, success=False)

        db_metrics = metrics["database"]
        assert "query_users" in db_metrics
        assert db_metrics["query_users"]["count"] == 2
        assert db_metrics["query_users"]["success_count"] == 1
        assert db_metrics["query_users"]["error_count"] == 1

    def test_performance_monitor_decorator(self, caplog):
        """Test performance tracking decorator."""
        # Reset collector
        from apps.planning.src.services.logging_config import metrics_collector

        metrics_collector.__init__()

        # Define decorated function
        @performance_monitor("db_test_op")
        def slow_func():
            return "success"

        # Test successful execution
        result = slow_func()
        assert result == "success"

        metrics = metrics_collector.get_all_metrics()
        assert "db_test_op" in metrics["database"]
        assert metrics["database"]["db_test_op"]["count"] == 1

        # Test failure
        @performance_monitor("fail_op")
        def fail_func():
            raise ValueError("Fail")

        with pytest.raises(ValueError):
            fail_func()

    def test_logging_config_setup(self):
        """Test LoggingConfig.setup_logging."""
        with (
            patch("os.makedirs"),
            patch("logging.FileHandler"),
            patch("logging.StreamHandler"),
        ):
            # Test Debug Mode
            with patch(
                "apps.planning.src.services.logging_config.Config.FLASK_DEBUG", True
            ):
                logger = LoggingConfig.setup_logging()
                assert logger.level == logging.DEBUG

            # Test Production Mode
            with patch(
                "apps.planning.src.services.logging_config.Config.FLASK_DEBUG", False
            ):
                logger = LoggingConfig.setup_logging()
                assert logger.level == logging.INFO

    def test_request_monitoring_middleware(self):
        """Test Flask middleware setup."""
        app = Flask(__name__)
        LoggingConfig._setup_request_monitoring(app)

        target = (
            "apps.planning.src.services.logging_config"
            ".metrics_collector.record_request_metric"
        )
        with app.test_client() as client:
            with patch(target) as mock_record:
                client.get("/")
                mock_record.assert_called()
