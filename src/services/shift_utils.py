from datetime import datetime

def get_shift_teams(date_obj, teams):
    """
    Determines the Early and Late shift teams for a given date based on the 
    2-2-3 Rotating Schedule (Pitman Schedule).
    
    Args:
        date_obj (datetime): The date to calculate teams for.
        teams (list): List of Team objects from the database.
        
    Returns:
        tuple: (early_team, late_team) - The Team objects assigned to Early and Late shifts.
               Returns (None, None) if no matching teams are found.
    """
    week_num = date_obj.isocalendar()[1]
    day_of_week = date_obj.weekday() # 0=Mon, 6=Sun
    is_odd_week = (week_num % 2) != 0
    
    # 1. Determine Active Pattern Group
    # Group 1 (Teams A & B): Odd Week (Mon,Tue,Fri,Sat,Sun) OR Even Week (Wed,Thu)
    # Group 2 (Teams C & D): Odd Week (Wed,Thu) OR Even Week (Mon,Tue,Fri,Sat,Sun)
    
    is_group_1_day = False
    if is_odd_week:
        if day_of_week in [0, 1, 4, 5, 6]: # Mon, Tue, Fri, Sat, Sun
            is_group_1_day = True
    else: # Even week
        if day_of_week in [2, 3]: # Wed, Thu
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
            
    # Find Team objects
    early_team = None
    late_team = None
    
    for team in teams:
        if team.name == early_team_name:
            early_team = team
        elif team.name == late_team_name:
            late_team = team
            
    return early_team, late_team
