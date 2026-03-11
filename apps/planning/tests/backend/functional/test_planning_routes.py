import time
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from apps.planning.src.routes.planning import (
    SESSION_TIMEOUT_SECONDS,
    cleanup_expired_sessions,
    get_session_data,
    is_session_valid,
    session_excel_data_cache,
    store_session_data,
    update_session_timestamp,
)


@pytest.fixture
def mock_session_cache():
    # Clear cache before and after test
    session_excel_data_cache.clear()
    yield
    session_excel_data_cache.clear()


class TestPlanningRoutes:
    """Consolidated Test Suite for Planning Routes.

    Includes tests for:
    - Session management internals
    - Route access (Index, Manage Mappings)
    - File Uploads
    - Dashboard Generation
    - Schedule execution (Run, Publish, Gantt)
    - Error handling
    """

    @pytest.fixture(autouse=True)
    def setup_app_context(self, app):
        with app.app_context():
            yield

    @pytest.fixture(autouse=True)
    def mock_db_g(self, app):
        with app.app_context():
            with patch("sqlite3.connect") as mock_connect:
                mock_db = mock_connect.return_value
                mock_cursor = MagicMock()
                mock_db.cursor.return_value = mock_cursor
                mock_cursor.execute.return_value = mock_cursor
                yield mock_db

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def test_cleanup_expired_sessions(self, mock_session_cache):
        """Test session cleanup logic."""
        current = time.time()
        session_excel_data_cache["valid"] = {"timestamp": current}
        session_excel_data_cache["expired"] = {
            "timestamp": current - SESSION_TIMEOUT_SECONDS - 10
        }
        cleanup_expired_sessions()
        assert "valid" in session_excel_data_cache
        assert "expired" not in session_excel_data_cache

    def test_is_session_valid(self, mock_session_cache):
        """Test session validation helper."""
        current = time.time()
        session_excel_data_cache["valid"] = {"timestamp": current}
        session_excel_data_cache["expired"] = {
            "timestamp": current - SESSION_TIMEOUT_SECONDS - 10
        }
        assert is_session_valid("valid") is True
        assert is_session_valid("expired") is False
        assert is_session_valid("nonexistent") is False

    def test_store_and_get_session_data(self, mock_session_cache):
        """Test session data storage and retrieval."""
        store_session_data("test_id", {"key": "value"})
        assert "test_id" in session_excel_data_cache
        data = get_session_data("test_id")
        assert data == {"key": "value"}

        # Access updates timestamp
        with patch("apps.planning.src.routes.planning.time.time") as mock_time:
            mock_time.return_value = time.time() + 100
            update_session_timestamp("test_id")
            assert (
                session_excel_data_cache["test_id"]["timestamp"]
                == mock_time.return_value
            )

    # =========================================================================
    # BASIC ROUTES
    # =========================================================================

    def test_index_route(self, client):
        """Test the main planning dashboard route."""
        response = client.get("/planning/")
        assert response.status_code == 200

    def test_manage_mappings_route(self, client):
        """Test the manage mappings UI route."""
        response = client.get("/planning/manage_mappings_ui")
        assert response.status_code == 200

    def test_output_file_route_nonexistent(self, client, app):
        """Test output file route for nonexistent/invalid file."""
        app.config.setdefault("OUTPUT_FOLDER", ".")
        response = client.get("/planning/output/nonexistent.html")
        assert response.status_code in [404, 500]

    # =========================================================================
    # UPLOAD & DASHBOARD
    # =========================================================================

    def test_upload_file_success(self, auth_client):
        """Test successful Excel file upload."""
        session_id = "valid_Upload_session"
        excel_content = b"fake_excel_content"

        with (
            patch("apps.planning.src.routes.planning.pd") as mock_pd,
            patch("apps.planning.src.routes.planning.extract_data") as mock_extract,
            patch("apps.planning.src.routes.planning.store_session_data") as mock_store,
            patch("apps.planning.src.routes.planning.sanitize_data") as mock_sanitize,
            patch(
                "apps.planning.src.routes.planning.get_current_week_number",
                return_value=10,
            ),
        ):
            mock_xls = MagicMock()
            mock_xls.sheet_names = ["Summary KW10"]
            mock_pd.ExcelFile.return_value.__enter__.return_value = mock_xls

            mock_data_list = [{"scheduler_group_task": "Task A", "task_type": "PM"}]
            mock_extract.return_value = (mock_data_list, [])
            mock_sanitize.return_value = [
                {"id": "1", "name": "Task A", "task_type": "PM"}
            ]

            response = auth_client.post(
                "/planning/upload",
                data={
                    "session_id": session_id,
                    "excelFile": (BytesIO(excel_content), "test.xlsx"),
                },
                content_type="multipart/form-data",
            )

            assert response.status_code == 200
            assert "File processed" in response.json.get("message", "")
            mock_store.assert_called()

    def test_upload_file_weeks_mismatch(self, client):
        """Test upload validation for week mismatch."""
        mock_xls = MagicMock()
        mock_xls.sheet_names = ["Summary KW01"]

        with patch(
            "apps.planning.src.routes.planning.pd.ExcelFile", return_value=mock_xls
        ):
            with patch(
                "apps.planning.src.routes.planning.get_current_week_number",
                return_value=5,
            ):
                response = client.post(
                    "/planning/upload",
                    data={
                        "session_id": "valid_id",
                        "excelFile": (BytesIO(b"dummy"), "test.xlsx"),
                    },
                    content_type="multipart/form-data",
                )
                assert response.status_code == 400
                assert "Week mismatch" in response.json.get("message", "")

    def test_upload_errors(self, client):
        """Test various upload error conditions."""
        # Missing Session
        assert client.post("/planning/upload", data={}).status_code == 400

        # Invalid Session Format
        assert (
            client.post("/planning/upload", data={"session_id": "bad/id"}).status_code
            == 400
        )

        # No file or technicians
        assert (
            client.post("/planning/upload", data={"session_id": "valid_id"}).status_code
            == 400
        )

    def test_generate_dashboard_success(self, auth_client, app, tmp_path):
        """Test successful dashboard generation."""
        session_id = "sess_dash_ok"
        app.config["OUTPUT_FOLDER"] = str(tmp_path)

        with (
            patch(
                "apps.planning.src.routes.planning.is_session_valid", return_value=True
            ),
            patch(
                "apps.planning.src.routes.planning.get_session_data"
            ) as mock_get_sess,
            patch("apps.planning.src.routes.planning.update_session_timestamp"),
            patch("apps.planning.src.routes.planning.TaskManager") as MockTM,
            patch(
                "apps.planning.src.routes.planning.get_all_technician_skills_by_name",
                return_value={},
            ),
            patch(
                "apps.planning.src.routes.planning.generate_html_files"
            ) as mock_gen_html,
        ):
            mock_get_sess.return_value = [
                {"id": "1", "name": "Task 1", "task_type": "PM"}
            ]
            mock_tm_instance = MockTM.return_value
            mock_tm_instance.get_or_create.return_value = 101
            mock_tm_instance.get_required_skills.return_value = [
                {"technology_id": "T1"}
            ]
            mock_gen_html.return_value = ({"Tech A": 100}, [])

            response = auth_client.post(
                "/planning/generate_dashboard",
                data={
                    "session_id": session_id,
                    "present_technicians": '["Tech A"]',
                    "rep_assignments": "[]",
                    "all_processed_tasks": '[{"id": "1", "name": "Task 1"}]',
                },
            )

            assert response.status_code == 200
            assert "Dashboard generated" in response.json["message"]

    # =========================================================================
    # SCHEDULE OPERATIONS
    # =========================================================================

    def test_create_schedule_validation_error(self, auth_client):
        """Test create-schedule route validation error."""
        response = auth_client.post(
            "/planning/schedules/create", data={"name": "New Schedule"}
        )
        assert response.status_code == 400
        assert "All fields are required" in response.json["error"]

    def test_run_planning_locked_schedule(self, client, app):
        """Test running planning on locked schedule."""
        with app.app_context():
            with patch("apps.planning.src.routes.planning.db.get_or_404") as mock_get:
                mock_schedule = MagicMock()
                mock_schedule.planning_status = "Locked"
                mock_get.return_value = mock_schedule

                response = client.post("/planning/schedules/1/run")
                assert response.status_code == 400
                assert (
                    "Cannot run planning on a locked schedule" in response.json["error"]
                )

    def test_run_planning_success(self, client, app):
        """Test successful planning run."""
        with app.app_context():
            schedule = MagicMock()
            schedule.id = 1
            schedule.planning_status = "Draft"

            # Create concrete objects/mocks with concrete attributes
            mock_pt = MagicMock()
            mock_pt.maintenance_order_id = 101
            # Ensure attributes are not Mocks
            mock_pt.status = "Unplanned"
            mock_pt.assigned_user_id = None

            with (
                patch(
                    "apps.planning.src.routes.planning.db.get_or_404",
                    return_value=schedule,
                ),
                patch("apps.planning.src.routes.planning.db.session"),
                patch(
                    "apps.planning.src.routes.planning.PlanningTask.query"
                ) as mock_pt_query,
                patch("apps.planning.src.routes.planning.PlanningEngine") as MockEngine,
            ):
                mock_pt_query.filter_by.return_value.all.return_value = [mock_pt]
                mock_pt_query.filter_by.return_value.first.return_value = mock_pt

                engine_instance = MockEngine.return_value
                result = MagicMock()
                result.unassigned_tasks = []

                # Mock assignment object
                assignment = MagicMock()
                assignment.maintenance_order_id = 101
                assignment.assigned_technician_ids = [99]
                # Add dates if needed by code
                assignment.planned_start_time = None
                assignment.planned_end_time = None
                assignment.actual_duration_minutes = 60

                result.assigned_tasks = [assignment]

                # Setup statistics with to_dict returning real dict
                stats_mock = MagicMock()
                stats_mock.to_dict.return_value = {
                    "assigned_tasks": 1,
                    "unassigned_tasks": 0,
                }
                # Also set attributes directly in case code accesses them
                stats_mock.assigned_tasks = 1
                stats_mock.unassigned_tasks = 0

                result.statistics = stats_mock
                result.warnings = []

                engine_instance.generate_plan.return_value = result

                response = client.post(
                    "/planning/schedules/1/run",
                    data={"planning_mode": "weekend"},
                )

                assert response.status_code == 200
                assert response.json["success"] is True

    def test_view_schedule_populated(self, client, app):
        """Test viewing a populated schedule."""
        with app.app_context():
            with patch(
                "apps.planning.src.routes.planning.db.get_or_404"
            ) as mock_get_schedule:
                # Setup Schedule
                schedule = MagicMock()
                schedule.id = 1
                schedule.name = "Test Schedule"
                mock_get_schedule.return_value = schedule

                # Setup Task
                pt = MagicMock()
                # Set concrete values to avoid JSON serialization errors
                pt.status = "Planned"
                pt.maintenance_order_id = 101
                pt.assigned_user.username = "UserA"

                # Setup MO
                mo = MagicMock()
                mo.id = 101
                mo.title = "Test Order"
                mo.description = "Test Order Description"
                mo.order_type = "PM"
                mo.priority = 1
                mo.estimated_completion_time = 60
                mo.labour_count = 1

                # Required skills (iterable of objects with .name)
                skill_mock = MagicMock()
                skill_mock.name = "Mechanic"
                mo.required_skills = [skill_mock]

                # User skills
                us_mock = MagicMock()
                us_mock.skill.name = "Mechanic"
                pt.assigned_user.skills = [us_mock]

                def mock_get_fn(model, id):
                    if id == 101:
                        return mo
                    return None

                with (
                    patch(
                        "apps.planning.src.routes.planning.PlanningTask.query"
                    ) as mock_pt_query,
                    patch(
                        "apps.planning.src.routes.planning.db.session.get",
                        side_effect=mock_get_fn,
                    ),
                    patch(
                        "apps.planning.src.routes.planning.load_shift_config",
                        return_value={},
                    ),
                ):
                    mock_pt_query.filter_by.return_value.all.return_value = [pt]

                    response = client.get("/planning/schedules/1")
                    assert response.status_code == 200
                    assert b"Test Order" in response.data
                    assert b"UserA" in response.data

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    def test_run_planning_error(self, client, app):
        """Test error during planning run."""
        with app.app_context():
            with patch("apps.planning.src.routes.planning.db.get_or_404") as mock_get:
                mock_get.side_effect = Exception("Database BOOM")
                response = client.post("/planning/schedules/1/run")
                assert response.status_code == 500
                assert "Database BOOM" in response.json["error"]
