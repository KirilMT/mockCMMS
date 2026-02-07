from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from apps.reports.src.models import Incident
from apps.reports.src.services.data_aggregator import DataAggregator
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


class TestDataAggregator:
    """Consolidated tests for DataAggregator covering both mock and integration
    scenarios."""

    @pytest.fixture
    def aggregator(self, app):
        with app.app_context():
            yield DataAggregator()

    # =========================================================================
    # MOCKED LOGIC TESTS (Coverage Focused)
    # =========================================================================

    def test_get_weekend_tasks_mock(self, aggregator):
        """Test get_weekend_tasks query with mocks."""
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

    def test_get_incidents_no_filter_mock(self, aggregator):
        """Test get_incidents without filters using mocks."""
        with patch("apps.reports.src.services.data_aggregator.Incident") as mock_inc:
            mock_item = MagicMock(spec=Incident)
            mock_item.to_dict.return_value = {"id": 1}
            mock_inc.query.all.return_value = [mock_item]

            result = aggregator.get_incidents()
            assert len(result) == 1

    def test_get_incidents_with_filters_mock(self, aggregator):
        """Test get_incidents with all filters using mocks."""
        filters = {
            "incident_type": "TypeA",
            "severity": "High",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
        }
        with patch("apps.reports.src.services.data_aggregator.Incident") as mock_inc:
            mock_inc.timestamp = create_mock_column()
            q = mock_inc.query
            q = q.filter_by.return_value
            q = q.filter_by.return_value
            q = q.filter.return_value
            q = q.filter.return_value
            q.all.return_value = []

            aggregator.get_incidents(filters)
            assert q.all.called

    # =========================================================================
    # INTEGRATION STYLE TESTS (Real DB Objects)
    # =========================================================================

    def test_data_aggregator_incidents_db(self, app, aggregator):
        """Test DataAggregator fetches incidents correctly from DB."""
        with app.app_context():
            today = datetime.now()
            incident = Incident(
                incident_type="Safety Issue",
                equipment_line="Line 2",
                description="Test Safety",
                severity="Medium",
                technician_name="Tech 1",
                timestamp=today,
            )
            db.session.add(incident)
            db.session.commit()

            incidents = aggregator.get_incidents()
            assert len(incidents) >= 1
            assert any(i["incident_type"] == "Safety Issue" for i in incidents)

    def test_data_aggregator_weekend_tasks_db(self, app, aggregator):
        """Test DataAggregator can query weekend tasks from DB."""
        with app.app_context():
            today = datetime.now()
            asset = Asset(asset_code="A_AGGR", name="Test Asset Aggr")
            db.session.add(asset)
            db.session.commit()

            mo = MaintenanceOrder(
                asset_id=asset.id,
                description="Weekend Setup Test",
                order_type="Preventive",
                status="Completed",
                due_date=today,
                created_at=today,
            )
            db.session.add(mo)
            db.session.commit()

            start_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
            end_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")

            tasks = aggregator.get_weekend_tasks(start_date, end_date)
            assert isinstance(tasks, list)
            assert any(t["description"] == "Weekend Setup Test" for t in tasks)
