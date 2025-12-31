"""Tests for shift utilities (shift_utils.py).

This module tests the shift calculation and rotation logic for the 2-2-3 Rotating
Schedule (Pitman Schedule) implementation.
"""

from datetime import datetime

import pytest

from src.services.db_utils import Team, db
from src.services.shift_utils import get_shift_teams


class TestShiftUtilities:
    """Test shift calculation and rotation logic."""

    @pytest.fixture
    def teams(self, app):
        """Create test teams for shift calculations."""
        with app.app_context():
            # Create 4 teams (A, B, C, D) as required by Pitman schedule
            team_a = Team(name="Team A")
            team_b = Team(name="Team B")
            team_c = Team(name="Team C")
            team_d = Team(name="Team D")

            db.session.add_all([team_a, team_b, team_c, team_d])
            db.session.commit()

            yield [team_a, team_b, team_c, team_d]

    def test_get_shift_teams_shift_a(self, app, teams):
        """Test that Team A is correctly assigned on a day when Team A should work.

        Uses a specific date known to be Team A's day based on the Pitman schedule. Week
        1 (Odd), Monday should have Group 1 (Teams A & B).
        """
        with app.app_context():
            # January 1, 2024 is Monday, Week 1 (Odd week)
            # Group 1 day (Mon in odd week)
            # rotation_idx = (1-1)//2 = 0 (even)
            # Expected: Early=Team B, Late=Team A
            test_date = datetime(2024, 1, 1)

            early, late = get_shift_teams(test_date, teams)

            assert early is not None, "Early shift should be assigned"
            assert late is not None, "Late shift should be assigned"

            # For odd week Monday, rotation_idx=0 (even), so B early, A late
            assert (
                early.name == "Team B"
            ), f"Expected Team B for early shift, got {early.name}"
            assert (
                late.name == "Team A"
            ), f"Expected Team A for late shift, got {late.name}"

    def test_get_shift_teams_shift_b(self, app, teams):
        """Test that Team B is correctly assigned on a day when Team B should work.

        Uses a specific date known to be Team B's day based on the Pitman schedule.
        """
        with app.app_context():
            # January 8, 2024 is Monday, Week 2 (Even week)
            # Group 1 day: NO (Mon in even week is Group 2 day)
            # Actually, let's use Wed, Jan 3, 2024 (Week 1, odd)
            # Wed in odd week = Group 2 day
            # rotation_idx = 1//2 = 0 (even)
            # Expected: Early=Team C, Late=Team D

            # Let's use a date that gives us Team B
            # Week 2 (even), Wednesday = Group 1 day
            # January 10, 2024 is Wednesday, Week 2 (even)
            test_date = datetime(2024, 1, 10)

            early, late = get_shift_teams(test_date, teams)

            assert early is not None, "Early shift should be assigned"
            assert late is not None, "Late shift should be assigned"

            # Week 2 (even), Wednesday = Group 1 day
            # rotation_idx = (2-1)//2 = 0 (even)
            # Expected: Early=Team B, Late=Team A
            assert (
                early.name == "Team B"
            ), f"Expected Team B for early shift, got {early.name}"

    def test_get_shift_teams_shift_c(self, app, teams):
        """Test that Team C is correctly assigned on a day when Team C should work.

        Uses a specific date known to be Team C's day based on the Pitman schedule.
        """
        with app.app_context():
            # January 3, 2024 is Wednesday, Week 1 (Odd week)
            # Wed in odd week = Group 2 day
            # rotation_idx = 1//2 = 0 (even)
            # Expected: Early=Team C, Late=Team D
            test_date = datetime(2024, 1, 3)

            early, late = get_shift_teams(test_date, teams)

            assert early is not None, "Early shift should be assigned"
            assert late is not None, "Late shift should be assigned"

            # Week 1 (odd), Wednesday = Group 2 day
            # rotation_idx = 1//2 = 0 (even)
            # Expected: Early=Team C, Late=Team D
            assert (
                early.name == "Team C"
            ), f"Expected Team C for early shift, got {early.name}"
            assert (
                late.name == "Team D"
            ), f"Expected Team D for late shift, got {late.name}"

    def test_get_shift_teams_rotation_cycle(self, app, teams):
        """Test that shift rotation works correctly over multiple consecutive dates.

        Verifies the Pitman schedule rotation pattern across different weeks.
        """
        with app.app_context():
            # Test a sequence of dates to verify rotation pattern
            # Calculations based on actual shift_utils.py logic:
            # Week 1: odd, rotation_idx for G1=(1-1)//2=0, for G2=1//2=0
            # Week 2: even, rotation_idx for G1=(2-1)//2=0, for G2=2//2=1
            # Week 3: odd, rotation_idx for G1=(3-1)//2=1, for G2=3//2=1
            test_dates = [
                # Week 1, Mon (odd): G1 day, idx=0 -> B early, A late
                (datetime(2024, 1, 1), "Team B", "Team A"),
                # Week 1, Wed (odd): G2 day, idx=0 -> C early, D late
                (datetime(2024, 1, 3), "Team C", "Team D"),
                # Week 2, Mon (even): G2 day, idx=1 -> D early, C late
                (datetime(2024, 1, 8), "Team D", "Team C"),
                # Week 2, Wed (even): G1 day, idx=0 -> B early, A late
                (datetime(2024, 1, 10), "Team B", "Team A"),
                # Week 3, Mon (odd): G1 day, idx=1 -> A early, B late
                (datetime(2024, 1, 15), "Team A", "Team B"),
            ]

            for test_date, expected_early, expected_late in test_dates:
                early, late = get_shift_teams(test_date, teams)

                assert (
                    early is not None
                ), f"Early shift should be assigned for {test_date}"
                assert (
                    late is not None
                ), f"Late shift should be assigned for {test_date}"

                assert early.name == expected_early, (
                    f"Date {test_date}: Expected {expected_early} for "
                    f"early, got {early.name}"
                )
                assert late.name == expected_late, (
                    f"Date {test_date}: Expected {expected_late} for "
                    f"late, got {late.name}"
                )

    def test_get_shift_teams_invalid_input(self, app, teams):
        """Test that get_shift_teams handles invalid input gracefully.

        Verifies behavior when given None or invalid data.
        """
        with app.app_context():
            # Test with None date (should raise AttributeError or handle gracefully)
            with pytest.raises(AttributeError):
                get_shift_teams(None, teams)

            # Test with empty teams list (should return None, None)
            test_date = datetime(2024, 1, 1)
            early, late = get_shift_teams(test_date, [])

            assert early is None, "Early shift should be None with empty teams list"
            assert late is None, "Late shift should be None with empty teams list"

            # Test with partial teams list (missing some teams)
            partial_teams = [teams[0], teams[1]]  # Only Team A and B
            test_date_needing_c = datetime(2024, 1, 3)  # Should need Team C

            early, late = get_shift_teams(test_date_needing_c, partial_teams)

            # Should return None for teams that don't exist in the list
            assert early is None, "Should return None when team not found in list"
            assert late is None, "Should return None when team not found in list"
