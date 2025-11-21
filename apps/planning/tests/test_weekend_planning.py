import pytest
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path to allow imports to work
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock dependencies handled in conftest.py if missing

from apps.planning.src.services.planning_engine import PlanningEngine, ShiftDefinition

# Mock Configuration
MOCK_CONFIG = {
    "shift_patterns": {
        "production": {
            "shifts": [
                {"name": "morning", "start_time": "06:00", "end_time": "14:00"},
                {"name": "afternoon", "start_time": "14:00", "end_time": "22:00"},
                {"name": "night", "start_time": "22:00", "end_time": "06:00"}
            ]
        },
        "maintenance": {
            "shifts": [
                {"name": "early", "start_time": "06:00", "end_time": "18:00"},
                {"name": "late", "start_time": "18:00", "end_time": "06:00"}
            ]
        }
    },
    "planning_windows": {
        "weekend_maintenance": {
            "start_day": "Friday",
            "start_time": "22:00",
            "end_day": "Sunday",
            "end_time": "22:00",
            "resource_pattern": "maintenance"
        }
    }
}

class TestWeekendPlanning:
    @pytest.fixture
    def engine(self):
        engine = PlanningEngine()
        # Mock _load_config to return our test config
        engine._load_config = MagicMock(return_value=MOCK_CONFIG)
        engine._log = MagicMock() # Mock logger
        return engine

    def test_shift_intersection_friday_night(self, engine):
        """Test that Friday maintenance shift starts at 22:00 (intersection of Late Shift and Window Start)."""
        # Friday
        start_date = datetime(2023, 11, 24) # Nov 24 2023 is a Friday
        
        shifts = engine._get_weekend_shifts(start_date)
        
        assert len(shifts) > 0
        
        # First shift should be Friday Late (intersected)
        # Maintenance Late is 18:00 - 06:00
        # Window starts Fri 22:00
        # Intersection: Fri 22:00 - Sat 06:00
        
        first_shift = shifts[0]
        assert "Late" in first_shift.name
        assert first_shift.start_time.time() == time(22, 0)
        assert first_shift.end_time.time() == time(6, 0)
        assert first_shift.is_overnight == True
        assert first_shift.duration_minutes == 8 * 60 # 8 hours

    def test_shift_intersection_saturday_full(self, engine):
        """Test that Saturday has full Early and Late shifts."""
        start_date = datetime(2023, 11, 24) # Friday
        
        shifts = engine._get_weekend_shifts(start_date)
        
        # Find Saturday shifts
        sat_shifts = [s for s in shifts if s.day_name == 'saturday']
        
        assert len(sat_shifts) == 2
        
        # Early: 06:00 - 18:00 (Full 12h)
        early = sat_shifts[0]
        assert "Early" in early.name
        assert early.start_time.time() == time(6, 0)
        assert early.end_time.time() == time(18, 0)
        assert early.duration_minutes == 12 * 60
        
        # Late: 18:00 - 06:00 (Full 12h)
        late = sat_shifts[1]
        assert "Late" in late.name
        assert late.start_time.time() == time(18, 0)
        assert late.end_time.time() == time(6, 0)
        assert late.is_overnight == True

    def test_shift_intersection_sunday_end(self, engine):
        """Test that Sunday shifts end at 22:00 (Window End)."""
        start_date = datetime(2023, 11, 24) # Friday
        
        shifts = engine._get_weekend_shifts(start_date)
        
        # Find Sunday shifts
        sun_shifts = [s for s in shifts if s.day_name == 'sunday']
        
        assert len(sun_shifts) >= 1
        
        # Early: 06:00 - 18:00 (Full 12h)
        early = sun_shifts[0]
        assert "Early" in early.name
        assert early.duration_minutes == 12 * 60
        
        # Late: 18:00 - 06:00 BUT Window ends Sun 22:00
        # Intersection: 18:00 - 22:00
        if len(sun_shifts) > 1:
            late = sun_shifts[1]
            assert "Late" in late.name
            assert late.start_time.time() == time(18, 0)
            assert late.end_time.time() == time(22, 0)
            assert late.duration_minutes == 4 * 60
            assert late.is_overnight == False # Ends same day

    def test_assign_task_to_shift(self, engine):
        # Setup a mock task and technician
        task = MagicMock()
        task.id = 1
        mo = MagicMock()
        mo.id = 101
        mo.description = "Test Task"
        mo.labour_count = 1
        mo.estimated_completion_time = 60 # 1 hour
        mo.required_skills = []
        mo.priority = "High"
        mo.order_type = "PM"
        
        tech = MagicMock()
        tech.id = 1
        tech.name = "John Doe"
        tech.skills = []
        
        workloads = {1: MagicMock(total_available_minutes=1000, total_assigned_minutes=0)}
        
        # Try to assign to a specific time
        current_time = datetime(2023, 11, 24, 8, 0) # Fri 08:00
        result = MagicMock()
        
        # Shift ends at 18:00
        shift_end = datetime(2023, 11, 24, 18, 0)
        shift_avail = {1: 720} # 12 hours
        
        assignment = engine._assign_single_task(
            task, mo, [tech], workloads, current_time, result, "weekend", 720,
            shift_end_time=shift_end,
            shift_availability=shift_avail
        )
        
        assert assignment is not None
        assert assignment.assigned_technician_ids == [1]
        assert assignment.planned_start_time == current_time
        assert assignment.planned_end_time == current_time + timedelta(minutes=60)
