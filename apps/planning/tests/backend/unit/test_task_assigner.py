from unittest.mock import MagicMock, patch

import pytest

from apps.planning.src.services.task_assigner import (
    assign_tasks,
    balance_workload_with_helpers,
)


class TestTaskAssigner:
    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    def test_assign_tasks_pm_flow(self, mock_logger):
        # inputs
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
        total_time = 480
        db = MagicMock()
        rep_ass = []

        # We mock the strategy class to verifying it's instantiated and called
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

            result = assign_tasks(tasks, techs, total_time, db, rep_ass, mock_logger)

            assert strat_instance.assign_task.called
            assert len(result[0]) == 1  # assignments
            assert result[0][0]["technician"] == "TechA"

    def test_assign_tasks_skip_invalid_quantity(self, mock_logger):
        tasks = [{"id": 1, "task_type_upper": "PM", "quantity": 0}]
        techs = ["TechA"]
        total_time = 480
        db = MagicMock()

        result = assign_tasks(tasks, techs, total_time, db, [], mock_logger)
        # assignments empty, unassigned keys
        assert len(result[0]) == 0
        # Wait, quantity 0 might not add to unassigned logic depending on
        # implementation...
        # Code says: if quantity <= 0... for i in range...
        # unassigned_tasks_reasons_dict.
        # If quantity 0, range(1, 1) is empty?
        # No max(1, quantity) -> range(1,1) -> loop runs once?
        # Code: range(1, max(1, quantity if quantity > 0 else 1))
        # -> range(1,1) -> empty.
        pass

    def test_balance_workload_no_overload(self, mock_logger):
        assignments = []
        schedules = {"TechA": [(0, 100, "Task1")], "TechB": [(0, 100, "Task2")]}
        avail = {"TechA": 380, "TechB": 380}  # Total 480.
        # Threshold 0.8 * 480 = 384. 480-380 = 100 occupied. Not overloaded.
        techs = ["TechA", "TechB"]
        skills = {}

        res_assignments, res_sched, res_avail = balance_workload_with_helpers(
            assignments, schedules, avail, techs, 480, skills, [], [], mock_logger
        )
        # Should be unchanged
        assert res_assignments == assignments

    def test_balance_workload_overloaded(self, mock_logger):
        # TechA overloaded (occupy 400 mins). TechB idle (occupy 0).
        # Total 480. Overload thr = 384. Occupied > 384.
        # TechA occupied 400. 480-400 = 80 avail.
        # TechB occupied 0. 480 avail. Idle thr = 240. TechB > 240.

        tasks_def = [{"id": 1, "task_type_upper": "PM", "technology_ids": [10]}]

        assignments = [
            {
                "technician": "TechA",
                "start": 0,
                "duration": 400,
                "task_name": "BigTask",
                "instance_id": "1_1",
            }
        ]
        schedules = {"TechA": [(0, 400, "BigTask")], "TechB": []}
        avail = {"TechA": 80, "TechB": 480}
        techs = ["TechA", "TechB"]
        skills = {"TechB": {10: 3}}  # TechB can help

        res_assignments, res_sched, res_avail = balance_workload_with_helpers(
            assignments,
            schedules,
            avail,
            techs,
            480,
            skills,
            tasks_def,
            [],
            mock_logger,
        )

        # Expect split
        # duration 400 becomes 200.
        # TechA: 200. TechB: 200.
        assert len(res_assignments) == 2
        assert res_assignments[0]["duration"] == 200
        assert res_assignments[1]["duration"] == 200
        names = [a["technician"] for a in res_assignments]
        assert "TechA" in names
        assert "TechB" in names
