from unittest.mock import MagicMock, patch

import pytest

from apps.planning.src.services.task_assigner import (
    _assign_task_definition_to_schedule,
    assign_tasks,
    balance_workload_with_helpers,
)


class TestTaskAssigner:
    """Consolidated tests for Task Assigner and Workload Balancer."""

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    # =========================================================================
    # TASK ASSIGNMENT (PM FLOW)
    # =========================================================================

    def test_assign_tasks_pm_flow(self, mock_logger):
        """Test successful PM task assignment via strategy."""
        tasks = [
            {
                "id": 1,
                "task_type_upper": "PM",
                "quantity": 1,
                "mitarbeiter_pro_aufgabe": 1,
                "planned_worktime_min": 60,
            }
        ]
        techs = ["TechA"]

        with patch(
            "apps.planning.src.services.strategies.pm_strategy.PMAssignmentStrategy"
        ) as MockStrat:
            strat_instance = MockStrat.return_value
            strat_instance.assign_task.return_value = {
                "success": True,
                "assignments": [
                    {
                        "technician": "TechA",
                        "start": 0,
                        "duration": 60,
                        "task_name": "Task 1",
                        "instance_id": "1_1",
                    }
                ],
            }

            result = assign_tasks(tasks, techs, 480, MagicMock(), [], mock_logger)
            assert strat_instance.assign_task.called
            assert len(result[0]) == 1
            assert result[0][0]["technician"] == "TechA"

    def test_assign_task_skipped_invalid_data(self, mock_logger):
        """Test skipping tasks with invalid quantities or technicians."""
        # 1. Invalid quantity (0)
        task_q0 = {"id": "T1", "task_type_upper": "PM", "quantity": 0}
        unassigned = {}
        _assign_task_definition_to_schedule(
            task_to_assign=task_q0,
            present_technicians=[],
            total_work_minutes=480,
            rep_assignments=[],
            logger=mock_logger,
            technician_schedules={},
            all_task_assignments_details=[],
            unassigned_tasks_reasons_dict=unassigned,
            incomplete_tasks_instance_ids=[],
            all_pm_task_names_from_excel_normalized_set=set(),
            db_conn=MagicMock(),
        )
        assert len(unassigned) == 0  # Logic skips loop if quantity 0

        # 2. Invalid 'Mitarbeiter pro Aufgabe' (0)
        task_m0 = {
            "id": "T2",
            "name": "Zero Tech",
            "task_type_upper": "PM",
            "mitarbeiter_pro_aufgabe": 0,
            "planned_worktime_min": 60,
            "quantity": 1,
        }
        _assign_task_definition_to_schedule(
            task_to_assign=task_m0,
            present_technicians=[],
            total_work_minutes=480,
            rep_assignments=[],
            logger=mock_logger,
            technician_schedules={},
            all_task_assignments_details=[],
            unassigned_tasks_reasons_dict=unassigned,
            incomplete_tasks_instance_ids=[],
            all_pm_task_names_from_excel_normalized_set=set(),
            db_conn=MagicMock(),
        )
        assert "T2_1" in unassigned
        assert "Invalid 'Mitarbeiter pro Aufgabe'" in unassigned["T2_1"]

    # =========================================================================
    # WORKLOAD BALANCING
    # =========================================================================

    def test_balance_workload_no_overload(self, mock_logger):
        """Test that balanced workloads remain unchanged."""
        schedules = {"TechA": [(0, 100, "T1")], "TechB": [(0, 100, "T2")]}
        avail = {"TechA": 380, "TechB": 380}
        res_assignments, _, _ = balance_workload_with_helpers(
            [], schedules, avail, ["TechA", "TechB"], 480, {}, [], [], mock_logger
        )
        assert res_assignments == []

    def test_balance_workload_success(self, mock_logger):
        """Test splitting a task between overloaded and idle technicians."""
        available_time = {"TechA": 20, "TechB": 400}
        tasks = [
            {
                "id": "T1",
                "name": "Task One",
                "task_type_upper": "PM",
                "technology_ids": ["S1"],
            }
        ]
        assignments = [
            {
                "technician": "TechA",
                "task_name": "Task One",
                "start": 0,
                "duration": 120,
                "instance_id": "T1_1",
            }
        ]
        schedules = {"TechA": [(0, 120, "Task One")], "TechB": []}
        skills = {"TechA": {"S1": 1}, "TechB": {"S1": 1}}

        _a, _s, _avail = balance_workload_with_helpers(
            assignments=assignments,
            technician_schedules=schedules,
            available_time=available_time,
            present_technicians=["TechA", "TechB"],
            total_work_minutes=480,
            technician_technology_skills=skills,
            tasks=tasks,
            rep_assignments=[],
            logger=mock_logger,
        )

        assert len(assignments) == 2
        names = [a["technician"] for a in assignments]
        assert "TechB" in names
        assert assignments[1]["duration"] == 60  # Split 120 -> 60/60
        assert assignments[1]["technician_task_info"] == "Helper"

    def test_balance_workload_rep_qualified(self, mock_logger):
        """Test balancing for REP task ensuring helper is in qualified group."""
        available_time = {"TechA": 20, "TechB": 400}
        tasks = [{"id": "R1", "name": "Rep Task", "task_type_upper": "REP"}]
        assignments = [
            {
                "technician": "TechA",
                "task_name": "Rep Task",
                "start": 0,
                "duration": 100,
                "instance_id": "R1_1",
            }
        ]
        schedules = {"TechA": [(0, 100, "Rep Task")], "TechB": []}
        rep_ass = [
            {"task_id": "R1", "technicians": [{"name": "TechA"}, {"name": "TechB"}]}
        ]

        balance_workload_with_helpers(
            assignments=assignments,
            technician_schedules=schedules,
            available_time=available_time,
            present_technicians=["TechA", "TechB"],
            total_work_minutes=480,
            technician_technology_skills={},
            tasks=tasks,
            rep_assignments=rep_ass,
            logger=mock_logger,
        )

        assert any(a["technician"] == "TechB" for a in assignments)
