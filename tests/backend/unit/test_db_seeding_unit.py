import logging
from unittest.mock import MagicMock, patch

from src.services.db_seeding import (
    _assign_technician_teams,
    _create_maintenance_orders,
    _get_or_create,
    populate_dummy_data,
)
from src.services.db_utils import Asset, MaintenanceOrder, Role, Skill, Team, User, db


class TestDBSeeding:
    """Consolidated tests for database seeding logic."""

    def test_populate_dummy_data_success(self, app):
        """Test full population of dummy data."""
        with app.app_context():
            logger = logging.getLogger("test_seeding")
            populate_dummy_data(logger)

            # Verify data exists
            assert Role.query.count() > 0
            assert User.query.count() > 0
            assert Asset.query.count() > 0

    def test_populate_idempotency(self, app):
        """Test that populate doesn't duplicate if run twice."""
        with app.app_context():
            logger = logging.getLogger("test_seeding_idem")
            populate_dummy_data(logger)
            c1 = User.query.count()

            # Run again
            populate_dummy_data(logger)
            c2 = User.query.count()

            assert c1 == c2

    def test_load_dummy_data_graceful_error(self, app):
        """Test handling of missing dummy data file (graceful skip)."""
        with app.app_context():
            with patch("builtins.open", side_effect=FileNotFoundError):
                # Ensure DB is empty to force load attempt
                Role.query.delete()
                User.query.delete()
                db.session.commit()

                mock_logger = MagicMock()
                populate_dummy_data(mock_logger)
                # Verify logger was called on error but didn't crash
                assert mock_logger.error.called

    def test_get_or_create_existing(self, app):
        """Test _get_or_create returns existing instance."""
        with app.app_context():
            role = Role(name="ExistingRole")
            db.session.add(role)
            db.session.commit()

            instance, created = _get_or_create(Role, name="ExistingRole")
            assert instance.id == role.id
            assert created is False

    def test_create_maintenance_orders_logic(self, app):
        """Test specific logic for mapping assets and skills in MO seeding."""
        with app.app_context():
            asset = Asset(name="SeedingAsset", asset_code="SA-001")
            db.session.add(asset)
            skill = Skill(name="SeedingSkill")
            db.session.add(skill)
            db.session.commit()

            orders_data = [
                {
                    "asset": "SeedingAsset",
                    "description": "Seeding Test MO",
                    "required_skills": ["SeedingSkill"],
                    "due_days_from_now": 2,
                    "order_type": "PM",
                    "status": "Open",
                    "priority": "Medium",
                }
            ]

            _create_maintenance_orders(
                orders_data,
                {"SeedingAsset": asset},
                {"SeedingSkill": skill},
                MagicMock(),
            )
            mo = MaintenanceOrder.query.filter_by(description="Seeding Test MO").first()
            assert mo is not None
            assert len(mo.required_skills) == 1

    def test_assign_technician_teams_logic(self, app):
        """Test logic for complex technician skill/team assignment."""
        with app.app_context():
            user = User(username="TechSeeding", email="tech@seeding.com")
            user.set_password("pass")
            team = Team(name="SeedingTeam")
            db.session.add_all([user, team])
            db.session.commit()

            tech_data = [
                {
                    "name": "TechSeeding",
                    "shift_team": "SeedingTeam",
                    "skills": [{"skill": "SkillX", "level": 4}],
                }
            ]

            _assign_technician_teams(tech_data, MagicMock())
            db.session.refresh(user)
            assert user.team.name == "SeedingTeam"
            assert user.skills[0].skill.name == "SkillX"
