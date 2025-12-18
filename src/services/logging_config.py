"""
Enhanced logging configuration for the core mockCMMS application.
"""

import logging
import os
import json
import time
from datetime import datetime
from functools import wraps
from flask import request, g, current_app

# Calculate ROOT_DIR relative to this file -> ../.. -> root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging in production."""

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        try:
            if request:
                log_entry["request"] = {
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.remote_addr,
                    "user_agent": str(request.user_agent),
                }
        except RuntimeError:
            # Outside request context
            pass

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class MetricsCollector:
    """Collects application performance metrics."""

    def __init__(self):
        self.request_metrics = {}
        self.database_metrics = {}

    def record_request_metric(self, endpoint, method, duration, status_code):
        """Record request timing and status metrics."""
        key = f"{method}_{endpoint}"
        if key not in self.request_metrics:
            self.request_metrics[key] = {
                "count": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "status_codes": {},
            }

        metrics = self.request_metrics[key]
        metrics["count"] += 1
        metrics["total_duration"] += duration
        metrics["avg_duration"] = metrics["total_duration"] / metrics["count"]

        # Track status codes
        if status_code not in metrics["status_codes"]:
            metrics["status_codes"][status_code] = 0
        metrics["status_codes"][status_code] += 1

    def record_database_metric(self, operation, duration, success=True):
        """Record database operation metrics."""
        if operation not in self.database_metrics:
            self.database_metrics[operation] = {
                "count": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "success_count": 0,
                "error_count": 0,
            }

        metrics = self.database_metrics[operation]
        metrics["count"] += 1
        metrics["total_duration"] += duration
        metrics["avg_duration"] = metrics["total_duration"] / metrics["count"]

        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1

    def get_all_metrics(self):
        """Get all collected metrics."""
        return {
            "requests": self.request_metrics,
            "database": self.database_metrics,
            "collection_time": datetime.utcnow().isoformat(),
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()


def performance_monitor(operation_name):
    """Decorator to monitor function performance."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                if (
                    "db" in operation_name.lower()
                    or "database" in operation_name.lower()
                ):
                    metrics_collector.record_database_metric(
                        operation_name, duration, success
                    )

                # Log slow operations
                if duration > 1.0:  # Operations taking more than 1 second
                    if current_app:
                        current_app.logger.warning(
                            f"Slow operation detected: {operation_name} "
                            f"took {duration:.2f}s"
                        )

        return wrapper

    return decorator


class LoggingConfig:
    """Centralized logging configuration for the application."""

    @staticmethod
    def setup_logging(app=None):
        """Configure application logging with appropriate levels and formatting."""

        # Determine debug mode (use app.debug if app provided, else env var)
        flask_debug = app.debug if app else os.getenv("FLASK_DEBUG", "0") == "1"

        # Create logs directory if it doesn't exist
        log_dir = os.path.join(ROOT_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Set log level based on debug mode
        log_level = logging.DEBUG if flask_debug else logging.INFO

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # In Production: Take full control (Wipe defaults, use JSON Console)
        # In Debug: Touch NOTHING regarding console (Let Flask/Werkzeug defaults rule)
        if not flask_debug:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Add JSON Console for Production to ensure logs are visible
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(console_handler)

        # File handlers configuration (Always active, Always JSON)
        file_formatter = StructuredFormatter()

        # Helper to safely add file handler if not exists
        def add_file_handler(filename, level, formatter):
            path = os.path.join(log_dir, filename)
            # Check for existing handler for this file
            for h in root_logger.handlers:
                if isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == path:
                    return # Already exists
            
            handler = logging.FileHandler(path)
            handler.setLevel(level)
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

        add_file_handler("application.log", logging.INFO, file_formatter)
        add_file_handler("errors.log", logging.ERROR, file_formatter)

        # Performance log file (Production only)
        if not flask_debug:
            add_file_handler("performance.log", logging.WARNING, file_formatter)

        # Restore Werkzeug logs to console in Debug mode (lost due to Root FileHandler)
        if flask_debug:
            werkzeug_logger = logging.getLogger("werkzeug")
            # Only add if no handlers exist (avoid duplicates if reloaded)
            if not werkzeug_logger.handlers:
                w_handler = logging.StreamHandler()
                w_handler.setFormatter(logging.Formatter("%(message)s"))
                werkzeug_logger.addHandler(w_handler)

        # Set up request timing middleware if app is provided
        if app:
            LoggingConfig._setup_request_monitoring(app)
            
            # Ensure app logger propagates to root (so FileHandlers catch it)
            app.logger.propagate = True
            
            # Only clear app handlers in Production (where we use Root JSON).
            # In Debug, KEEP defaults (Standard Flask output).
            if not flask_debug:
                app.logger.handlers = []

        return root_logger

    @staticmethod
    def _setup_request_monitoring(app):
        """Set up request timing and monitoring middleware."""

        @app.before_request
        def before_request():
            g.start_time = time.time()

        @app.after_request
        def after_request(response):
            if hasattr(g, "start_time"):
                duration = time.time() - g.start_time

                # Record metrics
                metrics_collector.record_request_metric(
                    request.endpoint or "unknown",
                    request.method,
                    duration,
                    response.status_code,
                )

                # Log slow requests
                if duration > 2.0:  # Requests taking more than 2 seconds
                    app.logger.warning(
                        f"Slow request: {request.method} {request.path} "
                        f"took {duration:.2f}s"
                    )

                # Add performance headers for debugging (check app.debug)
                if app.debug:
                    response.headers["X-Response-Time"] = f"{duration:.3f}s"

            return response

    @staticmethod
    def get_metrics():
        """Get current application metrics."""
        return metrics_collector.get_all_metrics()
