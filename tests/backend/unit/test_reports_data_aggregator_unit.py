from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.reports.src.services.data_aggregator import DataAggregator


@pytest.fixture
def aggregator():
    return DataAggregator()


def test_get_shift_incidents_missing_asset(aggregator):
    """Test incident processing when MO has no asset."""
    # Use mocks for start/end to avoid datetime type checks
    start = MagicMock()
    start.__le__ = MagicMock(return_value=True)
    start.__ge__ = MagicMock(return_value=True)

    end = MagicMock()
    end.__le__ = MagicMock(return_value=True)
    end.__ge__ = MagicMock(return_value=True)

    mock_mo = MagicMock()
    mock_mo.id = 1
    mock_mo.asset = None  # Force N/A path
    mock_mo.description = "Test"
    mock_mo.created_at = datetime(2023, 1, 1, 10, 0, 0)
    mock_mo.priority = 1
    mock_mo.status = "Open"

    with patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO:
        # MockMO.created_at needs to be comparable too.
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        MockMO.created_at = mock_col
        MockMO.query.filter.return_value.all.return_value = [mock_mo]

        results = aggregator._get_shift_incidents(start, end)
        assert len(results) == 1
        assert results[0]["asset_name"] == "N/A"
        assert results[0]["asset_code"] == "N/A"


def test_get_aggregated_shift_data_missing_asset(aggregator):
    """Test shift aggregation when completed MO has no asset."""
    with (
        patch("apps.reports.src.services.data_aggregator.ShiftUtils") as MockUtils,
        patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO,
    ):
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        MockMO.due_date = mock_col

        # Mock ShiftUtils to return Mocks instead of datetimes
        start_mock = MagicMock()
        end_mock = MagicMock()
        MockUtils.return_value.get_shift_window.return_value = (
            start_mock,
            end_mock,
        )

        # Mock _get_shift_incidents (internal call)
        aggregator._get_shift_incidents = MagicMock(return_value=[])

        # Mock completed MOs with NO ASSET
        mock_mo = MagicMock()
        mock_mo.asset = None
        mock_mo.description = "Desc"
        mock_mo.status = "Completed"

        MockMO.query.filter.return_value.all.return_value = [mock_mo]

        data = aggregator.get_aggregated_shift_data("2023-01-01", "Early")

        items = data["break_activities"]
        assert len(items) == 1
        assert items[0]["asset"] == "N/A"


def test_get_aggregated_weekend_data_missing_asset(aggregator):
    """Test weekend aggregation when MOs have no asset (PM and Tickets)."""
    with patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO:
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        mock_col.__lt__ = MagicMock(return_value=MagicMock())
        MockMO.due_date = mock_col
        # We need two queries: PMs and Other MOs.
        # MockMO.query.filter....all() is called twice.

        mock_pm = MagicMock()
        mock_pm.asset = None
        mock_pm.description = "PM Desc"

        mock_mo = MagicMock()
        mock_mo.asset = None
        mock_mo.description = "MO Desc"
        mock_mo.id = 99

        # Side effect for two calls
        MockMO.query.filter.return_value.all.side_effect = [[mock_pm], [mock_mo]]

        # Mock datetime in the module to return Mocks
        with patch(
            "apps.reports.src.services.data_aggregator.datetime"
        ) as mock_datetime:
            mock_dt = MagicMock()
            mock_datetime.strptime.return_value.replace.return_value = mock_dt

            with patch("apps.reports.src.services.data_aggregator.timedelta"):
                data = aggregator.get_aggregated_weekend_data("2023-10-28")  # Saturday

        assert data["pms"][0]["asset"] == "N/A"
        assert data["mos_tickets"][0]["asset"] == "N/A"


def test_get_weekend_tasks(aggregator):
    """Test get_weekend_tasks querying."""
    with patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO:
        # Configuration for comparisons on due_date
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__lt__ = MagicMock(return_value=MagicMock())
        MockMO.due_date = mock_col

        # Let's mock datetime completely to avoid complexity
        with patch("apps.reports.src.services.data_aggregator.datetime") as mock_dt_cls:
            mock_start_dt = MagicMock()
            mock_start_dt.__ge__ = MagicMock(return_value=True)
            mock_start_dt.__le__ = MagicMock(return_value=True)

            mock_end_dt = MagicMock()
            mock_end_dt.__ge__ = MagicMock(return_value=True)
            mock_end_dt.__le__ = MagicMock(return_value=True)

            # Setup chain: datetime.strptime(...).replace(...)
            mock_dt_cls.strptime.return_value.replace.side_effect = [
                mock_start_dt,
                mock_end_dt,
            ]
            # Also timedelta
            with patch("apps.reports.src.services.data_aggregator.timedelta"):
                # Setup filter return
                mock_task = MagicMock()
                mock_task.to_dict.return_value = {
                    "id": 1,
                    "description": "Weekend Task",
                }
                MockMO.query.filter.return_value.all.return_value = [mock_task]

                results = aggregator.get_weekend_tasks("2023-10-28", "2023-10-29")

                assert len(results) == 1
                assert results[0]["description"] == "Weekend Task"
                # Verify filter call used our mocks
                assert MockMO.query.filter.called


def test_get_shift_data(aggregator):
    """Test get_shift_data querying."""
    with (
        patch("apps.reports.src.services.data_aggregator.ShiftUtils") as MockUtils,
        patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO,
    ):
        # Configuration for comparisons on created_at
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__lt__ = MagicMock(return_value=MagicMock())
        MockMO.created_at = mock_col

        # Mock ShiftUtils
        mock_start = MagicMock()
        mock_end = MagicMock()
        MockUtils.return_value.get_shift_window.return_value = (mock_start, mock_end)

        # Mock query result
        mock_task = MagicMock()
        mock_task.to_dict.return_value = {"id": 1, "shift": "Early"}
        MockMO.query.filter.return_value.all.return_value = [mock_task]

        # Call the method
        results = aggregator.get_shift_data("2023-01-01", "Early")

        # Assertions
        assert len(results) == 1
        assert results[0]["shift"] == "Early"
        MockUtils.return_value.get_shift_window.assert_called_once()
        # Ensure filter called with mocked start/end
        args, _ = MockMO.query.filter.call_args
        # args contains the sqlalchemy expressions.
        # We cannot easily check exact expressions on args without complex matching.
        # We know __ge__ and __lt__ were called on created_at because we mocked them.
        MockMO.created_at.__ge__.assert_called_with(mock_start)
        MockMO.created_at.__lt__.assert_called_with(mock_end)
