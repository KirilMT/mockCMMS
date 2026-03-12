"""Comprehensive tests for DataAggregator service - MAXIMIZE COVERAGE."""

from datetime import datetime, timezone

from apps.reporting.src.services.data_aggregator import DataAggregator
from src.services.db_utils import Asset, MaintenanceOrder, db


class TestDataAggregatorWithRealDB:
    """Test DataAggregator with real database (app fixture provides DB)."""

    def test_get_shift_incidents_with_reactive_mo(self, app):
        """Test _get_shift_incidents retrieves Completed Reactive MOs."""
        with app.app_context():
            # Create test data
            asset = Asset(name="Line 1", asset_code="AST-001")
            db.session.add(asset)
            db.session.flush()

            mo = MaintenanceOrder(
                description="Test breakdown",
                order_type="Reactive",
                priority="High",
                status="Completed",  # Must be Completed to appear in breakdowns
                asset_id=asset.id,
                # Use naive datetime - SQLite stores without timezone
                created_at=datetime(2026, 2, 8, 10, 30),
            )
            db.session.add(mo)
            db.session.commit()

            aggregator = DataAggregator()
            start = datetime(2026, 2, 8, 8, 0, tzinfo=timezone.utc)
            end = datetime(2026, 2, 8, 16, 0, tzinfo=timezone.utc)

            incidents = aggregator._get_shift_incidents(start, end)

            assert len(incidents) >= 1
            found = False
            for inc in incidents:
                if inc["id"] == mo.id:
                    assert inc["asset_code"] == "AST-001"
                    assert inc["description"] == "Test breakdown"
                    found = True
            assert found

    def test_get_shift_incidents_no_asset(self, app):
        """Test _get_shift_incidents handles Completed MO with minimal asset info."""
        with app.app_context():
            # Asset_id is NOT NULL, so create minimal asset
            asset = Asset(name="Unknown Asset", asset_code="UNK-000")
            db.session.add(asset)
            db.session.flush()

            mo = MaintenanceOrder(
                description="Test without full asset details",
                order_type="Reactive",
                priority="Medium",
                status="Completed",  # Must be Completed to appear in breakdowns
                asset_id=asset.id,
                # Use naive datetime - SQLite stores without timezone
                created_at=datetime(2026, 2, 8, 11, 0),
            )
            db.session.add(mo)
            db.session.commit()

            aggregator = DataAggregator()
            start = datetime(2026, 2, 8, 8, 0, tzinfo=timezone.utc)
            end = datetime(2026, 2, 8, 16, 0, tzinfo=timezone.utc)

            incidents = aggregator._get_shift_incidents(start, end)

            found = False
            for inc in incidents:
                if inc["id"] == mo.id:
                    assert inc["asset_code"] == "UNK-000"
                    found = True
            assert found

    def test_get_shift_data_returns_list(self, app):
        """Test get_shift_data returns a list."""
        with app.app_context():
            aggregator = DataAggregator()
            result = aggregator.get_shift_data("2026-02-08", "Day")
            assert isinstance(result, list)

    def test_get_aggregated_shift_data_structure(self, app):
        """Test get_aggregated_shift_data returns proper dict structure."""
        with app.app_context():
            aggregator = DataAggregator()
            data = aggregator.get_aggregated_shift_data("2026-02-08", "Day")

            assert isinstance(data, dict)
            assert "shift_info" in data or "breakdowns" in data

    def test_get_weekend_tasks_in_range(self, app):
        """Test get_weekend_tasks retrieves tasks in date range."""
        with app.app_context():
            asset = Asset(name="Machine B", asset_code="AST-100")
            db.session.add(asset)
            db.session.flush()

            mo = MaintenanceOrder(
                description="Preventive maintenance",
                order_type="Preventive",
                priority="Medium",
                status="Scheduled",
                asset_id=asset.id,
                due_date=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
            )
            db.session.add(mo)
            db.session.commit()
            mo_id = mo.id

            aggregator = DataAggregator()
            tasks = aggregator.get_weekend_tasks("2026-02-08", "2026-02-09")

            # tasks might be list of dicts or objects
            found = False
            for task in tasks:
                task_id = task.get("id") if isinstance(task, dict) else task.id
                if task_id == mo_id:
                    found = True
            assert found

    def test_get_weekend_tasks_empty_range(self, app):
        """Test get_weekend_tasks with no tasks in range."""
        with app.app_context():
            aggregator = DataAggregator()
            # Future date with no tasks
            tasks = aggregator.get_weekend_tasks("2030-01-01", "2030-01-02")
            assert isinstance(tasks, list)

    def test_get_aggregated_weekend_data_structure(self, app):
        """Test get_aggregated_weekend_data returns dict."""
        with app.app_context():
            aggregator = DataAggregator()
            data = aggregator.get_aggregated_weekend_data("2026-02-08")
            assert isinstance(data, dict)

    def test_get_shift_incidents_multiple_mos(self, app):
        """Test _get_shift_incidents only returns Completed Reactive MOs."""
        with app.app_context():
            asset1 = Asset(name="Line X", asset_code="AST-X")
            asset2 = Asset(name="Line Y", asset_code="AST-Y")
            db.session.add_all([asset1, asset2])
            db.session.flush()

            mo1 = MaintenanceOrder(
                description="First breakdown",
                order_type="Reactive",
                priority="High",
                status="Completed",  # Completed Reactive → appears in breakdowns
                asset_id=asset1.id,
                # Use naive datetime - SQLite stores without timezone
                created_at=datetime(2026, 2, 9, 10, 0),
            )
            mo2 = MaintenanceOrder(
                description="Second breakdown",
                order_type="Corrective",
                priority="Medium",
                status="In Progress",  # Non-Reactive and non-Completed → excluded
                asset_id=asset2.id,
                created_at=datetime(2026, 2, 9, 12, 0),
            )
            db.session.add_all([mo1, mo2])
            db.session.commit()

            aggregator = DataAggregator()
            start = datetime(2026, 2, 9, 8, 0, tzinfo=timezone.utc)
            end = datetime(2026, 2, 9, 16, 0, tzinfo=timezone.utc)

            incidents = aggregator._get_shift_incidents(start, end)

            ids_found = [inc["id"] for inc in incidents]
            assert mo1.id in ids_found
            assert mo2.id not in ids_found

    def test_data_aggregator_initialization(self, app):
        """Test DataAggregator can be instantiated."""
        with app.app_context():
            aggregator = DataAggregator()
            assert aggregator is not None
