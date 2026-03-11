from unittest.mock import patch

import pytest

from apps.planning.src.services.strategies.pm_strategy import PMAssignmentStrategy
from apps.planning.src.services.task_assigner import (
    _assign_task_definition_to_schedule,
    _log,
)


class TestPlanningServices:
    @pytest.fixture(autouse=True)
    def setup_app(self, app):
        with app.app_context():
            yield

    def test_log_helper(self):
        with patch("builtins.print") as mock_print:
            _log(None, "info", "Hello World")
            mock_print.assert_called_with("[INFO] Hello World")

    def test_assign_task_errors(self, db_session):
        task = {
            "id": "1",
            "task_type_upper": "PM",
            "planned_worktime_min": 60,
            "mitarbeiter_pro_aufgabe": 0,
            "quantity": 1,
        }
        reasons = {}
        _assign_task_definition_to_schedule(
            task, [], 480, [], None, {}, [], reasons, [], set(), db_session
        )
        assert "1_1" in reasons

        task["mitarbeiter_pro_aufgabe"] = -1
        _assign_task_definition_to_schedule(
            task, [], 480, [], None, {}, [], reasons, [], set(), db_session
        )
        assert "must be positive" in reasons["1_1"]

    def test_pm_strategy_no_skills(self):
        strategy = PMAssignmentStrategy(None)
        context = {
            "task_to_assign": {"technology_ids": [], "id": "1"},
            "present_technicians": ["T1"],
            "instance_num": 1,
            "quantity": 1,
            "technician_schedules": {"T1": []},
            "technician_technology_skills": {"T1": {}},
            "total_work_minutes": 480,
        }
        res = strategy.assign_task(context)
        assert res["success"] is False
        assert "no required technology_ids defined" in res["failure_reason"].lower()
