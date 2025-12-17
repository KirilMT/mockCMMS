import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from apps.planning.src.routes.planning import view_schedule, planning_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    # We don't need to register blueprint if we call view_schedule directly,
    # but we need app context.
    return app


def test_view_schedule_passes_config(app):
    with app.app_context():
        with patch("apps.planning.src.routes.planning.Schedule") as MockSchedule:
            with patch(
                "apps.planning.src.routes.planning.render_template"
            ) as mock_render:
                with patch(
                    "apps.planning.src.routes.planning.load_shift_config"
                ) as mock_load_config:
                    with patch(
                        "apps.planning.src.routes.planning.PlanningTask"
                    ) as MockPlanningTask:
                        with patch(
                            "apps.planning.src.routes.planning.MaintenanceOrder"
                        ) as MockMO:

                            # Setup mocks
                            mock_schedule = MagicMock()
                            MockSchedule.query.get_or_404.return_value = mock_schedule

                            mock_config = {
                                "shift_durations": {"shift_break": 10, "weekend": 20}
                            }
                            mock_load_config.return_value = mock_config

                            MockPlanningTask.query.filter_by.return_value.all.return_value = (
                                []
                            )

                            # Call the view function directly
                            # We need to mock request args
                            with app.test_request_context(
                                "/planning/schedules/1?mode=shift_break"
                            ):
                                view_schedule(1)

                                # Check if render_template was called with shift_config
                                args, kwargs = mock_render.call_args
                                assert "shift_config" in kwargs
                                assert kwargs["shift_config"] == mock_config
