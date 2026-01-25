import pytest

from apps.planning.src.services.strategies.rep_strategy import REPAssignmentStrategy


class TestREPAssignmentStrategy:
    @pytest.fixture
    def strategy(self):
        return REPAssignmentStrategy(logger=None)

    def test_assign_task_success(self, strategy):
        context = {
            "task_to_assign": {
                "id": 1,
                "name": "Repair Task",
                "planned_worktime_min": 120,
            },
            "instance_num": 1,
            "quantity": 1,
            "rep_assignments": [
                {"task_id": 1, "technician": "TechA", "time_slot": 60, "skipped": False}
            ],
        }
        result = strategy.assign_task(context)
        assert result["success"] is True
        assert result["assignments"][0]["technician"] == "TechA"
        assert result["assignments"][0]["start"] == 60
        assert result["assignments"][0]["duration"] == 120

    def test_assign_task_skipped_by_user(self, strategy):
        context = {
            "task_to_assign": {"id": 1, "name": "Repair Task"},
            "instance_num": 1,
            "quantity": 1,
            "rep_assignments": [
                {"task_id": 1, "skipped": True, "skip_reason": "Not needed"}
            ],
        }
        result = strategy.assign_task(context)
        assert result["success"] is False
        assert "Not needed" in result["failure_reason"]

    def test_assign_task_missing_assignment_data(self, strategy):
        context = {
            "task_to_assign": {"id": 1, "name": "Repair Task"},
            "instance_num": 1,
            "quantity": 1,
            "rep_assignments": [],  # Empty
        }
        result = strategy.assign_task(context)
        assert result["success"] is False
        assert "not received" in result["failure_reason"]

    def test_assign_task_incomplete_info(self, strategy):
        context = {
            "task_to_assign": {
                "id": 1,
                "name": "Repair Task",
                "planned_worktime_min": 60,
            },
            "instance_num": 1,
            "quantity": 1,
            "rep_assignments": [
                {
                    "task_id": 1,
                    "technician": None,  # Missing
                    "time_slot": 60,
                }
            ],
        }
        result = strategy.assign_task(context)
        assert result["success"] is False
        assert "Incomplete" in result["failure_reason"]
