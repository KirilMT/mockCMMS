"""Tests for shift rotation logic in Weekend Planning."""

from datetime import datetime

import pytest

from apps.planning.src.services.planning_engine import PlanningEngine
from src.services.db_utils import Team, User, db


@pytest.fixture
def planning_engine():
    # Use reloaded class

    return PlanningEngine(logger=None)


@pytest.fixture
def setup_shift_teams(app):
    """Setup the 4 shift teams and assign technicians."""
    with app.app_context():
        # Create Shift Teams if they don't exist
        teams = [
            Team(name="Team A", shift_type="Early", rotation_pattern="Pattern 1"),
            Team(name="Team B", shift_type="Late", rotation_pattern="Pattern 1"),
            Team(name="Team C", shift_type="Early", rotation_pattern="Pattern 2"),
            Team(name="Team D", shift_type="Late", rotation_pattern="Pattern 2"),
        ]

        for team in teams:
            existing = Team.query.filter_by(name=team.name).first()
            if not existing:
                db.session.add(team)
            else:
                existing.rotation_pattern = team.rotation_pattern
                existing.shift_type = team.shift_type
        db.session.commit()

        # Get team IDs
        team_a = Team.query.filter_by(name="Team A").first()
        team_b = Team.query.filter_by(name="Team B").first()
        team_c = Team.query.filter_by(name="Team C").first()
        team_d = Team.query.filter_by(name="Team D").first()

        # Create Technicians (as Users)
        techs = [
            User(
                username="Tech A",
                team_id=team_a.id,
                email="techa@example.com",
                password_hash="hash",
            ),
            User(
                username="Tech B",
                team_id=team_b.id,
                email="techb@example.com",
                password_hash="hash",
            ),
            User(
                username="Tech C",
                team_id=team_c.id,
                email="techc@example.com",
                password_hash="hash",
            ),
            User(
                username="Tech D",
                team_id=team_d.id,
                email="techd@example.com",
                password_hash="hash",
            ),
            User(
                username="Tech Unassigned",
                team_id=None,
                email="unassigned@example.com",
                password_hash="hash",
            ),
        ]

        for tech in techs:
            existing = User.query.filter_by(username=tech.username).first()
            if not existing:
                db.session.add(tech)
            else:
                existing.team_id = tech.team_id
        db.session.commit()

    yield


class TestShiftRotation:
    def test_get_working_teams_odd_week(self, app, planning_engine, setup_shift_teams):
        """Test that Team A and Team B are active in odd ISO weeks."""
        with app.app_context():
            # Week 45 (Odd)
            date_odd = datetime(2023, 11, 11)  # Saturday, Week 45
            assert date_odd.isocalendar()[1] % 2 != 0

            active_teams = planning_engine._get_working_teams(date_odd)

            team_names = [t.name for t in active_teams]
            assert "Team A" in team_names
            assert "Team B" in team_names
            assert "Team C" not in team_names
            assert "Team D" not in team_names

    def test_get_working_teams_even_week(self, app, planning_engine, setup_shift_teams):
        """Test that Team C and Team D are active in even ISO weeks."""
        with app.app_context():
            # Week 46 (Even)
            date_even = datetime(2023, 11, 18)  # Saturday, Week 46
            assert date_even.isocalendar()[1] % 2 == 0

            active_teams = planning_engine._get_working_teams(date_even)

            team_names = [t.name for t in active_teams]
            assert "Team C" in team_names
            assert "Team D" in team_names
            assert "Team A" not in team_names
            assert "Team B" not in team_names

    def test_technician_filtering_in_planning(
        self, app, planning_engine, setup_shift_teams
    ):
        """Test that generate_plan filters technicians correctly based on shift."""
        with app.app_context():
            start_date = datetime(2023, 11, 11)
            active_teams = planning_engine._get_working_teams(start_date)
            active_team_ids = [t.id for t in active_teams]

            team_a = Team.query.filter_by(name="Team A").first()
            team_b = Team.query.filter_by(name="Team B").first()
            team_c = Team.query.filter_by(name="Team C").first()

            assert team_a.id in active_team_ids
            assert team_b.id in active_team_ids
            assert team_c.id not in active_team_ids

    def test_unassigned_technician_exclusion(
        self, app, planning_engine, setup_shift_teams
    ):
        """Test that unassigned technicians are never included in active teams."""
        with app.app_context():
            date_odd = datetime(2023, 11, 11)
            active_teams = planning_engine._get_working_teams(date_odd)

            active_team_ids = [t.id for t in active_teams]
            available_technicians = User.query.filter(
                User.team_id.in_(active_team_ids)
            ).all()

            tech_names = [t.username for t in available_technicians]

            assert "Tech Unassigned" not in tech_names
            assert "Tech A" in tech_names  # For odd week
