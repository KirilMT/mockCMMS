"""
Tests for advanced team formation logic in the planning engine.

Tests cover:
- Multi-technician team formation
- Skill coverage validation
- Experience balancing
- Team optimization scoring
"""

import pytest
from datetime import datetime, timedelta
from flask import Flask
from src.services.db_utils import db, MaintenanceOrder, User, Skill, Asset
from apps.planning.src.services.planning_models import PlanningTask, Schedule
from apps.planning.src.services.planning_engine import PlanningEngine


@pytest.fixture
def app_context_team_tests():
    """Create application context with test database for team formation tests."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Create skills
        electrical = Skill(id=1, name="Electrical")
        mechanical = Skill(id=2, name="Mechanical")
        plc = Skill(id=3, name="PLC Programming")
        robotics = Skill(id=4, name="Robotics")

        db.session.add_all([electrical, mechanical, plc, robotics])
        db.session.flush()

        # Create technicians with different skill levels and combinations
        # Senior multi-skilled technician
        alice = Technician(
            id=1, name="Alice",
            availability_status='Available'
        )
        alice.skills = [
            TechnicianSkill(technician_id=1, skill_id=1, skill_level=5),  # Electrical - Expert
            TechnicianSkill(technician_id=1, skill_id=2, skill_level=4),  # Mechanical - Advanced
        ]

        # Mid-level specialist
        bob = Technician(
            id=2, name="Bob",
            availability_status='Available'
        )
        bob.skills = [
            TechnicianSkill(technician_id=2, skill_id=3, skill_level=4),  # PLC - Advanced
            TechnicianSkill(technician_id=2, skill_id=1, skill_level=3),  # Electrical - Intermediate
        ]

        # Junior technician with limited skills
        charlie = Technician(
            id=3, name="Charlie",
            availability_status='Available'
        )
        charlie.skills = [
            TechnicianSkill(technician_id=3, skill_id=2, skill_level=2),  # Mechanical - Beginner
        ]

        # Senior specialist
        diana = Technician(
            id=4, name="Diana",
            availability_status='Available'
        )
        diana.skills = [
            TechnicianSkill(technician_id=4, skill_id=4, skill_level=5),  # Robotics - Expert
            TechnicianSkill(technician_id=4, skill_id=1, skill_level=4),  # Electrical - Advanced
        ]

        # Mid-level generalist
        eve = Technician(
            id=5, name="Eve",
            availability_status='Available'
        )
        eve.skills = [
            TechnicianSkill(technician_id=5, skill_id=1, skill_level=3),  # Electrical
            TechnicianSkill(technician_id=5, skill_id=2, skill_level=3),  # Mechanical
            TechnicianSkill(technician_id=5, skill_id=3, skill_level=3),  # PLC
        ]

        db.session.add_all([alice, bob, charlie, diana, eve])
        db.session.flush()

        # Create asset
        asset = Asset(id=1, name="Robot Assembly Line", asset_code="RAL-001")
        db.session.add(asset)
        db.session.flush()

        # Create schedule
        schedule = Schedule(
            id=1,
            name="Weekend Team Test",
            start_date=datetime(2025, 11, 23),
            end_date=datetime(2025, 11, 24),
            planning_status='Draft'
        )
        db.session.add(schedule)
        db.session.commit()

        yield app


def test_two_person_team_skill_coverage(app_context_team_tests):
    """Test that 2-person teams are formed with complementary skills."""
    with app_context_team_tests.app_context():
        # Create task requiring Electrical AND Mechanical skills, 2 technicians
        mo = MaintenanceOrder(
            id=1,
            description="Robot Maintenance",
            asset_id=1,
            order_type="PM",
            estimated_completion_time=120,
            labour_count=2,  # Requires 2 technicians
            priority="High"
        )
        mo.required_skills.extend([
            Skill.query.get(1),  # Electrical
            Skill.query.get(2),  # Mechanical
        ])
        db.session.add(mo)
        db.session.commit()

        # Create planning task
        task = PlanningTask(
            maintenance_order_id=1,
            schedule_id=1,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(Schedule.query.get(1), planning_mode="weekend")

        # Should successfully assign 2-person team
        assert len(result.assigned_tasks) == 1
        assigned = result.assigned_tasks[0]

        # Team should have 2 members
        assert len(assigned.assigned_technician_ids) == 2

        # Team should collectively have both Electrical and Mechanical skills
        team = [Technician.query.get(tid) for tid in assigned.assigned_technician_ids]
        team_skills = set()
        for tech in team:
            team_skills.update(ts.skill.name for ts in tech.skills)

        assert "Electrical" in team_skills
        assert "Mechanical" in team_skills


def test_experience_balancing_in_team(app_context_team_tests):
    """Test that teams balance senior and junior technicians."""
    with app_context_team_tests.app_context():
        # Create task requiring only Electrical skill, 2 technicians
        mo = MaintenanceOrder(
            id=2,
            description="Electrical Panel Replacement",
            asset_id=1,
            order_type="PM",
            estimated_completion_time=90,
            labour_count=2,
            priority="Medium"
        )
        mo.required_skills.append(Skill.query.get(1))  # Electrical
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=2,
            schedule_id=1,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(Schedule.query.get(1), planning_mode="weekend")

        assert len(result.assigned_tasks) == 1
        assigned = result.assigned_tasks[0]

        # Get team members and their skill levels
        team = [Technician.query.get(tid) for tid in assigned.assigned_technician_ids]
        team_avg_levels = []
        for tech in team:
            electrical_skill = next((ts for ts in tech.skills if ts.skill.name == "Electrical"), None)
            if electrical_skill:
                team_avg_levels.append(electrical_skill.skill_level)

        # Should have at least one technician with skill level >= 4 (senior)
        assert any(level >= 4 for level in team_avg_levels), \
            f"Team should include senior technician, but levels are: {team_avg_levels}"


def test_three_person_multi_skill_team(app_context_team_tests):
    """Test formation of 3-person team with multiple required skills."""
    with app_context_team_tests.app_context():
        # Create complex task requiring Electrical, Mechanical, AND PLC skills
        mo = MaintenanceOrder(
            id=3,
            description="Complete Robot System Overhaul",
            asset_id=1,
            order_type="Project",
            estimated_completion_time=240,
            labour_count=3,
            priority="High"
        )
        mo.required_skills.extend([
            Skill.query.get(1),  # Electrical
            Skill.query.get(2),  # Mechanical
            Skill.query.get(3),  # PLC
        ])
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=3,
            schedule_id=1,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(Schedule.query.get(1), planning_mode="weekend")

        assert len(result.assigned_tasks) == 1
        assigned = result.assigned_tasks[0]

        # Team should have 3 members
        assert len(assigned.assigned_technician_ids) == 3

        # Team should collectively cover all 3 required skills
        team = [Technician.query.get(tid) for tid in assigned.assigned_technician_ids]
        team_skills = set()
        for tech in team:
            team_skills.update(ts.skill.name for ts in tech.skills)

        assert "Electrical" in team_skills
        assert "Mechanical" in team_skills
        assert "PLC Programming" in team_skills


def test_team_cannot_be_formed_insufficient_skills(app_context_team_tests):
    """Test that task remains unassigned if no team can cover all required skills."""
    with app_context_team_tests.app_context():
        # Create task requiring a skill no one has
        rare_skill = Skill(id=99, name="Underwater Welding")
        db.session.add(rare_skill)
        db.session.flush()

        mo = MaintenanceOrder(
            id=4,
            description="Underwater Pipe Repair",
            asset_id=1,
            order_type="REP",
            estimated_completion_time=60,
            labour_count=2,
            priority="Critical"
        )
        mo.required_skills.append(rare_skill)
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=4,
            schedule_id=1,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(Schedule.query.get(1), planning_mode="weekend")

        # Task should be unassigned due to missing skills
        assert len(result.unassigned_tasks) == 1
        unassigned = result.unassigned_tasks[0]
        assert "Underwater Welding" in unassigned.reason_detail  # Skill name in detail message


def test_single_person_task_selects_best_candidate(app_context_team_tests):
    """Test that single-person tasks select the most qualified technician."""
    with app_context_team_tests.app_context():
        # Create task requiring only Robotics skill, 1 technician
        mo = MaintenanceOrder(
            id=5,
            description="Robot Calibration",
            asset_id=1,
            order_type="PM",
            estimated_completion_time=45,
            labour_count=1,
            priority="Medium"
        )
        mo.required_skills.append(Skill.query.get(4))  # Robotics
        db.session.add(mo)
        db.session.commit()

        task = PlanningTask(
            maintenance_order_id=5,
            schedule_id=1,
            status='Unplanned'
        )
        db.session.add(task)
        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(Schedule.query.get(1), planning_mode="weekend")

        assert len(result.assigned_tasks) == 1
        assigned = result.assigned_tasks[0]

        # Should assign Diana (expert in Robotics with level 5)
        assert len(assigned.assigned_technician_ids) == 1
        assigned_tech = Technician.query.get(assigned.assigned_technician_ids[0])
        assert assigned_tech.name == "Diana"


def test_workload_distribution_across_team_tasks(app_context_team_tests):
    """Test that multiple team tasks distribute workload fairly."""
    with app_context_team_tests.app_context():
        # Create 3 similar tasks requiring Electrical skill, 2 technicians each
        for i in range(1, 4):
            mo = MaintenanceOrder(
                id=i,
                description=f"Electrical Task {i}",
                asset_id=1,
                order_type="PM",
                estimated_completion_time=60,
                labour_count=2,
                priority="Medium"
            )
            mo.required_skills.append(Skill.query.get(1))  # Electrical
            db.session.add(mo)

            task = PlanningTask(
                maintenance_order_id=i,
                schedule_id=1,
                status='Unplanned'
            )
            db.session.add(task)

        db.session.commit()

        # Run planning
        engine = PlanningEngine()
        result = engine.generate_plan(Schedule.query.get(1), planning_mode="weekend")

        # All 3 tasks should be assigned
        assert len(result.assigned_tasks) == 3

        # Collect all technician assignments
        tech_assignment_counts = {}
        for assigned in result.assigned_tasks:
            for tech_id in assigned.assigned_technician_ids:
                tech_assignment_counts[tech_id] = tech_assignment_counts.get(tech_id, 0) + 1

        # Workload should be distributed (no tech should get all 3 tasks)
        max_assignments = max(tech_assignment_counts.values())
        assert max_assignments <= 2, f"Workload not balanced: {tech_assignment_counts}"

