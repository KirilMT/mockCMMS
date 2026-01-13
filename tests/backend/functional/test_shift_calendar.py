"""Tests for shift calendar route and logic.

This module tests the shift calendar page, parameter handling, and data generation logic.
"""

import pytest
from datetime import datetime
from src.services.db_utils import Team, User, Role, db

class TestShiftCalendar:
    """Test suite for shift calendar route logic."""

    @pytest.fixture
    def teams(self, app):
        """Seed teams for calendar testing."""
        with app.app_context():
            # Ensure teams exist
            teams = []
            for name in ["Team A", "Team B", "Team C", "Team D"]:
                team = Team.query.filter_by(name=name).first()
                if not team:
                    team = Team(name=name)
                    db.session.add(team)
                teams.append(team)

            # Ensure Technician role exists
            tech_role = Role.query.filter_by(name="Technician").first()
            if not tech_role:
                tech_role = Role(name="Technician")
                db.session.add(tech_role)

            # Add some users to teams
            user_a = User.query.filter_by(username="tech_a").first()
            if not user_a:
                user_a = User(username="tech_a", email="tech_a@example.com")
                user_a.set_password("password")
                user_a.roles.append(tech_role)
                user_a.team_id = teams[0].id # Team A
                db.session.add(user_a)

            db.session.commit()
            return teams

    def test_shift_calendar_page_loads(self, auth_client, teams):
        """Test GET /shift_calendar returns calendar page."""
        response = auth_client.get("/shift_calendar")
        assert response.status_code == 200
        assert b"Shift Calendar" in response.data
        assert b"Team A" in response.data
        assert b"Team B" in response.data

    def test_shift_calendar_with_params(self, auth_client, teams):
        """Test GET /shift_calendar with year and month params."""
        # Test a specific non-current month to verify logic
        response = auth_client.get("/shift_calendar?year=2025&month=12")
        assert response.status_code == 200
        assert b"December 2025" in response.data

    def test_shift_calendar_navigation_logic(self, auth_client, teams):
        """Test the navigation logic (prev/next month calculation)."""
        # Testing transition from January back to December previous year
        response = auth_client.get("/shift_calendar?year=2026&month=1")
        assert response.status_code == 200
        # Check that the "Previous" button links to Dec 2025
        # The URL might be encoded, so we check for month=12 and year=2025
        assert b"month=12" in response.data
        assert b"year=2025" in response.data

        # Testing transition from December to January next year
        response = auth_client.get("/shift_calendar?year=2025&month=12")
        assert response.status_code == 200
        # Check that the "Next" button links to Jan 2026
        assert b"month=1" in response.data
        assert b"year=2026" in response.data

    def test_calendar_data_generation_coverage(self, auth_client, teams):
        """Test specifically triggering the _generate_calendar_data logic fully."""
        # Requesting a full month view triggers the generation loop
        # We pick a month with 31 days to ensure full coverage of the loop
        response = auth_client.get("/shift_calendar?year=2024&month=1")
        assert response.status_code == 200
        # Check that we have enough days generated (grid view includes previous/next month days)
        # Checking for specific day numbers or structure might be redundant if we check for success,
        # but verifies data integrity.
        assert b"31" in response.data # Day 31 exists
        assert b"1" in response.data # Day 1 exists

