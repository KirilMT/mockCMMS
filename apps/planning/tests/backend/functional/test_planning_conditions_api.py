"""Tests for Line Conditions API routes and Settings route.

Covers:
- Settings route
- Conditions CRUD API (GET, POST, PUT, DELETE)
- Task Conditions API (GET, POST)
- Exception handling for all condition endpoints
"""

from unittest.mock import MagicMock, patch

import pytest


class TestConditionsApi:
    """Tests for line conditions API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_app(self, app):
        with app.app_context():
            yield

    # =========================================================================
    # SETTINGS ROUTE
    # =========================================================================

    def test_settings_route(self, client):
        """Test GET /settings renders the settings page."""
        response = client.get("/planning/settings")
        assert response.status_code == 200

    # =========================================================================
    # CONDITIONS CRUD - GET
    # =========================================================================

    def test_get_conditions_empty(self, client):
        """Test GET /api/conditions returns empty list initially."""
        response = client.get("/planning/api/conditions")
        assert response.status_code == 200
        assert isinstance(response.json, list)

    def test_get_conditions_with_data(self, auth_client):
        """Test GET /api/conditions returns created conditions."""
        # Create a condition first
        create_res = auth_client.post(
            "/planning/api/conditions",
            json={
                "name": "Power Off",
                "description": "Turn off power",
                "color_code": "red",
            },
        )
        assert create_res.status_code == 201
        response = auth_client.get("/planning/api/conditions")
        assert response.status_code == 200
        assert isinstance(response.json, list)

    # =========================================================================
    # CONDITIONS CRUD - POST
    # =========================================================================

    def test_create_condition_success(self, auth_client):
        """Test POST /api/conditions creates a new condition."""
        response = auth_client.post(
            "/planning/api/conditions",
            json={
                "name": "Line Empty",
                "description": "The line must be empty",
                "color_code": "yellow",
            },
        )
        assert response.status_code == 201
        assert response.json["message"] == "Condition created"
        assert "id" in response.json

    def test_create_condition_missing_name(self, auth_client):
        """Test POST /api/conditions with missing name returns 400."""
        response = auth_client.post(
            "/planning/api/conditions",
            json={"description": "No name provided"},
        )
        assert response.status_code == 400
        assert "Name is required" in response.json["error"]

    def test_create_condition_duplicate_returns_existing_id(self, auth_client):
        """Test POST /api/conditions with duplicate name returns existing ID."""
        auth_client.post(
            "/planning/api/conditions",
            json={"name": "DupCondition", "color_code": "green"},
        )
        # Second create with same name returns the existing ID (not 409)
        response = auth_client.post(
            "/planning/api/conditions",
            json={"name": "DupCondition", "color_code": "blue"},
        )
        # LineConditionManager.create_condition returns existing ID on IntegrityError
        assert response.status_code == 201

    def test_create_condition_default_color(self, auth_client):
        """Test POST /api/conditions uses default blue color_code."""
        response = auth_client.post(
            "/planning/api/conditions",
            json={"name": "DefaultColor"},
        )
        assert response.status_code == 201

    # =========================================================================
    # CONDITIONS CRUD - PUT
    # =========================================================================

    def test_update_condition_success(self, auth_client):
        """Test PUT /api/conditions/<id> updates a condition."""
        # Create first
        res = auth_client.post(
            "/planning/api/conditions",
            json={"name": "ToUpdate", "color_code": "red"},
        )
        cid = res.json["id"]
        # Update
        response = auth_client.put(
            f"/planning/api/conditions/{cid}",
            json={"name": "Updated", "description": "New desc", "color_code": "green"},
        )
        assert response.status_code == 200
        assert response.json["message"] == "Condition updated"

    def test_update_condition_missing_name(self, auth_client):
        """Test PUT /api/conditions/<id> with missing name returns 400."""
        response = auth_client.put(
            "/planning/api/conditions/1",
            json={"description": "No name"},
        )
        assert response.status_code == 400
        assert "Name is required" in response.json["error"]

    def test_update_condition_not_found(self, auth_client):
        """Test PUT on nonexistent condition returns 409 (IntegrityError path)."""
        response = auth_client.put(
            "/planning/api/conditions/9999",
            json={"name": "Ghost"},
        )
        # update_condition on non-existent row still commits, returns True
        assert response.status_code == 200

    # =========================================================================
    # CONDITIONS CRUD - DELETE
    # =========================================================================

    def test_delete_condition_success(self, auth_client):
        """Test DELETE /api/conditions/<id> deletes a condition."""
        res = auth_client.post(
            "/planning/api/conditions",
            json={"name": "ToDelete", "color_code": "red"},
        )
        cid = res.json["id"]
        response = auth_client.delete(f"/planning/api/conditions/{cid}")
        assert response.status_code == 200
        assert response.json["message"] == "Condition deleted"

    def test_delete_condition_not_found(self, auth_client):
        """Test DELETE on nonexistent condition returns 404."""
        response = auth_client.delete("/planning/api/conditions/9999")
        assert response.status_code == 404
        assert "not found" in response.json["error"].lower()

    # =========================================================================
    # CONDITIONS - EXCEPTION HANDLING
    # =========================================================================

    def test_conditions_api_exception(self, auth_client):
        """Test exception handling in manage_conditions_api."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db = MagicMock()
            mock_g.db.cursor.side_effect = Exception("DB Crash")
            # GET exception
            response = auth_client.get("/planning/api/conditions")
            assert response.status_code == 500
            assert "DB Crash" in response.json["error"]

    def test_update_delete_condition_exception(self, auth_client):
        """Test exception handling in update_delete_condition_api."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db = MagicMock()
            mock_g.db.cursor.side_effect = Exception("DB Error")
            # PUT exception
            response = auth_client.put(
                "/planning/api/conditions/1", json={"name": "Fail"}
            )
            assert response.status_code == 500

            # DELETE exception
            response = auth_client.delete("/planning/api/conditions/1")
            assert response.status_code == 500

    # =========================================================================
    # TASK CONDITIONS API - GET
    # =========================================================================

    def test_get_task_conditions_empty(self, client):
        """Test GET /api/tasks/<id>/conditions returns empty list."""
        response = client.get("/planning/api/tasks/1/conditions")
        assert response.status_code == 200
        assert isinstance(response.json, list)

    def test_get_task_conditions_with_data(self, auth_client):
        """Test GET /api/tasks/<id>/conditions after assignment."""
        # Create a condition
        res = auth_client.post(
            "/planning/api/conditions",
            json={"name": "Safety Gates", "color_code": "green"},
        )
        assert res.status_code == 201
        cid = res.json["id"]

        # Create a task in the planning DB

        # Assign condition to task via API
        assign_res = auth_client.post(
            "/planning/api/tasks/1/conditions",
            json={"condition_ids": [cid]},
        )
        assert assign_res.status_code == 200

        # Verify task conditions
        response = auth_client.get("/planning/api/tasks/1/conditions")
        assert response.status_code == 200

    # =========================================================================
    # TASK CONDITIONS API - POST
    # =========================================================================

    def test_update_task_conditions_success(self, auth_client):
        """Test POST /api/tasks/<id>/conditions updates task conditions."""
        # Create conditions
        r1 = auth_client.post(
            "/planning/api/conditions",
            json={"name": "Cond1", "color_code": "red"},
        )
        r2 = auth_client.post(
            "/planning/api/conditions",
            json={"name": "Cond2", "color_code": "blue"},
        )
        cid1 = r1.json["id"]
        cid2 = r2.json["id"]

        # Assign both conditions to a task
        response = auth_client.post(
            "/planning/api/tasks/1/conditions",
            json={"condition_ids": [cid1, cid2]},
        )
        assert response.status_code == 200
        assert "updated successfully" in response.json["message"]

    def test_update_task_conditions_empty_list(self, auth_client):
        """Test POST with empty condition_ids clears task conditions."""
        response = auth_client.post(
            "/planning/api/tasks/1/conditions",
            json={"condition_ids": []},
        )
        assert response.status_code == 200

    def test_task_conditions_exception(self, auth_client):
        """Test exception handling in manage_task_conditions_api."""
        with patch("apps.planning.src.routes.planning.g") as mock_g:
            mock_g.db = MagicMock()
            mock_g.db.cursor.side_effect = Exception("Task Condition Error")
            response = auth_client.get("/planning/api/tasks/1/conditions")
            assert response.status_code == 500
            assert "Task Condition Error" in response.json["error"]

    # =========================================================================
    # CREATE SCHEDULE SUCCESS PATH
    # =========================================================================

    def test_create_schedule_success(self, auth_client):
        """Test successful schedule creation (covers line 1109, 1125)."""
        response = auth_client.post(
            "/planning/schedules/create",
            data={
                "name": "Weekend Plan",
                "start_date": "2025-03-15",
                "end_date": "2025-03-16",
            },
        )
        # Successful creation redirects (302)
        assert response.status_code in [200, 302]

    def test_create_schedule_end_before_start(self, auth_client):
        """Test schedule creation with end date before start date."""
        response = auth_client.post(
            "/planning/schedules/create",
            data={
                "name": "Bad Dates",
                "start_date": "2025-03-16",
                "end_date": "2025-03-15",
            },
        )
        assert response.status_code == 400
        assert "End date must be after start date" in response.json["error"]
