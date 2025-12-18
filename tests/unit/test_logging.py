"""
Unit tests for the logging configuration and performance monitoring.
"""

import json
import logging
import time
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from src.services.logging_config import (
    LoggingConfig,
    StructuredFormatter,
    MetricsCollector,
    performance_monitor,
    metrics_collector,
)


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = Flask(__name__)
    app.debug = False
    app.testing = True
    return app


def test_structured_formatter():
    """Test that the structured formatter outputs valid JSON with expected fields."""
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted_output = formatter.format(record)
    log_data = json.loads(formatted_output)

    assert log_data["level"] == "INFO"
    assert log_data["logger"] == "test_logger"
    assert log_data["message"] == "Test message"
    assert "timestamp" in log_data
    assert "module" in log_data
    assert "function" in log_data


def test_metrics_collector():
    """Test the metrics collector functionality."""
    collector = MetricsCollector()

    # Test request metrics
    collector.record_request_metric("index", "GET", 0.1, 200)
    collector.record_request_metric("index", "GET", 0.2, 200)
    collector.record_request_metric("index", "GET", 0.3, 404)

    metrics = collector.get_all_metrics()
    req_metrics = metrics["requests"]["GET_index"]

    assert req_metrics["count"] == 3
    assert req_metrics["total_duration"] == pytest.approx(0.6)
    assert req_metrics["avg_duration"] == pytest.approx(0.2)
    assert req_metrics["status_codes"][200] == 2
    assert req_metrics["status_codes"][404] == 1

    # Test database metrics
    collector.record_database_metric("query_users", 0.05, success=True)
    collector.record_database_metric("query_users", 0.05, success=False)

    db_metrics = metrics["database"]["query_users"]
    assert db_metrics["count"] == 2
    assert db_metrics["total_duration"] == pytest.approx(0.1)
    assert db_metrics["success_count"] == 1
    assert db_metrics["error_count"] == 1


def test_performance_monitor_decorator():
    """Test the performance monitor decorator."""

    # Reset metrics collector for this test
    metrics_collector.database_metrics = {}

    @performance_monitor("test_db_op")
    def successful_op():
        time.sleep(0.01)
        return "success"

    @performance_monitor("test_db_op_fail")
    def failing_op():
        raise ValueError("error")

    # Test success
    result = successful_op()
    assert result == "success"

    metrics = metrics_collector.get_all_metrics()
    assert "test_db_op" in metrics["database"]
    assert metrics["database"]["test_db_op"]["count"] == 1
    assert metrics["database"]["test_db_op"]["success_count"] == 1

    # Test failure
    with pytest.raises(ValueError):
        failing_op()

    metrics = metrics_collector.get_all_metrics()
    assert "test_db_op_fail" in metrics["database"]
    assert metrics["database"]["test_db_op_fail"]["error_count"] == 1


def test_logging_setup(app):
    """Test that logging setup configures handlers correctly."""
    with patch("logging.FileHandler") as mock_file_handler:
        # Configure the mock to return a NEW mock object each time it's instantiated
        mock_file_handler.side_effect = lambda *args, **kwargs: MagicMock()

        logger = LoggingConfig.setup_logging(app)

        assert logger.level == logging.INFO

        # Check if handlers are added (Console + File + Error File + Perf File)
        # Note: Perf file only in production (app.debug=False)
        assert len(logger.handlers) >= 4


def test_request_monitoring(app):
    """Test request monitoring middleware."""
    LoggingConfig.setup_logging(app)

    with app.test_client() as client:
        # Mocking the metrics collector to verify call
        with patch(
            "src.services.logging_config.metrics_collector.record_request_metric"
        ) as mock_record:

            @app.route("/test-log")
            def test_route():
                return "ok"

            client.get("/test-log")

            assert mock_record.called
            args, _ = mock_record.call_args
            # Args: endpoint, method, duration, status_code
            assert args[0] == "test_route"
            assert args[1] == "GET"
            assert args[3] == 200
