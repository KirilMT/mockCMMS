from unittest.mock import patch

import pytest
from flask import Flask, jsonify

from apps.planning.src.services.security import (
    InputValidator,
    SecurityMiddleware,
    require_json_fields,
    validate_request,
    validate_tech_id_param,
)


class TestSecurityCoverage:
    """Coverage tests for security.py."""

    def test_validate_integer_range(self):
        """Test integer validation with ranges."""
        assert InputValidator.validate_integer(10, min_val=0, max_val=20) == 10

        # Code wraps exceptions in "Invalid integer value: ..."
        # Original error: "Value -1 is less than minimum 0"
        # Since invalid_integer catches ValueError, it re-raises as ValueError(f"...")

        with pytest.raises(ValueError, match="Invalid integer value"):
            InputValidator.validate_integer(-1, min_val=0)

        with pytest.raises(ValueError, match="Invalid integer value"):
            InputValidator.validate_integer(21, max_val=20)

        with pytest.raises(ValueError, match="Invalid integer value"):
            InputValidator.validate_integer("invalid")

    def test_validate_string_constraints(self):
        """Test string validation constraints."""
        assert InputValidator.validate_string("valid") == "valid"

        with pytest.raises(ValueError, match="Expected string"):
            InputValidator.validate_string(123)

        with pytest.raises(ValueError, match="String too long"):
            InputValidator.validate_string("a" * 256, max_length=255)

        with pytest.raises(ValueError, match="String does not match required pattern"):
            InputValidator.validate_string("abc", pattern=r"^[0-9]+$")

    def test_validate_json_request(self):
        """Test JSON request validation."""
        app = Flask(__name__)
        with app.test_request_context(json={"key": "value"}):
            assert InputValidator.validate_json_request() == {"key": "value"}

        with app.test_request_context(json={"key": "value"}):
            with pytest.raises(ValueError, match="Missing required fields"):
                InputValidator.validate_json_request(required_fields=["missing"])

        with app.test_request_context(data="not json", content_type="text/plain"):
            with pytest.raises(ValueError, match="Request must be JSON"):
                InputValidator.validate_json_request()

        with app.test_request_context(json="not dict"):
            with pytest.raises(ValueError, match="JSON must be an object"):
                InputValidator.validate_json_request()

    def test_validate_request_decorator(self):
        """Test validate_request decorator."""
        app = Flask(__name__)

        def failing_validation():
            raise ValueError("Validation failed")

        @validate_request(failing_validation)
        def target_func():
            return "success"

        with app.test_request_context():
            response, status = target_func()
            assert status == 400
            assert response.json["error"] == "Validation failed"

    def test_validate_request_internal_error(self):
        """Test validate_request decorator handles unexpected errors."""
        app = Flask(__name__)

        def error_validation():
            raise RuntimeError("Unexpected boom")

        @validate_request(error_validation)
        def target_func():
            return "success"

        with app.test_request_context():
            response, status = target_func()
            assert status == 500
            assert response.json["error"] == "Internal server error"

    def test_require_json_fields_helper(self):
        """Test require_json_fields helper."""
        app = Flask(__name__)
        validator = require_json_fields("required_field")

        with app.test_request_context(json={"other": "value"}):
            with pytest.raises(ValueError, match="Missing required fields"):
                validator()

    def test_validate_tech_id_param_helper(self):
        """Test validate_tech_id_param helper."""
        app = Flask(__name__)
        validator = validate_tech_id_param()

        # Test Query Param
        with app.test_request_context(query_string="technician_id=0"):
            with pytest.raises(ValueError, match="Invalid integer value"):
                validator()

        # Test JSON Body
        with app.test_request_context(json={"technician_id": 0}):
            with pytest.raises(ValueError, match="Invalid integer value"):
                validator()

    def test_security_headers_api(self):
        """Test security headers for API source."""
        app = Flask(__name__)
        app.config["JSONIFY_MIMETYPE"] = "application/json"  # Fix for jsonify context

        # We need to mock Config.DATA_SOURCE since it is imported directly
        with patch("apps.planning.src.services.security.Config") as mock_config:
            mock_config.DATA_SOURCE = "api"
            with app.app_context():
                response = jsonify({})
                # Simulate existing X-Frame-Options
                response.headers["X-Frame-Options"] = "SAMEORIGIN"

                SecurityMiddleware.add_security_headers(response)
                assert "X-Frame-Options" not in response.headers
                assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_security_headers_default(self):
        """Test security headers for non-API source."""
        app = Flask(__name__)
        app.config["JSONIFY_MIMETYPE"] = "application/json"

        with patch("apps.planning.src.services.security.Config") as mock_config:
            mock_config.DATA_SOURCE = "db"
            with app.app_context():
                response = jsonify({})

                SecurityMiddleware.add_security_headers(response)
                assert response.headers["X-Frame-Options"] == "DENY"
                assert (
                    response.headers["Strict-Transport-Security"]
                    == "max-age=31536000; includeSubDomains"
                )
