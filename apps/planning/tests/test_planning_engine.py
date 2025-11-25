# apps/planning/tests/test_planning_engine.py

"""
Unit tests for the Planning Engine (Phase 2)

Tests cover:
- Skill-based matching
- Multi-skill tasks
- Team size optimization
- Duration adjustments
- Workload distribution
- Constraint handling
"""

import pytest
from datetime import datetime, timedelta
from src.services.db_utils import db, MaintenanceOrder, User, Skill, SparePart, UserSkill, maintenance_order_spare_parts
from apps.planning.src.services.planning_models import (
    PlanningTask, Schedule
)
from apps.planning.src.services.planning_engine import PlanningEngine
from apps.planning.src.services.planning_result import UnassignedReason


@pytest.fixture
def planning_app():
    """Create a Flask app with in-memory database for planning tests."""
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
    """Create a sample schedule with tasks."""
    with planning_app.app_context():
        # Create schedule
        schedule = Schedule(
            name="Weekend Plan - Nov 2025",
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
        hydraulic = Skill(name="Hydraulic")
        db.session.add_all([electrical, mechanical, hydraulic])
        db.session.commit()

        # Create technicians
        tech1 = Technician(name="Alice", availability_status="Available")
        tech2 = Technician(name="Bob", availability_status="Available")
        tech3 = Technician(name="Charlie", availability_status="Available")
        tech4 = Technician(name="Dave", availability_status="On Leave")  # Not available

        db.session.add_all([tech1, tech2, tech3, tech4])
        db.session.commit()

        # Assign skills
        # Alice: Electrical (level 5), Mechanical (level 3)
        db.session.add(TechnicianSkill(technician_id=tech1.id, skill_id=electrical.id, skill_level=5))
        db.session.add(TechnicianSkill(technician_id=tech1.id, skill_id=mechanical.id, skill_level=3))

        # Bob: Mechanical (level 5), Hydraulic (level 4)
        db.session.add(TechnicianSkill(technician_id=tech2.id, skill_id=mechanical.id, skill_level=5))
        db.session.add(TechnicianSkill(technician_id=tech2.id, skill_id=hydraulic.id, skill_level=4))

        # Charlie: Electrical (level 3), Hydraulic (level 3)
        db.session.add(TechnicianSkill(technician_id=tech3.id, skill_id=electrical.id, skill_level=3))
        db.session.add(TechnicianSkill(technician_id=tech3.id, skill_id=hydraulic.id, skill_level=3))

        # Dave (on leave): All skills but unavailable
        db.session.add(TechnicianSkill(technician_id=tech4.id, skill_id=electrical.id, skill_level=4))

        db.session.commit()

        yield {
            'alice': tech1,
            'bob': tech2,
            'charlie': tech3,
            'dave': tech4,
            'electrical': electrical,
            'mechanical': mechanical,
            'hydraulic': hydraulic
        }


def test_skill_based_matching_single_skill(planning_app, sample_schedule, sample_technicians):
    """Test that tasks are matched to technicians with required single skill."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create a task requiring only Electrical skill
        mo = MaintenanceOrder(
            description="Electrical Panel Inspection",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=60,
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

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify assignment
        assert len(result.assigned_tasks) == 1
        assert len(result.unassigned_tasks) == 0

        assignment = result.assigned_tasks[0]
        # Should be assigned to Alice (has Electrical skill level 5) or Charlie (level 3)
        assert assignment.assigned_technician_names[0] in ['Alice', 'Charlie']
        assert 'Electrical' in assignment.required_skills


def test_multi_skill_task_matching(planning_app, sample_schedule, sample_technicians):
    """Test that tasks requiring multiple skills are matched correctly."""
    with planning_app.app_context():
        # Merge skills into current session
        electrical = db.session.merge(sample_technicians['electrical'])
        mechanical = db.session.merge(sample_technicians['mechanical'])

        # Create a task requiring both Electrical AND Mechanical skills
        mo = MaintenanceOrder(
            description="Electrical Motor Replacement",
            order_type="Corrective",
            asset_id=1,
            estimated_completion_time=120,
            labour_count=1,
            priority="High"
        )
        mo.required_skills.extend([electrical, mechanical])
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify assignment
        assert len(result.assigned_tasks) == 1

        assignment = result.assigned_tasks[0]
        # Should be assigned to Alice (only tech with both Electrical and Mechanical)
        assert assignment.assigned_technician_names[0] == 'Alice'
        assert set(assignment.required_skills) == {'Electrical', 'Mechanical'}


def test_no_matching_skills_unassigned(planning_app, sample_schedule, sample_technicians):
    """Test that tasks without matching skills are marked unassigned."""
    with planning_app.app_context():
        # Create a skill no one has
        programming = Skill(name="Programming")
        db.session.add(programming)
        db.session.commit()

        # Create a task requiring this skill
        mo = MaintenanceOrder(
            description="PLC Programming",
            order_type="Project",
            asset_id=1,
            estimated_completion_time=180,
            labour_count=1,
            priority="Low"
        )
        mo.required_skills.append(programming)
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify task is unassigned
        assert len(result.assigned_tasks) == 0
        assert len(result.unassigned_tasks) == 1

        unassigned = result.unassigned_tasks[0]
        assert unassigned.reason == UnassignedReason.NO_MATCHING_SKILLS
        assert 'Programming' in unassigned.required_skills


def test_team_size_optimization(planning_app, sample_schedule, sample_technicians):
    """Test that team size is correctly handled."""
    with planning_app.app_context():
        # Merge skill into current session
        mechanical = db.session.merge(sample_technicians['mechanical'])

        # Create a task requiring 2 technicians with Mechanical skill
        mo = MaintenanceOrder(
            description="Heavy Equipment Move",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=90,
            labour_count=2,  # Requires 2 technicians
            priority="Medium"
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

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify assignment
        assert len(result.assigned_tasks) == 1

        assignment = result.assigned_tasks[0]
        # Should have 2 technicians assigned (Alice and Bob both have Mechanical)
        assert len(assignment.assigned_technician_ids) == 2
        assert set(assignment.assigned_technician_names) == {'Alice', 'Bob'}


def test_insufficient_team_size_unassigned(planning_app, sample_schedule, sample_technicians):
    """Test that tasks requiring more technicians than available are unassigned."""
    with planning_app.app_context():
        # Create a task requiring 5 technicians (we only have 3 available)
        mo = MaintenanceOrder(
            description="Large Assembly",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=120,
            labour_count=5,
            priority="Medium"
        )
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify task is unassigned
        assert len(result.assigned_tasks) == 0
        assert len(result.unassigned_tasks) == 1

        unassigned = result.unassigned_tasks[0]
        assert unassigned.reason == UnassignedReason.TEAM_SIZE_CONFLICT


def test_duration_adjustment_by_team_size(planning_app, sample_schedule, sample_technicians):
    """Test that duration is adjusted based on team size."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create a task requiring 1 tech but eligible for more
        mo = MaintenanceOrder(
            description="Equipment Inspection",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=100,  # Base: 100 minutes
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

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify assignment
        assert len(result.assigned_tasks) == 1

        assignment = result.assigned_tasks[0]
        # Duration should be 100 minutes (no adjustment if team size = required)
        assert assignment.estimated_duration_minutes == 100
        # Actual duration could be same or adjusted
        assert assignment.actual_duration_minutes <= 100


def test_workload_distribution(planning_app, sample_schedule, sample_technicians):
    """Test that workload is distributed fairly among technicians."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create multiple tasks
        for i in range(3):
            mo = MaintenanceOrder(
                description=f"Task {i+1}",
                order_type="PM",
                asset_id=1,
                estimated_completion_time=60,
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

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="weekend")

        # Verify all tasks assigned
        assert len(result.assigned_tasks) == 3

        # Check workload distribution
        workloads = {wl.technician_name: wl.assigned_task_count for wl in result.technician_workloads}

        # Alice and Charlie both have Electrical skill
        # Tasks should be distributed between them
        alice_tasks = workloads.get('Alice', 0)
        charlie_tasks = workloads.get('Charlie', 0)

        assert alice_tasks + charlie_tasks == 3
        # Workload should be relatively balanced (difference of at most 1)
        assert abs(alice_tasks - charlie_tasks) <= 2  # Allow some imbalance


def test_spare_parts_constraint(planning_app, sample_schedule, sample_technicians):
    """Test that tasks without available spare parts are marked unassigned."""
    with planning_app.app_context():
        # Merge skill into current session
        mechanical = db.session.merge(sample_technicians['mechanical'])

        # Create a spare part with zero stock
        part = SparePart(description="Special Filter", stock_quantity=0)
        db.session.add(part)
        db.session.commit()

        # Create a task requiring this part
        mo = MaintenanceOrder(
            description="Filter Replacement",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=30,
            labour_count=1,
            priority="Medium"
        )
        mo.required_skills.append(mechanical)
        db.session.add(mo)
        db.session.commit()

        # Link part to MO
        db.session.execute(
            maintenance_order_spare_parts.insert().values(
                maintenance_order_id=mo.id,
                spare_part_id=part.id,
                quantity_required=1
            )
        )
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning WITH parts check
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, check_parts=True)

        # Verify task is unassigned due to parts
        assert len(result.assigned_tasks) == 0
        assert len(result.unassigned_tasks) == 1

        unassigned = result.unassigned_tasks[0]
        assert unassigned.reason == UnassignedReason.INSUFFICIENT_PARTS


def test_invalid_task_data_unassigned(planning_app, sample_schedule, sample_technicians):
    """Test that tasks with invalid data are marked unassigned."""
    with planning_app.app_context():
        # Create task with zero duration
        mo = MaintenanceOrder(
            description="Invalid Task",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=0,  # Invalid!
            labour_count=1,
            priority="Medium"
        )
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule)

        # Verify task is unassigned
        assert len(result.assigned_tasks) == 0
        assert len(result.unassigned_tasks) == 1

        unassigned = result.unassigned_tasks[0]
        assert unassigned.reason == UnassignedReason.INVALID_DATA


def test_priority_ordering(planning_app, sample_schedule, sample_technicians):
    """Test that tasks are assigned in priority order."""
    with planning_app.app_context():
        # Merge skill into current session
        mechanical = db.session.merge(sample_technicians['mechanical'])

        # Create tasks with different priorities
        # NOTE: Using 25 minutes to fit within shift-break 30-minute window
        tasks_data = [
            ("Low Priority Task", "Low", "PM"),
            ("Critical Task", "Critical", "REP"),
            ("Medium Task", "Medium", "PM")
        ]

        for desc, priority, order_type in tasks_data:
            mo = MaintenanceOrder(
                description=desc,
                order_type=order_type,
                asset_id=1,
                estimated_completion_time=25,  # Changed from 60 to fit shift-break window
                labour_count=1,
                priority=priority
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

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule, planning_mode="shift_break")

        # Verify all assigned
        assert len(result.assigned_tasks) == 3

        # Verify order: Critical (REP) should be first, then Medium (PM), then Low (PM)
        assignments = result.assigned_tasks
        assert "Critical" in assignments[0].task_description
        assert "Medium" in assignments[1].task_description
        assert "Low" in assignments[2].task_description


def test_planning_result_statistics(planning_app, sample_schedule, sample_technicians):
    """Test that planning result statistics are calculated correctly."""
    with planning_app.app_context():
        # Merge skill into current session
        electrical = db.session.merge(sample_technicians['electrical'])

        # Create 2 assignable tasks and 1 unassignable
        for i in range(2):
            mo = MaintenanceOrder(
                description=f"Assignable Task {i+1}",
                order_type="PM",
                asset_id=1,
                estimated_completion_time=60,
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

        # Unassignable (no skills)
        skill_none = Skill(name="Nonexistent")
        db.session.add(skill_none)
        db.session.commit()

        mo = MaintenanceOrder(
            description="Unassignable Task",
            order_type="PM",
            asset_id=1,
            estimated_completion_time=60,
            labour_count=1,
            priority="Medium"
        )
        mo.required_skills.append(skill_none)
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=mo.id,
            schedule_id=sample_schedule.id,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(sample_schedule)

        # Verify statistics
        assert result.statistics is not None
        assert result.statistics.total_tasks == 3
        assert result.statistics.assigned_tasks == 2
        assert result.statistics.unassigned_tasks == 1
        assert result.statistics.assignment_success_rate == pytest.approx(66.67, abs=0.1)

