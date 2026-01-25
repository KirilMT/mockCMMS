"""Comprehensive tests for Planning API routes.

Covers:
- Technicians API (CRUD operations)
- Satellite Points API (CRUD operations)
- Lines API (CRUD operations)
- Technologies and Groups API (GET operations)
- Technician Mappings API (GET operation)
- Health check endpoints
- Schedule management (Phase 3 routes)
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPlanningApi:
    """Tests for Planning API endpoints covering full route coverage."""

    @pytest.fixture(autouse=True)
    def setup_app(self, app):
        with app.app_context():
            yield

    # =========================================================================
    # TECHNICIANS API TESTS
    # =========================================================================

    def test_technicians_get(self, client):
        """Test GET /api/technicians returns technician groups."""
        res = client.get("/planning/api/technicians")
        assert res.status_code == 200
        assert isinstance(res.json, dict)

    def test_technicians_post_success(self, auth_client):
        """Test successful technician creation."""
        res = auth_client.post(
            "/planning/api/technicians",
            json={"name": "NewTech", "satellite_point_id": None},
        )
        assert res.status_code == 201
        assert "NewTech" in res.json.get("message", "")

    def test_technicians_post_missing_name(self, auth_client):
        """Test POST with missing name returns 400."""
        res = auth_client.post("/planning/api/technicians", json={"name": ""})
        assert res.status_code == 400

    def test_technicians_post_duplicate(self, auth_client):
        """Test POST with duplicate name returns 409."""
        auth_client.post("/planning/api/technicians", json={"name": "DupTech"})
        res = auth_client.post("/planning/api/technicians", json={"name": "DupTech"})
        assert res.status_code == 409

    def test_technicians_post_value_error(self, auth_client):
        """Test POST with invalid satellite_point_id triggers error path."""
        res = auth_client.post(
            "/planning/api/technicians",
            json={"name": "T1", "satellite_point_id": "invalid"},
        )
        assert res.status_code == 500
        assert "value error" in res.json.get("message", "").lower()

    def test_manage_technician_put_success(self, auth_client):
        """Test successful technician update."""
        # Create first
        res1 = auth_client.post("/planning/api/technicians", json={"name": "OrigName"})
        tid = res1.json["technician"]["id"]
        # Update
        res2 = auth_client.put(
            f"/planning/api/technicians/{tid}", json={"name": "UpdatedName"}
        )
        assert res2.status_code == 200
        assert "updated" in res2.json.get("message", "").lower()

    def test_manage_technician_put_satellite_only(self, auth_client):
        """Test updating only satellite_point_id."""
        res1 = auth_client.post("/planning/api/technicians", json={"name": "SatTest"})
        tid = res1.json["technician"]["id"]
        res2 = auth_client.put(
            f"/planning/api/technicians/{tid}", json={"satellite_point_id": 1}
        )
        assert res2.status_code == 200

    def test_manage_technician_put_both_fields(self, auth_client):
        """Test updating both name and satellite_point_id."""
        res1 = auth_client.post("/planning/api/technicians", json={"name": "BothTest"})
        tid = res1.json["technician"]["id"]
        res2 = auth_client.put(
            f"/planning/api/technicians/{tid}",
            json={"name": "BothUpdated", "satellite_point_id": 2},
        )
        assert res2.status_code == 200

    def test_manage_technician_put_no_data(self, auth_client):
        """Test PUT with no update data returns 400."""
        res1 = auth_client.post("/planning/api/technicians", json={"name": "NoData"})
        tid = res1.json["technician"]["id"]
        res2 = auth_client.put(f"/planning/api/technicians/{tid}", json={})
        assert res2.status_code == 400

    def test_manage_technician_not_found(self, auth_client):
        """Test PUT/DELETE on non-existent technician."""
        res = auth_client.put("/planning/api/technicians/9999", json={"name": "NoOne"})
        assert res.status_code == 404

    def test_manage_technician_name_exists(self, auth_client, db_session):
        """Test PUT with existing name returns 409."""
        auth_client.post("/planning/api/technicians", json={"name": "TechA"})
        res2 = auth_client.post("/planning/api/technicians", json={"name": "TechB"})
        tid = res2.json["technician"]["id"]
        res3 = auth_client.put(
            f"/planning/api/technicians/{tid}", json={"name": "TechA"}
        )
        assert res3.status_code == 409

    def test_manage_technician_delete_success(self, auth_client):
        """Test successful technician deletion."""
        res1 = auth_client.post("/planning/api/technicians", json={"name": "ToDelete"})
        tid = res1.json["technician"]["id"]
        res2 = auth_client.delete(f"/planning/api/technicians/{tid}")
        assert res2.status_code == 200
        assert "deleted" in res2.json.get("message", "").lower()

    def test_manage_technician_delete_not_found(self, auth_client):
        """Test DELETE on non-existent technician."""
        res = auth_client.delete("/planning/api/technicians/9999")
        assert res.status_code == 404

    # =========================================================================
    # SATELLITE POINTS API TESTS
    # =========================================================================

    def test_satellite_points_get(self, client):
        """Test GET /api/satellite_points."""
        res = client.get("/planning/api/satellite_points")
        assert res.status_code == 200
        assert isinstance(res.json, list)

    def test_satellite_points_post_success(self, auth_client):
        """Test successful satellite point creation."""
        res = auth_client.post(
            "/planning/api/satellite_points", json={"name": "NewSatPoint"}
        )
        assert res.status_code == 200
        assert res.json.get("name") == "NewSatPoint"

    def test_satellite_points_post_no_name(self, auth_client):
        """Test POST with empty name."""
        res = auth_client.post("/planning/api/satellite_points", json={"name": ""})
        assert res.status_code == 200
        assert "required" in res.json.get("error", "").lower()

    def test_satellite_points_post_exception(self, auth_client):
        """Test POST with db exception."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("Crash")
            res = auth_client.post(
                "/planning/api/satellite_points", json={"name": "CrashMe"}
            )
            assert res.status_code == 200

    def test_manage_satellite_point_put(self, auth_client):
        """Test PUT /api/satellite_points/<id>."""
        # Create first
        auth_client.post("/planning/api/satellite_points", json={"name": "SP1"})
        res = auth_client.put(
            "/planning/api/satellite_points/1", json={"name": "SP1Up"}
        )
        assert res.status_code == 200

    def test_manage_satellite_point_put_empty(self, auth_client):
        """Test PUT with empty name."""
        res = auth_client.put("/planning/api/satellite_points/1", json={"name": ""})
        assert res.status_code == 200

    def test_manage_satellite_point_delete(self, auth_client):
        """Test DELETE /api/satellite_points/<id>."""
        auth_client.post("/planning/api/satellite_points", json={"name": "ToDelete"})
        res = auth_client.delete("/planning/api/satellite_points/1")
        assert res.status_code == 200

    def test_satellite_points_put_delete_exceptions(self, auth_client):
        """Cover exception paths for satellite points PUT/DELETE."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("DB Fail")

            # Cover PUT exception
            res_put = auth_client.put(
                "/planning/api/satellite_points/1", json={"name": "Fail"}
            )
            assert res_put.status_code == 200

            # Cover DELETE exception
            res_del = auth_client.delete("/planning/api/satellite_points/1")
            assert res_del.status_code == 200

    # =========================================================================
    # LINES API TESTS
    # =========================================================================

    def test_lines_get(self, client):
        """Test GET /api/lines."""
        res = client.get("/planning/api/lines")
        assert res.status_code == 200
        assert isinstance(res.json, list)

    def test_lines_post_success(self, auth_client):
        """Test successful line creation."""
        res = auth_client.post("/planning/api/lines", json={"name": "Line1"})
        assert res.status_code == 200
        assert res.json.get("name") == "Line1"

    def test_lines_post_no_name(self, auth_client):
        """Test POST with empty name."""
        res = auth_client.post("/planning/api/lines", json={"name": ""})
        assert res.status_code == 200
        assert "required" in res.json.get("error", "").lower()

    def test_lines_post_exception(self, auth_client):
        """Test POST with db exception."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("Crash")
            res = auth_client.post("/planning/api/lines", json={"name": "CrashLine"})
            assert res.status_code == 200

    def test_manage_line_put(self, auth_client):
        """Test PUT /api/lines/<id>."""
        auth_client.post("/planning/api/lines", json={"name": "L1"})
        res = auth_client.put("/planning/api/lines/1", json={"name": "L1Updated"})
        assert res.status_code == 200

    def test_manage_line_put_empty(self, auth_client):
        """Test PUT with empty name."""
        res = auth_client.put("/planning/api/lines/1", json={"name": ""})
        assert res.status_code == 200

    def test_manage_line_delete(self, auth_client):
        """Test DELETE /api/lines/<id>."""
        auth_client.post("/planning/api/lines", json={"name": "ToDeleteLine"})
        res = auth_client.delete("/planning/api/lines/1")
        assert res.status_code == 200

    def test_lines_put_delete_exceptions(self, auth_client):
        """Cover exception paths for lines PUT/DELETE."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("DB Fail")

            # Cover PUT exception
            res_put = auth_client.put("/planning/api/lines/1", json={"name": "Fail"})
            assert res_put.status_code == 200

            # Cover DELETE exception
            res_del = auth_client.delete("/planning/api/lines/1")
            assert res_del.status_code == 200

    # =========================================================================
    # TECHNOLOGIES AND GROUPS API TESTS
    # =========================================================================

    def test_technologies_get(self, client):
        """Test GET /api/technologies."""
        res = client.get("/planning/api/technologies")
        assert res.status_code == 200
        assert isinstance(res.json, list)

    def test_technologies_get_exception(self, client):
        """Test GET /api/technologies with db error."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("DB Fail")
            res = client.get("/planning/api/technologies")
            assert res.status_code == 200
            assert res.json == []

    def test_technology_groups_get(self, client):
        """Test GET /api/technology_groups."""
        res = client.get("/planning/api/technology_groups")
        assert res.status_code == 200
        assert isinstance(res.json, list)

    def test_technology_groups_get_exception(self, client):
        """Test GET /api/technology_groups with db error."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("DB Fail")
            res = client.get("/planning/api/technology_groups")
            assert res.status_code == 200
            assert res.json == []

    def test_technician_groups_get(self, client):
        """Test GET /api/technician_groups."""
        res = client.get("/planning/api/technician_groups")
        assert res.status_code == 200
        assert isinstance(res.json, list)

    def test_technician_groups_get_exception(self, client):
        """Test GET /api/technician_groups with db error."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("DB Fail")
            res = client.get("/planning/api/technician_groups")
            assert res.status_code == 200
            assert res.json == []

    # =========================================================================
    # TECHNICIAN MAPPINGS API TESTS
    # =========================================================================

    def test_technician_mappings_get(self, client):
        """Test GET /api/get_technician_mappings."""
        res = client.get("/planning/api/get_technician_mappings")
        assert res.status_code == 200
        assert "technicians" in res.json

    def test_technician_mappings_get_error(self, client):
        """Test GET with db error returns 500."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db.cursor.side_effect = Exception("DB Error")
            res = client.get("/planning/api/get_technician_mappings")
            assert res.status_code == 500
            assert "error" in res.json

    # =========================================================================
    # TASKS API TESTS
    # =========================================================================

    def test_tasks_api_missing_fields(self, auth_client):
        """Test POST /api/tasks with missing fields."""
        res = auth_client.post("/planning/api/tasks", json={})
        assert res.status_code == 400

    def test_tasks_api_no_tech_ids(self, auth_client):
        """Test POST /api/tasks with name but no technology_ids."""
        res = auth_client.post("/planning/api/tasks", json={"name": "Task1"})
        assert res.status_code == 400

    def test_tasks_api_success(self, auth_client):
        """Test successful task creation."""
        with patch("apps.planning.src.routes.planning.TaskManager") as MockTM:
            mock_instance = MockTM.return_value
            mock_instance.get_by_name.return_value = None
            mock_instance.get_or_create.return_value = 1
            res = auth_client.post(
                "/planning/api/tasks",
                json={"name": "NewTask", "technology_ids": [1, 2]},
            )
            assert res.status_code == 201

    def test_tasks_api_duplicate(self, auth_client):
        """Test POST with duplicate task name returns 409."""
        with patch("apps.planning.src.routes.planning.TaskManager") as MockTM:
            mock_instance = MockTM.return_value
            mock_instance.get_by_name.return_value = {"id": 1, "name": "Dup"}
            res = auth_client.post(
                "/planning/api/tasks", json={"name": "Dup", "technology_ids": [1]}
            )
            assert res.status_code == 409

    def test_tasks_api_exception(self, auth_client):
        """Test POST with server error."""
        with patch("apps.planning.src.routes.planning.TaskManager") as MockTM:
            MockTM.side_effect = Exception("Boom")
            res = auth_client.post(
                "/planning/api/tasks", json={"name": "ErrTask", "technology_ids": [1]}
            )
            assert res.status_code == 500

    # =========================================================================
    # HEALTH CHECK ENDPOINTS
    # =========================================================================

    def test_health_check(self, client):
        """Test GET /health/ endpoint."""
        with patch("apps.planning.src.routes.planning.HealthChecker") as MockChecker:
            mock_instance = MockChecker.return_value
            mock_instance.perform_full_health_check.return_value = {"status": "healthy"}
            res = client.get("/planning/health/")
            assert res.status_code == 200
            assert res.json.get("status") == "healthy"

    def test_health_check_unhealthy(self, client):
        """Test unhealthy status returns 503."""
        with patch("apps.planning.src.routes.planning.HealthChecker") as MockChecker:
            mock_instance = MockChecker.return_value
            mock_instance.perform_full_health_check.return_value = {
                "status": "unhealthy"
            }
            res = client.get("/planning/health/")
            assert res.status_code == 503

    def test_health_check_exception(self, client):
        """Test health check with exception."""
        with patch("apps.planning.src.routes.planning.HealthChecker") as MockChecker:
            MockChecker.side_effect = Exception("Health system failure")
            res = client.get("/planning/health/")
            assert res.status_code == 503

    def test_readiness_check(self, client):
        """Test GET /health/ready endpoint."""
        with patch("apps.planning.src.routes.planning.HealthChecker") as MockChecker:
            mock_instance = MockChecker.return_value
            mock_instance.check_database_health.return_value = (True, {})
            mock_instance.check_configuration_health.return_value = (True, {})
            res = client.get("/planning/health/ready")
            assert res.status_code == 200
            assert res.json.get("status") == "ready"

    def test_readiness_check_not_ready(self, client):
        """Test readiness returns 503 when not ready."""
        with patch("apps.planning.src.routes.planning.HealthChecker") as MockChecker:
            mock_instance = MockChecker.return_value
            mock_instance.check_database_health.return_value = (False, {})
            mock_instance.check_configuration_health.return_value = (True, {})
            res = client.get("/planning/health/ready")
            assert res.status_code == 503

    def test_liveness_check(self, client):
        """Test GET /health/live endpoint."""
        res = client.get("/planning/health/live")
        assert res.status_code == 200
        assert res.json.get("status") == "alive"

    def test_metrics_endpoint(self, client):
        """Test GET /health/metrics endpoint."""
        with patch("apps.planning.src.routes.planning.HealthChecker") as MockChecker:
            mock_instance = MockChecker.return_value
            mock_instance.get_application_metrics.return_value = {"uptime": 100}
            res = client.get("/planning/health/metrics")
            assert res.status_code == 200

    def test_debug_info(self, client, app):
        """Test GET /health/debug endpoint (only in debug mode)."""
        app.config["FLASK_DEBUG"] = True
        res = client.get("/planning/health/debug")
        # Returns 200 if in debug
        assert res.status_code == 200

    # =========================================================================
    # SCHEDULE MANAGEMENT (Phase 3 Routes)
    # =========================================================================

    def test_list_routes(self, client):
        """Test debug route listing endpoint."""
        res = client.get("/planning/debug/routes")
        assert res.status_code == 200
        assert isinstance(res.json, list)

    def test_planning_index(self, client):
        """Test main planning page."""
        res = client.get("/planning/planning")
        # This route might render template or error, but let's confirm 200 OK
        assert res.status_code == 200

    def test_create_schedule_method_allowed(self, client):
        """Test GET /schedules/create returns 405 (Method Not Allowed)."""
        res = client.get("/planning/schedules/create")
        assert res.status_code == 405

    # =========================================================================
    # GANTT AND PUBLISH TESTS (Coverage Maximization)
    # =========================================================================

    def test_gantt_data_success(self, client, app):
        """Test Gantt data retrieval success flow."""
        with app.app_context():
            from datetime import datetime

            # Mock DB models
            mock_schedule = MagicMock()
            mock_schedule.start_date = datetime(2025, 1, 1)
            mock_schedule.end_date = datetime(2025, 1, 5)
            mock_schedule.name = "Test Schedule"
            mock_schedule.planning_status = "Draft"
            mock_schedule.id = 1

            mock_pt = MagicMock()
            mock_pt.id = 100
            mock_pt.status = "Planned"
            mock_pt.planned_start_time.isoformat.return_value = "2025-01-02T08:00:00"
            mock_pt.planned_end_time.isoformat.return_value = "2025-01-02T10:00:00"
            mock_pt.actual_duration_minutes = 120

            mock_mo = MagicMock()
            mock_mo.id = 500
            mock_mo.description = "Test MO"
            mock_mo.estimated_completion_time = 120
            mock_mo.priority = 1
            mock_mo.order_type = "PM"
            mock_mo.required_skills = []

            mock_pt.maintenance_order = mock_mo
            mock_pt.assigned_user.username = "Tech1"
            mock_pt.assigned_user.id = 10

            with patch(
                "apps.planning.src.routes.planning.db.get_or_404",
                return_value=mock_schedule,
            ):
                with patch(
                    "apps.planning.src.routes.planning.PlanningTask.query"
                ) as mock_pt_query:
                    mock_pt_query.filter_by.return_value.all.return_value = [mock_pt]
                    with patch(
                        "apps.planning.src.routes.planning.User.query"
                    ) as mock_user_query:
                        chain = mock_user_query.join.return_value.filter.return_value
                        chain.all.return_value = []
                        t1 = MagicMock()
                        t1.name = "T1"
                        t1.id = 1
                        t2 = MagicMock()
                        t2.name = "T2"
                        t2.id = 2
                        with patch(
                            "src.services.shift_utils.get_shift_teams",
                            return_value=(t1, t2),
                        ):
                            with patch(
                                "apps.planning.src.routes.planning.Team.query.all",
                                return_value=[],
                            ):
                                res = client.get("/planning/schedules/1/gantt-data")
                                assert res.status_code == 200
                                assert res.json["schedule"]["id"] == mock_schedule.id

    def test_gantt_data_missing_mo(self, client, app):
        """Test Gantt data skipping task with missing MO."""
        with app.app_context():
            from datetime import datetime

            mock_schedule = MagicMock()
            mock_schedule.start_date = datetime(2025, 1, 1)
            mock_schedule.end_date = datetime(2025, 1, 5)
            mock_schedule.name = "Test Schedule"
            mock_schedule.planning_status = "Draft"
            mock_schedule.id = 1

            mock_pt = MagicMock()
            mock_pt.maintenance_order = None  # Missing MO logic

            with patch(
                "apps.planning.src.routes.planning.db.get_or_404",
                return_value=mock_schedule,
            ):
                with patch(
                    "apps.planning.src.routes.planning.PlanningTask.query"
                ) as mock_pt_query:
                    mock_pt_query.filter_by.return_value.all.return_value = [mock_pt]
                    with patch("apps.planning.src.routes.planning.User.query") as mq:
                        mq.join.return_value.filter.return_value.all.return_value = []
                        with patch(
                            "src.services.shift_utils.get_shift_teams",
                            return_value=(None, None),
                        ):
                            with patch(
                                "apps.planning.src.routes.planning.Team.query.all",
                                return_value=[],
                            ):
                                res = client.get("/planning/schedules/1/gantt-data")
                                assert res.status_code == 200
                                # Should have 0 tasks processed
                                assert len(res.json["tasks"]) == 0

    def test_gantt_data_exception(self, client):
        """Test Gantt data generation failure."""
        with patch(
            "apps.planning.src.routes.planning.db.get_or_404",
            side_effect=Exception("Explosion"),
        ):
            res = client.get("/planning/schedules/1/gantt-data")
            assert res.status_code == 500
            assert "Explosion" in res.json.get("error")

    def test_publish_schedule_success(self, client, app):
        """Test successful schedule publishing."""
        mock_schedule = MagicMock()
        mock_schedule.name = "Final Schedule"

        with app.app_context():
            with patch(
                "apps.planning.src.routes.planning.db.get_or_404",
                return_value=mock_schedule,
            ):
                with patch("apps.planning.src.routes.planning.Schedule.query"):
                    # Mock update
                    res = client.post("/planning/schedules/1/publish")
                    assert res.status_code == 200
                    assert res.json["success"] is True

    def test_publish_schedule_exception(self, client):
        """Test schedule publishing failure."""
        with patch(
            "apps.planning.src.routes.planning.db.get_or_404",
            side_effect=Exception("DB Lock"),
        ):
            with patch(
                "apps.planning.src.routes.planning.db.session.rollback"
            ) as mock_rollback:
                res = client.post("/planning/schedules/1/publish")
                assert res.status_code == 500
                assert "DB Lock" in res.json.get("error")
                mock_rollback.assert_called()
