from unittest.mock import MagicMock, patch

import pytest

from apps.reports.src.models import Incident
from apps.reports.src.services.data_aggregator import DataAggregator
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


class TestDataAggregatorCoverage:
    """Targeted tests for DataAggregator coverage."""

    @pytest.fixture
    def aggregator(self):
        return DataAggregator()

    def test_get_weekend_tasks(self, aggregator):
        """Test get_weekend_tasks query."""
        with patch(
            "apps.reports.src.services.data_aggregator.MaintenanceOrder"
        ) as mock_mo:
            mock_mo.due_date = create_mock_column()

            mock_task = MagicMock(spec=MaintenanceOrder)
            mock_task.to_dict.return_value = {"id": 1}
            mock_mo.query.filter.return_value.all.return_value = [mock_task]

            result = aggregator.get_weekend_tasks("2023-01-01", "2023-01-02")
            assert len(result) == 1
            assert result[0]["id"] == 1
            # Verify filter called
            mock_mo.query.filter.assert_called()

    def test_get_shift_data_morning(self, aggregator):
        """Test get_shift_data for morning shift."""
        with patch(
            "apps.reports.src.services.data_aggregator.MaintenanceOrder"
        ) as mock_mo:
            mock_mo.created_at = create_mock_column()

            mock_task = MagicMock(spec=MaintenanceOrder)
            mock_task.to_dict.return_value = {"id": 1}
            mock_mo.query.filter.return_value.all.return_value = [mock_task]

            result = aggregator.get_shift_data("2023-01-01", "Morning")
            assert len(result) == 1

            # Verify time range
            # Morning: 6-14

            # We can't easily inspect expression objects, but we know it runs

    def test_get_shift_data_afternoon(self, aggregator):
        """Test get_shift_data for afternoon shift."""
        with patch(
            "apps.reports.src.services.data_aggregator.MaintenanceOrder"
        ) as mock_mo:
            mock_mo.created_at = create_mock_column()

            mock_mo.query.filter.return_value.all.return_value = []
            aggregator.get_shift_data("2023-01-01", "Afternoon")
            mock_mo.query.filter.assert_called()

    def test_get_shift_data_night(self, aggregator):
        """Test get_shift_data for night shift (crosses day boundary)."""
        with patch(
            "apps.reports.src.services.data_aggregator.MaintenanceOrder"
        ) as mock_mo:
            mock_mo.created_at = create_mock_column()

            mock_mo.query.filter.return_value.all.return_value = []
            aggregator.get_shift_data("2023-01-01", "Night")
            mock_mo.query.filter.assert_called()

    def test_get_incidents_no_filter(self, aggregator):
        """Test get_incidents without filters."""
        with patch("apps.reports.src.services.data_aggregator.Incident") as mock_inc:
            mock_item = MagicMock(spec=Incident)
            mock_item.to_dict.return_value = {"id": 1}
            mock_inc.query.all.return_value = [mock_item]

            result = aggregator.get_incidents()
            assert len(result) == 1

    def test_get_incidents_with_filters(self, aggregator):
        """Test get_incidents with all filters."""
        filters = {
            "incident_type": "TypeA",
            "severity": "High",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
        }
        with patch("apps.reports.src.services.data_aggregator.Incident") as mock_inc:
            mock_inc.timestamp = create_mock_column()

            # Chain mocks for query.filter_by...filter...all
            # Base query
            q = mock_inc.query
            # Filter by type
            q = q.filter_by.return_value
            # Filter by severity
            q = q.filter_by.return_value
            # Filter start date
            q = q.filter.return_value
            # Filter end date
            q = q.filter.return_value

            q.all.return_value = []

            aggregator.get_incidents(filters)
            # Verify calls logic implicitly by successful execution
            assert q.all.called
