# src/services/shift_utils.py

"""Shift calculation utilities for the Pitman schedule."""


def get_shift_teams(date_obj, teams):
    """
    Determines the Early and Late shift teams for a given date based on a 2-2-3
    Rotating Schedule (Pitman Schedule).

    This schedule uses four teams (A, B, C, D) over a 28-day cycle.
    - Two teams work the day shift (e.g., A & C).
    - Two teams work the night shift (e.g., B & D).
    - Shifts rotate to give teams every other weekend off.

    Args:
        date_obj (datetime): The date for which to calculate the shift teams.
        teams (list): A list of Team objects from the database.

    Returns:
        tuple: A tuple containing (early_team, late_team) Team objects.
               Returns (None, None) if the required teams are not found.
    """
    week_num = date_obj.isocalendar()[1]
    day_of_week = date_obj.weekday()  # Monday is 0 and Sunday is 6

    is_odd_week = (week_num % 2) != 0

    is_group_1_day = False
    if is_odd_week:
        if day_of_week in [0, 1, 4, 5, 6]:  # Mon, Tue, Fri, Sat, Sun
            is_group_1_day = True
    else:  # Even week
        if day_of_week in [2, 3]:  # Wed, Thu
            is_group_1_day = True

    early_team_name = None
    late_team_name = None

    if is_group_1_day:
        # Group 1 (Teams A & B)
        # Rotation: Swap every 2 weeks. A is Early when (week-1)//2 is Even.
        rotation_idx = (week_num - 1) // 2
        if rotation_idx % 2 == 0:
            early_team_name = "Team B"
            late_team_name = "Team A"
        else:
            early_team_name = "Team A"
            late_team_name = "Team B"
    else:
        # Group 2 (Teams C & D)
        # Rotation: Swap every 2 weeks. C is Early when week//2 is Odd.
        rotation_idx = week_num // 2
        if rotation_idx % 2 != 0:
            early_team_name = "Team D"
            late_team_name = "Team C"
        else:
            early_team_name = "Team C"
            late_team_name = "Team D"

    # Find the corresponding team objects
    early_team = next((t for t in teams if t.name == early_team_name), None)
    late_team = next((t for t in teams if t.name == late_team_name), None)

    return early_team, late_team
