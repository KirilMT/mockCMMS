# apps/workforceManager/tests/test_planning_modes.py

"""
Unit tests for Planning Mode-Specific Logic (Phase 2 - Hybrid)

Tests cover:
- Shift-break mode: 30-minute window enforcement
- Shift-break mode: Strict priority ordering
- Weekend mode: PM frequency filtering
- Weekend mode: No time limits
"""

import pytest
from datetime import datetime
from src.services.db_utils import db, MaintenanceOrder, Technician, Skill, SparePart
from apps.workforceManager.src.services.planning_models import (
    PlanningTask, Schedule, TechnicianSkill
)
from apps.workforceManager.src.services.planning_engine import PlanningEngine
from apps.workforceManager.src.services.planning_result import UnassignedReason


@pytest.fixture
def planning_app():
    """Create a Flask app with in-memory database for planning mode tests."""
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_schedule(planning_app):
    """Create a sample schedule."""
    with planning_app.app_context():
        schedule = Schedule(
            name="Test Schedule",
            start_date=datetime(2025, 11, 18, 8, 0),
            end_date=datetime(2025, 11, 20, 18, 0),
            planning_status='Draft'
        )
        db.session.add(schedule)
        db.session.commit()

        yield schedule


@pytest.fixture
def sample_technicians(planning_app):
    """Create sample technicians with skills."""
    with planning_app.app_context():
        # Create skills
        electrical = Skill(name="Electrical")
        mechanical = Skill(name="Mechanical")
        db.session.add_all([electrical, mechanical])
        db.session.commit()

        # Create technicians
        tech1 = Technician(name="Alice", availability_status="Available")
        tech2 = Technician(name="Bob", availability_status="Available")

        db.session.add_all([tech1, tech2])
        db.session.commit()

        # Assign skills
        db.session.add(TechnicianSkill(technician_id=tech1.id, skill_id=electrical.id, skill_level=5))
        db.session.add(TechnicianSkill(technician_id=tech2.id, skill_id=mechanical.id, skill_level=5))

        db.session.commit()

        yield {
            'alice': tech1,
            'bob': tech2,
            'electrical': electrical,
            'mechanical': mechanical
        }


def test_shift_break_30_minute_window(planning_app, sample_schedule, sample_technicians):
    """Test that tasks over 30 minutes are unassigned in shift-break mode."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create a 45-minute task (exceeds 30-minute window)
        mo = MaintenanceOrder(
            description="Long Electrical Task",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=45,  # Exceeds 30 minutes
            labour_count=1,
            priority="Medium"
        )
        mo.required_skills.append(electrical)
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning in SHIFT-BREAK mode
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="shift_break")

        # Verify task is unassigned due to time window
        assert len(result.assigned_tasks) == 0
        assert len(result.unassigned_tasks) == 1

        unassigned = result.unassigned_tasks[0]
        assert unassigned.reason == UnassignedReason.INSUFFICIENT_TIME
        assert "30" in unassigned.reason_detail  # Should mention 30-minute limit


def test_shift_break_accepts_short_tasks(planning_app, sample_schedule, sample_technicians):
    """Test that tasks under 30 minutes ARE assigned in shift-break mode."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create a 20-minute task (fits within 30-minute window)
        mo = MaintenanceOrder(
            description="Quick Electrical Check",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=20,  # Within 30 minutes
            labour_count=1,
            priority="Medium"
        )
        mo.required_skills.append(electrical)
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning in SHIFT-BREAK mode
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="shift_break")

        # Verify task IS assigned
        assert len(result.assigned_tasks) == 1
        assert len(result.unassigned_tasks) == 0


