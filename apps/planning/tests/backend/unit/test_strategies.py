import logging

import pytest

from apps.planning.src.services.strategies.pm_strategy import PMAssignmentStrategy
from apps.planning.src.services.strategies.rep_strategy import REPAssignmentStrategy


@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")


@pytest.fixture
def base_context():
    return {
        "task_to_assign": {
            "id": 1,
            "name": "Task A",
            "planned_worktime_min": 60,
            "mitarbeiter_pro_aufgabe": 1,
            "technology_ids": [1],
        },
        "instance_num": 1,
        "quantity": 1,
        "present_technicians": ["Tech A"],
        "technician_schedules": {"Tech A": []},
        "technician_technology_skills": {"Tech A": {1: 1}},
        "task_lines_list": [],
        "technician_lines": {"Tech A": []},
        "total_work_minutes": 480,
    }


def test_pm_strategy_success(mock_logger, base_context):
    strategy = PMAssignmentStrategy(mock_logger)
    result = strategy.assign_task(base_context)

    assert result["success"] is True
    assert len(result["assignments"]) == 1
    assert result["assignments"][0]["technician"] == "Tech A"


def test_pm_strategy_no_eligible_techs(mock_logger, base_context):
    base_context["technician_technology_skills"] = {
        "Tech A": {2: 1}
    }  # Tech has wrong skill
    strategy = PMAssignmentStrategy(mock_logger)
    result = strategy.assign_task(base_context)

    assert result["success"] is False
    assert "No technicians eligible" in result["failure_reason"]


def test_rep_strategy_success(mock_logger):
    task = {"id": 100, "name": "Fix Pump", "planned_worktime_min": 120}
    rep_item = {"task_id": 100, "technician": "Tech B", "time_slot": 60}

    context = {
        "task_to_assign": task,
        "instance_num": 1,
        "quantity": 1,
        "rep_assignments": [rep_item],
        "total_work_minutes": 480,
        "technician_schedules": {"Tech B": []},
    }

    strategy = REPAssignmentStrategy(mock_logger)
    result = strategy.assign_task(context)

    assert result["success"] is True
    assert result["assignments"][0]["technician"] == "Tech B"
    assert result["assignments"][0]["start"] == 60
    assert result["assignments"][0]["duration"] == 120


def test_rep_strategy_missing_data(mock_logger):
    task = {"id": 101, "name": "Unknown", "planned_worktime_min": 60}
    context = {
        "task_to_assign": task,
        "instance_num": 1,
        "quantity": 1,
        "rep_assignments": [],  # Empty
        "total_work_minutes": 480,
        "technician_schedules": {},
    }

    strategy = REPAssignmentStrategy(mock_logger)
    result = strategy.assign_task(context)

    assert result["success"] is False
    assert "data not received" in result["failure_reason"]
