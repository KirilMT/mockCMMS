from datetime import datetime, timedelta

from apps.reports.src.services.data_aggregator import DataAggregator
from src.services.db_utils import Asset, MaintenanceOrder, db


class TestReportsDataAggregatorIntegration:
    def test_get_aggregated_shift_data_integration(self, app, db_session):
        # Create a test asset first (required foreign key)
        test_asset = Asset(name="Test Asset", asset_code="TEST001")
        db.session.add(test_asset)
        db.session.flush()  # Get the ID
        now = datetime.now()
        start = now.replace(hour=6, minute=0, second=0)
        # Breakdown (Reactive)
        breakdown = MaintenanceOrder(
            asset_id=test_asset.id,
            description="Belt snapped - Broken Belt",
            order_type="Reactive",
            priority="High",
            status="In Progress",
            created_at=start + timedelta(hours=1),  # Inside shift
        )
        db.session.add(breakdown)
        # Completed Activity (PM or anything completed)
        activity = MaintenanceOrder(
            asset_id=test_asset.id,
            description="Cleaned sensor - Clean Sensor",
            order_type="PM",
            status="Completed",
            due_date=start + timedelta(hours=2),  # Inside shift
        )
        db.session.add(activity)
        db.session.commit()
        aggregator = DataAggregator()
        data = aggregator.get_aggregated_shift_data(now.strftime("%Y-%m-%d"), "Early")
        assert "breakdowns" in data
        assert len(data["breakdowns"]) >= 1
        assert "break_activities" in data
