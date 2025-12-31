"""Unit tests for Data Simulation Service."""

from src.services.db_utils import Asset, MaintenanceOrder, User, db
from src.services.simulation_service import DataSimulationService


class TestDataSimulationService:
    """Test suite for DataSimulationService."""

    def test_generate_random_assets(self, app):
        """Test generation of random assets."""
        with app.app_context():
            initial_count = Asset.query.count()
            generated = DataSimulationService.generate_random_assets(count=5)

            assert len(generated) == 5
            assert Asset.query.count() == initial_count + 5

            for asset in generated:
                assert asset.id is not None
                assert asset.asset_code.startswith(
                    ("PUMP", "MOTOR", "CONV", "ROBOT", "PRESS", "DRILL")
                )
                assert asset.status in [
                    "Operational",
                    "Under Maintenance",
                    "Offline",
                    "Retired",
                    "Down",
                ]

    def test_generate_random_users(self, app):
        """Test generation of random users with dynamic roles."""
        with app.app_context():
            initial_count = User.query.count()
            generated = DataSimulationService.generate_random_users(count=3)

            assert len(generated) == 3
            assert User.query.count() == initial_count + 3

            for user in generated:
                assert user.id is not None
                assert user.username.startswith("user_")
                assert len(user.roles) >= 1
                assert user.team is not None
                assert user.availability_status is not None

    def test_generate_random_orders(self, app):
        """Test generation of random maintenance orders."""
        with app.app_context():
            # Ensure we have assets first
            DataSimulationService.generate_random_assets(count=3)

            initial_count = MaintenanceOrder.query.count()
            generated = DataSimulationService.generate_random_orders(count=5)

            assert len(generated) == 5
            assert MaintenanceOrder.query.count() == initial_count + 5

            allowed_types = [
                "PM",
                "PM (Preventive Maintenance)",
                "Reactive",
                "Corrective",
            ]

            for mo in generated:
                assert mo.id is not None
                assert mo.order_type in allowed_types
                assert mo.asset_id is not None
                assert mo.justification is not None
                # Check for populated fields
                if mo.order_type == "PM":
                    assert mo.schedule_name is not None

    def test_generate_random_spare_parts(self, app):
        """Test generation of random spare parts."""
        with app.app_context():
            from src.services.db_utils import SparePart

            initial_count = SparePart.query.count()
            generated = DataSimulationService.generate_random_spare_parts(count=5)

            assert len(generated) == 5
            assert SparePart.query.count() == initial_count + 5

            for part in generated:
                assert part.id is not None
                assert part.description.startswith("Simulated Spare Part")
                assert part.manufacturer is not None
                assert part.location is not None

    def test_generate_random_orders_no_assets(self, app):
        """Test generation of orders when no assets exist."""
        with app.app_context():
            # Clear all assets
            MaintenanceOrder.query.delete()
            Asset.query.delete()
            db.session.commit()

            generated = DataSimulationService.generate_random_orders(count=5)
            assert len(generated) == 0
