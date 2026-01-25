from unittest.mock import patch

from src.services.db_seeding import _get_or_create, populate_dummy_data
from src.services.db_utils import Asset, MaintenanceOrder, Role, Skill, Team, User, db


class TestDBSeedingExtended:
    """Extended tests for db_seeding.py coverage."""

    def test_load_dummy_data_file_not_found(self, app):
        """Test handling of missing dummy data file."""
        with app.app_context():
            # Mock logger to verify error logging
            with patch(
                "src.services.db_seeding._load_dummy_data",
                side_effect=FileNotFoundError,
            ):
                # We can't easily mock the internal call inside populate_dummy_data
                # without mocking the whole function
                # But we can test _load_dummy_data directly if we import it,
                # or mock open
                pass

            # Better approach: Mock existing check to force load attempt, and mock
            # open to raise FileNotFoundError
            with patch("builtins.open", side_effect=FileNotFoundError):
                # Ensure DB is empty so it tries to load
                Role.query.delete()
                User.query.delete()
                db.session.commit()

                # Capture logger?
                # Use proper mock
                from unittest.mock import Mock

                mock_logger = Mock()
                populate_dummy_data(mock_logger)
                # Verify it handled it gracefully (no crash)

    def test_get_or_create_existing(self, app):
        """Test _get_or_create returns existing instance."""
        with app.app_context():
            role = Role(name="TestRole")
            db.session.add(role)
            db.session.commit()

            instance, created = _get_or_create(Role, name="TestRole")
            assert instance.id == role.id
            assert created is False

    def test_create_maintenance_orders_logic(self, app):
        """Test specific logic in maintenance order creation."""
        with app.app_context():
            # Setup dependencies
            asset = Asset(name="TestAsset", asset_code="TA-001")
            db.session.add(asset)
            skill = Skill(name="Welding")
            db.session.add(skill)
            db.session.commit()

            assets_map = {"TestAsset": asset}
            skills_map = {"Welding": skill}

            # Mock data with required skills
            orders_data = [
                {
                    "asset": "TestAsset",
                    "description": "Test MO",
                    "required_skills": ["Welding"],
                    "due_days_from_now": 5,
                    "order_type": "PM",
                    "status": "Open",
                    "priority": "High",
                }
            ]

            from src.services.db_seeding import _create_maintenance_orders

            # We need a mock logger
            with patch("logging.getLogger") as mock_get_logger:
                logger = mock_get_logger()
                _create_maintenance_orders(orders_data, assets_map, skills_map, logger)

            mo = MaintenanceOrder.query.filter_by(description="Test MO").first()
            assert mo is not None
            assert mo.due_date is not None
            assert len(mo.required_skills) == 1
            assert mo.required_skills[0].name == "Welding"

    def test_assign_technician_teams_logic(self, app):
        """Test logic for assigning teams and skills to technicians."""
        with app.app_context():
            # Create user and team
            user = User(username="TechUser", email="tech@test.com")
            user.set_password("password123")
            team = Team(name="Shift A")
            db.session.add(user)
            db.session.add(team)
            db.session.commit()

            tech_data = [
                {
                    "name": "TechUser",
                    "shift_team": "Shift A",
                    "skills": [{"skill": "Electrical", "level": 3}],
                }
            ]

            from src.services.db_seeding import _assign_technician_teams

            with patch("logging.getLogger") as mock_get_logger:
                logger = mock_get_logger()
                _assign_technician_teams(tech_data, logger)

            db.session.refresh(user)
            assert user.team.name == "Shift A"
            assert len(user.skills) == 1
            assert user.skills[0].skill.name == "Electrical"
