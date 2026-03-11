"""Unit tests for Data Simulation Service."""

from src.services.db_utils import Asset, MaintenanceOrder, Role, Team, User, db
from src.services.simulation_service import DataSimulationService


class TestDataSimulationService:
    """Test suite for DataSimulationService, covering data generation and complex
    assignment logic."""

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

    def test_generate_random_orders_basic(self, app):
        """Test basic generation of random maintenance orders."""
        with app.app_context():
            DataSimulationService.generate_random_assets(count=3)
            initial_count = MaintenanceOrder.query.count()
            generated = DataSimulationService.generate_random_orders(count=5)

            assert len(generated) == 5
            assert MaintenanceOrder.query.count() == initial_count + 5

            for mo in generated:
                assert mo.id is not None
                assert mo.asset_id is not None
                if mo.order_type == "PM":
                    assert mo.schedule_name is not None

    def test_generate_random_orders_full_team_assignment(self, app):
        """Test the logic where every 100th order gets a full team assigned."""
        with app.app_context():
            # Setup: Create Team with multiple users
            team = Team(name="FullAssignmentTeam")
            db.session.add(team)
            for i in range(5):
                u = User(username=f"team_u_{i}", email=f"team_u{i}@test.com")
                u.set_password("pass")
                u.team = team
                db.session.add(u)
            asset = Asset(name="SimAsset", asset_code="SIM-001")
            db.session.add(asset)
            db.session.commit()

            # Generate 100 orders to hit the modulo 100 branch
            generated = DataSimulationService.generate_random_orders(count=100)
            assert len(generated) == 100
            target_mo = generated[99]
            assert isinstance(target_mo.assignees, list)

    def test_generate_random_orders_with_technicians(self, app):
        """Test generating orders where technicians are selectively assigned."""
        with app.app_context():
            tech_role = Role(name="Technician")
            db.session.add(tech_role)
            for i in range(3):
                u = User(username=f"tech_sim_{i}", email=f"tech_sim{i}@test.com")
                u.set_password("pass")
                u.roles.append(tech_role)
                db.session.add(u)
            asset = Asset(name="TechAsset", asset_code="TECH-001")
            db.session.add(asset)
            db.session.commit()

            generated = DataSimulationService.generate_random_orders(count=5)
            for mo in generated:
                if mo.assignees:
                    assert 1 <= len(mo.assignees) <= 3

    def test_generate_random_spare_parts(self, app):
        """Test generation of random spare parts."""
        with app.app_context():
            # Import locally to avoid issues with potential mocks
            from src.services.db_utils import SparePart

            initial_count = SparePart.query.count()
            generated = DataSimulationService.generate_random_spare_parts(count=5)

            assert len(generated) == 5
            assert SparePart.query.count() == initial_count + 5

    def test_generate_random_orders_no_assets(self, app):
        """Test generation of orders when no assets exist (should return empty)."""
        with app.app_context():
            MaintenanceOrder.query.delete()
            Asset.query.delete()
            db.session.commit()

            generated = DataSimulationService.generate_random_orders(count=5)
            assert len(generated) == 0