def test_shift_break_priority_ordering(planning_app, sample_schedule, sample_technicians):
    """Test that shift-break mode prioritizes Critical/REP over PM tasks."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create tasks with different types and priorities
        # PM task (lower priority in shift-break mode)
        pm_task = MaintenanceOrder(
            description="PM Task",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=15,
            labour_count=1,
            priority="High"
        )
        pm_task.required_skills.append(electrical)
        db.session.add(pm_task)
        db.session.commit()

        # REP task (higher priority in shift-break mode)
        rep_task = MaintenanceOrder(
            description="REP Task",
            order_type="REP",
            asset_id=1,
            estimated_completion_time=20,
            labour_count=1,
            priority="Medium"  # Lower priority level but REP type
        )
        rep_task.required_skills.append(electrical)
        db.session.add(rep_task)
        db.session.commit()

        # Create planning tasks
        for mo in [pm_task, rep_task]:
            task = PlanningTask(
                maintenance_order_id=mo.id,
                schedule_id=sample_schedule.id,
                status='Unplanned'
            )
            db.session.add(task)

        db.session.commit()

        # Run planning in SHIFT-BREAK mode
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="shift_break")

        # Verify both assigned
        assert len(result.assigned_tasks) == 2

        # Verify REP task assigned FIRST (despite lower priority level)
        first_assigned = result.assigned_tasks[0]
        assert "REP" in first_assigned.task_description
        assert first_assigned.task_type == "REP"


def test_weekend_no_time_limit(planning_app, sample_schedule, sample_technicians):
    """Test that weekend mode accepts long-duration tasks."""
    with planning_app.app_context():
        # Merge skill into current session
        mechanical = db.session.merge(sample_technicians['mechanical'])

        # Create a 4-hour (240 minute) task
        mo = MaintenanceOrder(
            description="Major Equipment Overhaul",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=240,  # 4 hours - too long for shift-break
            labour_count=1,
            priority="Medium",
            frequency="Monthly"
        )
        mo.required_skills.append(mechanical)
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning in WEEKEND mode
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify task IS assigned in weekend mode
        assert len(result.assigned_tasks) == 1
        assert len(result.unassigned_tasks) == 0

        assignment = result.assigned_tasks[0]
        assert assignment.estimated_duration_minutes == 240


def test_weekend_pm_priority_ordering(planning_app, sample_schedule, sample_technicians):
    """Test that weekend mode prioritizes PM over REP tasks."""
    with planning_app.app_context():
        # Merge skill into current session
        mechanical = db.session.merge(sample_technicians['mechanical'])

        # Create PM and REP tasks
        pm_task = MaintenanceOrder(
            description="Weekly PM",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=60,
            labour_count=1,
            priority="Medium",
            frequency="Weekly"
        )
        pm_task.required_skills.append(mechanical)
        db.session.add(pm_task)
        db.session.commit()

        rep_task = MaintenanceOrder(
            description="REP Task",
            order_type="REP",
            asset_id=1,
            estimated_completion_time=45,
            labour_count=1,
            priority="High"  # Higher priority level
        )
        rep_task.required_skills.append(mechanical)
        db.session.add(rep_task)
        db.session.commit()

        # Create planning tasks
        for mo in [pm_task, rep_task]:
            task = PlanningTask(
                maintenance_order_id=mo.id,
                schedule_id=sample_schedule.id,
                status='Unplanned'
            )
            db.session.add(task)

        db.session.commit()

        # Run planning in WEEKEND mode
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify both assigned
        assert len(result.assigned_tasks) == 2

        # Verify PM task assigned FIRST in weekend mode
        first_assigned = result.assigned_tasks[0]
        assert "PM" in first_assigned.task_description
        assert first_assigned.task_type == "PM"


def test_mode_comparison_same_task(planning_app, sample_schedule, sample_technicians):
    """Test that the same long task behaves differently in different modes."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create a 45-minute task
        mo = MaintenanceOrder(
            description="45-Minute Task",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=45,
            labour_count=1,
            priority="Medium"
        )
        mo.required_skills.append(electrical)
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Test 1: Shift-break mode - should REJECT
        engine = PlanningEngine()
        result_shift_break = engine.generate_plan(sample_schedule, planning_mode="shift_break")

        assert len(result_shift_break.assigned_tasks) == 0
        assert len(result_shift_break.unassigned_tasks) == 1

        # Reset task status
        task.status = 'Unplanned'
        db.session.commit()

        # Test 2: Weekend mode - should ACCEPT
        result_weekend = engine.generate_plan(sample_schedule, planning_mode="weekend")

        assert len(result_weekend.assigned_tasks) == 1
        assert len(result_weekend.unassigned_tasks) == 0

