import pytest

from apps.planning.src.services.strategies.pm_strategy import PMAssignmentStrategy


class TestPMAssignmentStrategy:
    @pytest.fixture
    def strategy(self):
        return PMAssignmentStrategy(logger=None)

    def test_assign_task_success(self, strategy):
        context = {
            "task_to_assign": {
                "id": 1,
                "name": "Test PM Task",
                "technology_ids": [101],
                "planned_worktime_min": 60,
                "mitarbeiter_pro_aufgabe": 1,
            },
            "instance_num": 1,
            "quantity": 1,
            "present_technicians": ["TechA", "TechB"],
            "technician_schedules": {"TechA": [], "TechB": [(0, 100, "Breakfast")]},
            "technician_technology_skills": {"TechA": {101: 3}, "TechB": {101: 2}},
            "task_lines_list": [],
            "technician_lines": {"TechA": [], "TechB": []},
            "total_work_minutes": 480,
        }

        result = strategy.assign_task(context)

        assert result["success"] is True
        assert len(result["assignments"]) == 1
        assert result["assignments"][0]["technician"] == "TechA"
        assert result["assignments"][0]["start"] == 0
        assert result["assignments"][0]["duration"] == 60

    def test_assign_task_no_skills(self, strategy):
        context = {
            "task_to_assign": {
                "id": 2,
                "technology_ids": [999],  # No one has this
                "name": "Hard Task",
            },
            "instance_num": 1,
            "quantity": 1,
            "present_technicians": ["TechA"],
            "technician_schedules": {"TechA": []},
            "technician_technology_skills": {"TechA": {101: 3}},
            "task_lines_list": [],
            "total_work_minutes": 480,
        }
        result = strategy.assign_task(context)
        assert result["success"] is False
        assert (
            "No viable technician groups" in result["failure_reason"]
            or "No technicians eligible" in result["failure_reason"]
        )

    def test_assign_task_no_time_slot(self, strategy):
        context = {
            "task_to_assign": {
                "id": 1,
                "name": "Long Task",
                "technology_ids": [101],
                "planned_worktime_min": 500,
                "mitarbeiter_pro_aufgabe": 1,
            },
            "instance_num": 1,
            "quantity": 1,
            "present_technicians": ["TechA"],
            "technician_schedules": {"TechA": [(0, 400, "Busy")]},
            "technician_technology_skills": {"TechA": {101: 3}},
            "task_lines_list": [],
            "total_work_minutes": 480,
        }
        # Available: 400-480 = 80 mins. Task needs 500. incomplete?
        # Logic says: if remaining >= effective * 0.75... 80 < 375. So fails.

        result = strategy.assign_task(context)
        assert result["success"] is False
        assert "No suitable time slot" in result["failure_reason"]

    def test_technician_lines_mismatch(self, strategy):
        context = {
            "task_to_assign": {"id": 3, "name": "Line Task", "technology_ids": [101]},
            "instance_num": 1,
            "quantity": 1,
            "present_technicians": ["TechA"],
            "technician_schedules": {"TechA": []},
            "technician_technology_skills": {"TechA": {101: 3}},
            "task_lines_list": ["LineX"],  # Task needs LineX
            "technician_lines": {"TechA": ["LineY"]},  # Tech has LineY
            "total_work_minutes": 480,
        }
        result = strategy.assign_task(context)
        assert result["success"] is False
        assert "No technicians eligible" in result["failure_reason"]
