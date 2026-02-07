import os
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.reports.src.services.report_generator import ReportGenerator
from src.services.db_utils import Asset, MaintenanceOrder, db


def create_mock_column():
    """Helper to create a column mock that supports comparison."""
    m = MagicMock()
    m.__ge__ = MagicMock(return_value=MagicMock())
    m.__gt__ = MagicMock(return_value=MagicMock())
    m.__le__ = MagicMock(return_value=MagicMock())
    m.__lt__ = MagicMock(return_value=MagicMock())
    m.__eq__ = MagicMock(return_value=MagicMock())
    m.__ne__ = MagicMock(return_value=MagicMock())
    return m


class TestReportGenerator:
    """Consolidated tests for ReportGenerator."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def sample_data(self):
        return {
            "title": "Test Report",
            "generated_at": "2023-01-01T12:00:00",
            "maintenance_orders": [
                {"id": 1, "description": "Fix Pump", "status": "Completed"},
                {"id": 2, "description": "Inspect Motor", "status": "Pending"},
            ],
        }

    def test_generate_report_with_data_csv(self, generator, sample_data):
        """Test generating a CSV report with provided data."""
        with patch("apps.reports.src.services.report_generator.os.makedirs"):
            with patch("builtins.open", mock_open()) as mock_file:
                path = generator.generate_report(
                    "test_report", "Test Title", {}, "CSV", 1, data=sample_data
                )
                assert path.endswith(".csv")
                mock_file.assert_called()

    def test_generate_report_with_data_markdown(self, generator, sample_data):
        """Test generating a Markdown report with provided data."""
        with patch("apps.reports.src.services.report_generator.os.makedirs"):
            with patch("builtins.open", mock_open()) as mock_file:
                path = generator.generate_report(
                    "test_report", "Test Title", {}, "Markdown", 1, data=sample_data
                )
                assert path.endswith(".markdown")
                handle = mock_file()
                args_list = handle.write.call_args_list
                assert any("# Test Title" in str(args) for args in args_list)

    def test_generate_report_with_data_pdf(self, generator, sample_data, tmp_path):
        """Test generating a PDF report (placeholder logic)."""
        parameters = {}
        generator._reports_dir = str(tmp_path)
        path = generator.generate_report(
            "test_report", "My PDF Title", parameters, "PDF", 1, data=sample_data
        )
        assert os.path.exists(path)
        assert path.endswith(".txt")
        with open(path, "r") as f:
            content = f.read()
            assert "PDF Report Placeholder: My PDF Title" in content

    def test_generate_csv_no_data(self, generator, tmp_path):
        """Test CSV generation with empty data."""
        file_path = str(tmp_path / "empty.csv")
        result = generator.generate_csv({}, file_path)
        assert os.path.exists(result)
        with open(result, "r") as f:
            assert f.read() == "No data found"

    def test_generate_report_invalid_format(self, generator, sample_data):
        """Test invalid format raises ValueError."""
        with patch("apps.reports.src.services.report_generator.os.makedirs"):
            with pytest.raises(ValueError, match="Unsupported format"):
                generator.generate_report(
                    "test_report", "Title", {}, "XYZ", 1, data=sample_data
                )

    def test_generate_report_missing_data(self, generator):
        """Test error when data is missing for unknown report type."""
        with pytest.raises(ValueError, match="Data required for report type"):
            generator.generate_report("unknown_type", "Title", {}, "CSV", 1)

    def test_generate_csv_empty(self, generator):
        """Test CSV generation with empty data."""
        with patch("builtins.open", mock_open()) as mock_file:
            data = {"maintenance_orders": []}
            generator.generate_csv(data, "test.csv")
            handle = mock_file()
            handle.write.assert_called_with("No data found")

    def test_generate_summary_stats(self, generator, sample_data):
        """Test summary stats calculation."""
        stats = generator.generate_summary_stats(sample_data)
        assert stats["total_count"] == 2
        assert stats["completion_rate"] == "50.0%"

    def test_report_generator_defaults(self, generator):
        """Test defaults like generated_at injection (from booster)."""
        with patch("apps.reports.src.services.report_generator.os.makedirs"):
            with patch("builtins.open", mock_open()):
                data = {"tasks": []}
                generator.generate_report("test", "Test Title", {}, "CSV", 1, data=data)
                assert "generated_at" in data
                assert data["title"] == "Test Title"


class TestReportGeneratorDBIntegration:
    """Comprehensive tests for ReportGenerator to maximize coverage using real DB."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create a generator instance with a temporary reports directory."""
        gen = ReportGenerator()
        # Override reports directory to use temp path
        gen._reports_dir = str(tmp_path / "reports")
        return gen

    @pytest.fixture
    def sample_data(self):
        return {
            "title": "Comprehensive Test Report",
            "generated_at": datetime.now().isoformat(),
            "maintenance_orders": [
                {
                    "id": 1,
                    "description": "Test Order 1",
                    "status": "Completed",
                    "order_type": "Reactive",
                    "created_at": "2023-01-01T10:00:00",
                    "modified_on": "2023-01-02T14:00:00",
                    "priority": "High",
                },
                {
                    "id": 2,
                    "description": "Test Order 2",
                    "status": "Pending",
                    "order_type": "Preventive",
                    "created_at": "2023-01-03T09:00:00",
                    "priority": "Medium",
                },
            ],
            "incidents": [
                {
                    "id": 1,
                    "incident_type": "Safety",
                    "severity": "High",
                    "description": "Test Incident",
                    "timestamp": "2023-01-01T10:00:00",
                }
            ],
            "tasks": [
                {"id": 3, "description": "Test Task", "due_date": "2023-01-05T00:00:00"}
            ],
            "weekend_dates": {"saturday": "2023-01-07", "sunday": "2023-01-08"},
        }

    def test_init_paths(self):
        """Test initialization and path calculation."""
        gen = ReportGenerator()
        assert "instance" in gen.reports_dir
        assert "reports" in gen.reports_dir

    def test_generate_report_no_data_reactive(self, generator, app):
        """Test generating a reactive report without fetching data (DB integration)."""
        with app.app_context():
            # Create required asset first
            asset = Asset(asset_code="R_TEST", name="Test Asset", status="Operational")
            db.session.add(asset)
            db.session.commit()

            # Create test data
            mo = MaintenanceOrder(
                description="Reactive Test",
                order_type="Reactive",
                status="Completed",
                priority="High",
                created_at=datetime.now(),
                asset_id=asset.id,
            )
            db.session.add(mo)
            db.session.commit()

            # Test standard generation
            path = generator.generate_report(
                "reactive_production", "Reactive Report", {"priority": "High"}, "CSV", 1
            )
            assert os.path.exists(path)
            with open(path, "r") as f:
                content = f.read()
                assert "Reactive Test" in content

    def test_generate_report_no_data_weekend(self, generator, app):
        """Test generating weekend report without provided data."""
        with app.app_context():
            # Calculate a weekend date for the query logic
            # The logic finds the NEXT weekend
            today = datetime.now()
            check_date = today.strftime("%Y-%m-%d")

            path = generator.generate_report(
                "completed_weekend",
                "Weekend Report",
                {"weekend_date": check_date},
                "CSV",
                1,
            )
            assert os.path.exists(path)

    def test_generate_report_data_types(self, generator, sample_data):
        """Test generating reports with different data types (incidents, tasks)."""
        # Test Incidents
        incident_data = {"incidents": sample_data["incidents"], "title": "Incidents"}
        path = generator.generate_report(
            "incidents", "Incidents", {}, "CSV", 1, data=incident_data
        )
        with open(path, "r") as f:
            content = f.read()
            assert "Safety" in content

        # Test Tasks
        task_data = {"tasks": sample_data["tasks"], "title": "Tasks"}
        path = generator.generate_report("tasks", "Tasks", {}, "CSV", 1, data=task_data)
        with open(path, "r") as f:
            content = f.read()
            assert "Test Task" in content

    def test_stats_generation(self, generator, sample_data):
        """Test summary statistics generation."""
        summary = generator.generate_summary_stats(sample_data)
        assert summary["total_count"] == 2
        assert summary["completion_rate"] == "50.0%"
