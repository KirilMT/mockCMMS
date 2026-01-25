import os
from unittest.mock import patch

from apps.reports.src.services.report_generator import ReportGenerator
from src.app import create_app


@patch("os.makedirs")
@patch("builtins.open")
def test_report_generator_defaults_coverage(mock_open, mock_makedirs):
    """Trigger missing lines in report_generator.py for coverage."""
    generator = ReportGenerator()
    data = {"tasks": []}
    generator.generate_report("test", "Test Title", {}, "csv", 1, data=data)
    assert "generated_at" in data
    assert data["title"] == "Test Title"


@patch.dict(os.environ)
def test_app_production_db_default_coverage():
    """Trigger the production DB default branch in src/app.py."""
    # surgically remove vars that would trigger other branches,
    # but don't clear everything which can break coverage internals
    if "TESTING_PRODUCTION" in os.environ:
        del os.environ["TESTING_PRODUCTION"]
    if "E2E_TEST" in os.environ:
        del os.environ["E2E_TEST"]
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    app = create_app({"TESTING": False})
    # Check that it uses mockcmms.db (the production default)
    assert "mockcmms.db" in app.config["SQLALCHEMY_DATABASE_URI"]
