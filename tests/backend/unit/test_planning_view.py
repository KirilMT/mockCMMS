from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    # We don't need to register blueprint if we call view_schedule directly,
    # but we need app context.
    return app


def test_view_schedule_passes_config(app):
    with app.app_context():
        with (
            patch("apps.planning.src.routes.planning.Schedule"),
            patch("apps.planning.src.routes.planning.render_template") as mock_render,
            patch(
                "apps.planning.src.routes.planning.load_shift_config"
            ) as mock_load_config,
            patch("apps.planning.src.routes.planning.PlanningTask") as MockPlanningTask,
            patch("apps.planning.src.routes.planning.db") as mock_db,
            patch("apps.planning.src.routes.planning.MaintenanceOrder"),
        ):
            # Setup mocks
            mock_schedule = MagicMock()
            mock_db.get_or_404.return_value = mock_schedule

            # Mock MaintenanceOrder
            mock_mo = MagicMock()
            mock_mo.id = 1
            mock_mo.description = "Test Task"
            mock_mo.order_type = "PM"
            mock_mo.priority = 1
            mock_mo.estimated_completion_time = 60
            mock_mo.labour_count = 1
            mock_mo.required_skills = []
            mock_db.session.get.return_value = mock_mo

            # Mock PlanningTask
            mock_pt = MagicMock()
            mock_pt.maintenance_order_id = 1
            mock_pt.assigned_user = None
            mock_pt.status = "Planned"

            task_query = MockPlanningTask.query.filter_by.return_value
            task_query.all.return_value = [mock_pt]

            mock_config = {
                "shift_durations": {
                    "shift_break": 10,
                    "weekend": 20,
                }
            }
            mock_load_config.return_value = mock_config

            # Import locally to avoid stale module reference if module was
            # reloaded by other tests
            from apps.planning.src.routes.planning import view_schedule

            with app.test_request_context("/planning/schedules/1?mode=shift_break"):
                with (
                    patch("apps.planning.src.routes.planning.Schedule") as MockSchedule,
                    patch(
                        "apps.planning.src.routes.planning.render_template"
                    ) as mock_render,
                    patch(
                        "apps.planning.src.routes.planning.load_shift_config"
                    ) as mock_load_config,
                    patch(
                        "apps.planning.src.routes.planning.PlanningTask"
                    ) as MockPlanningTask,
                    patch("apps.planning.src.routes.planning.MaintenanceOrder"),
                    patch("apps.planning.src.routes.planning.TaskManager"),
                    patch("apps.planning.src.routes.planning." "LineConditionManager"),
                    patch("apps.planning.src.routes.planning.g") as mock_g,
                ):
                    mock_schedule = MagicMock()
                    MockSchedule.query.get_or_404.return_value = mock_schedule

                    mock_config = {
                        "shift_durations": {
                            "shift_break": 10,
                            "weekend": 20,
                        }
                    }
                    mock_load_config.return_value = mock_config

                    mock_query = MockPlanningTask.query
                    task_query = mock_query.filter_by.return_value
                    task_query.all.return_value = []

                    mock_g.db = MagicMock()

                    view_schedule(1)

                    args, kwargs = mock_render.call_args
                    assert "shift_config" in kwargs
                    assert kwargs["shift_config"] == mock_config
