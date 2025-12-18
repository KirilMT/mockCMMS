"""Unit tests for Data Simulation Service."""

import pytest
from src.services.simulation_service import DataSimulationService
from src.services.db_utils import Asset, User, MaintenanceOrder, Role, Team, db

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
                assert asset.asset_code.startswith(("PUMP", "MOTOR", "CONV", "ROBOT", "PRESS", "DRILL"))
                assert asset.status in ["Operational", "Under Maintenance", "Offline"]

    def test_generate_random_technicians(self, app):
        """Test generation of random technicians."""
        with app.app_context():
            initial_count = User.query.count()
            generated = DataSimulationService.generate_random_technicians(count=3)

            assert len(generated) == 3
            assert User.query.count() == initial_count + 3

            tech_role = Role.query.filter_by(name="Technician").first()
            assert tech_role is not None

            for user in generated:
                assert user.id is not None
                assert user.username.startswith("tech_")
                assert tech_role in user.roles
                assert user.team is not None

    def test_generate_random_orders(self, app):
        """Test generation of random maintenance orders."""
        with app.app_context():
            # Ensure we have assets first
            DataSimulationService.generate_random_assets(count=3)

            initial_count = MaintenanceOrder.query.count()
            generated = DataSimulationService.generate_random_orders(count=5)

            assert len(generated) == 5
            assert MaintenanceOrder.query.count() == initial_count + 5

            for mo in generated:
                assert mo.id is not None
                assert mo.order_type in DataSimulationService.MO_TYPES
                assert mo.priority in DataSimulationService.MO_PRIORITIES
                assert mo.asset_id is not None

    def test_generate_random_orders_no_assets(self, app):
        """Test generation of orders when no assets exist."""
        with app.app_context():
            # Clear all assets
            MaintenanceOrder.query.delete()
            Asset.query.delete()
            db.session.commit()

            generated = DataSimulationService.generate_random_orders(count=5)
            assert len(generated) == 0
