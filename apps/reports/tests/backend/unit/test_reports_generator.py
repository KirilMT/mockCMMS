from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.reports.src.services.report_generator import ReportGenerator
from src.services.db_utils import MaintenanceOrder


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

    def test_generate_report_with_data_pdf(self, generator, sample_data):
        """Test generating a PDF report (placeholder logic)."""
        with patch("apps.reports.src.services.report_generator.os.makedirs"):
            with patch("builtins.open", mock_open()):
                path = generator.generate_report(
                    "test_report", "Test Title", {}, "PDF", 1, data=sample_data
                )
                assert path.endswith(".txt")

    def test_generate_report_invalid_format(self, generator, sample_data):
        """Test invalid format raises ValueError."""
        with patch("apps.reports.src.services.report_generator.os.makedirs"):
            with pytest.raises(ValueError, match="Unsupported format"):
                generator.generate_report(
                    "test_report", "Title", {}, "XYZ", 1, data=sample_data
                )

    def test_generate_report_no_data_reactive(self, generator):
        """Test fetching reactive data when no data provided."""
        mock_mo = MagicMock(spec=MaintenanceOrder)
        mock_mo.to_dict.return_value = {"id": 1, "order_type": "Reactive"}

        with patch(
            "apps.reports.src.services.report_generator.MaintenanceOrder"
        ) as mock_model:
            mock_model.created_at = create_mock_column()
            filtered = mock_model.query.filter_by.return_value.filter.return_value
            filtered.all.return_value = [mock_mo]

            with patch.object(generator, "generate_csv") as mock_csv:
                with patch("apps.reports.src.services.report_generator.os.makedirs"):
                    generator.generate_report(
                        "reactive_production", "Title", {"priority": "All"}, "CSV", 1
                    )
                mock_csv.assert_called()

    def test_generate_report_no_data_weekend(self, generator):
        """Test fetching weekend data when no data provided."""
        mock_mo = MagicMock(spec=MaintenanceOrder)
        mock_mo.to_dict.return_value = {"id": 1, "date": "2023-01-01"}

        with patch(
            "apps.reports.src.services.report_generator.MaintenanceOrder"
        ) as mock_model:
            mock_model.completion_date = create_mock_column()
            mock_model.query.filter.return_value.all.return_value = [mock_mo]

            with patch.object(generator, "generate_csv") as mock_csv:
                with patch("apps.reports.src.services.report_generator.os.makedirs"):
                    generator.generate_report(
                        "completed_weekend",
                        "Title",
                        {"weekend_date": "2023-01-01"},
                        "CSV",
                        1,
                    )
                mock_csv.assert_called()

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
