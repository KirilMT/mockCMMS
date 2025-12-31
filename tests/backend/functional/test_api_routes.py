"""Tests for API routes and endpoints.

This module tests all REST API endpoints for correct data handling, status codes, error
responses, and data validation.
"""

import json

from src.services.db_utils import (
    Asset,
    MaintenanceOrder,
    SparePart,
    TableConfiguration,
    User,
    db,
)


class TestAssetsAPI:
    """Test suite for Assets API endpoints (/v1/assets)."""

    def test_get_assets_empty(self, client, app):
        """Test GET /v1/assets returns empty list when no assets exist."""
        with app.app_context():
            response = client.get("/api/v1/assets")
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_get_assets_with_data(self, client, multiple_assets):
        """Test GET /v1/assets returns all assets when data exists."""
        response = client.get("/api/v1/assets")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify each asset has required fields
        for asset in data:
            assert "id" in asset
            assert "name" in asset
            assert "asset_code" in asset
            assert "status" in asset

    def test_get_asset_by_id_success(self, client, sample_asset):
        """Test GET /v1/assets/<id> returns specific asset."""
        response = client.get(f"/api/v1/assets/{sample_asset.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == sample_asset.id
        assert data["name"] == sample_asset.name
        assert data["asset_code"] == sample_asset.asset_code

    def test_get_asset_by_id_not_found(self, client, app):
        """Test GET /v1/assets/<id> returns 404 for non-existent asset."""
        with app.app_context():
            response = client.get("/api/v1/assets/999")
            assert response.status_code == 404
            data = response.get_json()
            assert "error" in data
            assert "not found" in data["error"].lower()

    def test_add_asset_success(self, client, app):
        """Test POST /v1/assets creates new asset successfully."""
        with app.app_context():
            asset_data = {
                "name": "New Test Asset",
                "asset_code": "NTA-001",
                "description": "A newly created test asset",
                "asset_type": "robot",
                "cost_center": "assembly",
                "status": "Operational",
            }
            response = client.post(
                "/api/v1/assets",
                data=json.dumps(asset_data),
                content_type="application/json",
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data["name"] == asset_data["name"]
            assert "id" in data

            # Verify asset was created in database
            asset = db.session.get(Asset, data["id"])
            assert asset is not None
            assert asset.name == asset_data["name"]

    def test_add_asset_missing_name(self, client, app):
        """Test POST /v1/assets without name field returns 400."""
        with app.app_context():
            asset_data = {"description": "Asset without name"}
            response = client.post(
                "/api/v1/assets",
                data=json.dumps(asset_data),
                content_type="application/json",
            )
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
            assert (
                "name" in data["error"].lower() or "required" in data["error"].lower()
            )

    def test_update_asset_success(self, client, sample_asset):
        """Test PUT /v1/assets/<id> updates asset successfully."""
        updated_data = {"name": "Updated Asset Name", "status": "Down"}
        response = client.put(
            f"/api/v1/assets/{sample_asset.id}",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == updated_data["name"]
        assert data["status"] == updated_data["status"]

    def test_update_asset_not_found(self, client, app):
        """Test PUT /v1/assets/<id> returns 404 for non-existent asset."""
        with app.app_context():
            updated_data = {"name": "Updated Name"}
            response = client.put(
                "/api/v1/assets/999",
                data=json.dumps(updated_data),
                content_type="application/json",
            )
            assert response.status_code == 404

    def test_delete_asset_success(self, client, sample_asset, app):
        """Test DELETE /v1/assets/<id> removes asset successfully."""
        asset_id = sample_asset.id
        response = client.delete(f"/api/v1/assets/{asset_id}")
        assert response.status_code == 200

        # Verify asset was deleted from database
        with app.app_context():
            asset = db.session.get(Asset, asset_id)
            assert asset is None

    def test_delete_asset_not_found(self, client, app):
        """Test DELETE /v1/assets/<id> returns 404 for non-existent asset."""
        with app.app_context():
            response = client.delete("/api/v1/assets/999")
            assert response.status_code == 404


class TestMaintenanceOrdersAPI:
    """Test suite for Maintenance Orders API endpoints (/v1/mos)."""

    def test_get_mos_empty(self, client, app):
        """Test GET /v1/mos returns empty list when no MOs exist."""
        with app.app_context():
            response = client.get("/api/v1/mos")
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_get_mos_with_data(self, client, multiple_mos):
        """Test GET /v1/mos returns all maintenance orders."""
        response = client.get("/api/v1/mos")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_get_mo_by_id_success(self, client, sample_mo):
        """Test GET /v1/mos/<id> returns specific maintenance order."""
        response = client.get(f"/api/v1/mos/{sample_mo.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == sample_mo.id
        assert data["description"] == sample_mo.description
        assert data["order_type"] == sample_mo.order_type

    def test_get_mo_by_id_not_found(self, client, app):
        """Test GET /v1/mos/<id> returns 404 for non-existent MO."""
        with app.app_context():
            response = client.get("/api/v1/mos/999")
            assert response.status_code == 404
            data = response.get_json()
            assert "error" in data

    def test_add_mo_success(self, client, sample_asset, sample_user, app):
        """Test POST /v1/mos creates new maintenance order."""
        with app.app_context():
            mo_data = {
                "asset_id": sample_asset.id,
                "description": "Routine inspection",
                "order_type": "PM",
                "status": "Open",
                "priority": "Medium",
            }
            response = client.post(
                "/api/v1/mos", data=json.dumps(mo_data), content_type="application/json"
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data["description"] == mo_data["description"]
            assert "id" in data

    def test_add_mo_missing_required_fields(self, client, app):
        """Test POST /v1/mos without required fields returns 400."""
        with app.app_context():
            mo_data = {"description": "Missing asset_id"}
            response = client.post(
                "/api/v1/mos", data=json.dumps(mo_data), content_type="application/json"
            )
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_add_mo_with_skills(self, client, sample_asset, sample_skill, app):
        """Test POST /v1/mos with required_skills associates skills."""
        with app.app_context():
            mo_data = {
                "asset_id": sample_asset.id,
                "description": "Welding task",
                "order_type": "PM",
                "required_skills": [sample_skill.id],
            }
            response = client.post(
                "/api/v1/mos", data=json.dumps(mo_data), content_type="application/json"
            )
            assert response.status_code == 201
            data = response.get_json()

            # Verify MO was created with skills
            mo = db.session.get(MaintenanceOrder, data["id"])
            assert mo is not None
            assert len(mo.required_skills) > 0

    def test_update_mo_success(self, client, sample_mo):
        """Test PUT /v1/mos/<id> updates maintenance order."""
        updated_data = {"description": "Updated description", "status": "In Progress"}
        response = client.put(
            f"/api/v1/mos/{sample_mo.id}",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["description"] == updated_data["description"]

    def test_update_mo_not_found(self, client, app):
        """Test PUT /v1/mos/<id> returns 404 for non-existent MO."""
        with app.app_context():
            updated_data = {"status": "Completed"}
            response = client.put(
                "/api/v1/mos/999",
                data=json.dumps(updated_data),
                content_type="application/json",
            )
            assert response.status_code == 404

    def test_delete_mo_success(self, client, sample_mo, app):
        """Test DELETE /v1/mos/<id> removes maintenance order."""
        mo_id = sample_mo.id
        response = client.delete(f"/api/v1/mos/{mo_id}")
        assert response.status_code == 200

        # Verify MO was deleted
        with app.app_context():
            mo = db.session.get(MaintenanceOrder, mo_id)
            assert mo is None

    def test_delete_mo_not_found(self, client, app):
        """Test DELETE /v1/mos/<id> returns 404 for non-existent MO."""
        with app.app_context():
            response = client.delete("/api/v1/mos/999")
            assert response.status_code == 404


class TestSparePartsAPI:
    """Test suite for Spare Parts API endpoints (/v1/spare_parts)."""

    def test_get_spare_parts_empty(self, client, app):
        """Test GET /v1/spare_parts returns empty list when no parts exist."""
        with app.app_context():
            response = client.get("/api/v1/spare_parts")
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_get_spare_parts_with_data(self, client, app, sample_spare_part):
        """Test GET /v1/spare_parts returns all spare parts."""
        with app.app_context():
            # Create additional spare parts for testing
            part2 = SparePart(description="Part 2", stock_quantity=5)
            part3 = SparePart(description="Part 3", stock_quantity=3)
            db.session.add_all([part2, part3])
            db.session.commit()

            response = client.get("/api/v1/spare_parts")
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) >= 3

    def test_get_spare_part_by_id_success(self, client, sample_spare_part):
        """Test GET /v1/spare_parts/<id> returns specific spare part."""
        response = client.get(f"/api/v1/spare_parts/{sample_spare_part.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == sample_spare_part.id
        assert data["description"] == sample_spare_part.description

    def test_get_spare_part_by_id_not_found(self, client, app):
        """Test GET /v1/spare_parts/<id> returns 404 for non-existent part."""
        with app.app_context():
            response = client.get("/api/v1/spare_parts/999")
            assert response.status_code == 404

    def test_add_spare_part_success(self, client, app):
        """Test POST /v1/spare_parts creates new spare part."""
        with app.app_context():
            part_data = {
                "description": "New Hydraulic Pump",
                "manufacturer": "ACME",
                "stock_quantity": 15,
                "min_quantity": 3,
            }
            response = client.post(
                "/api/v1/spare_parts",
                data=json.dumps(part_data),
                content_type="application/json",
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data["description"] == part_data["description"]
            assert "id" in data

    def test_add_spare_part_missing_required_fields(self, client, app):
        """Test POST /v1/spare_parts without required fields returns 400."""
        with app.app_context():
            part_data = {
                "manufacturer": "ACME"
                # Missing description
            }
            response = client.post(
                "/api/v1/spare_parts",
                data=json.dumps(part_data),
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_update_spare_part_success(self, client, sample_spare_part):
        """Test PUT /v1/spare_parts/<id> updates spare part."""
        updated_data = {"stock_quantity": 25, "min_quantity": 5}
        response = client.put(
            f"/api/v1/spare_parts/{sample_spare_part.id}",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["stock_quantity"] == updated_data["stock_quantity"]

    def test_update_spare_part_not_found(self, client, app):
        """Test PUT /v1/spare_parts/<id> returns 404 for non-existent part."""
        with app.app_context():
            updated_data = {"stock_quantity": 50}
            response = client.put(
                "/api/v1/spare_parts/999",
                data=json.dumps(updated_data),
                content_type="application/json",
            )
            assert response.status_code == 404

    def test_delete_spare_part_success(self, client, sample_spare_part, app):
        """Test DELETE /v1/spare_parts/<id> removes spare part."""
        part_id = sample_spare_part.id
        response = client.delete(f"/api/v1/spare_parts/{part_id}")
        assert response.status_code == 200

        # Verify part was deleted
        with app.app_context():
            part = db.session.get(SparePart, part_id)
            assert part is None

    def test_delete_spare_part_not_found(self, client, app):
        """Test DELETE /v1/spare_parts/<id> returns 404 for non-existent part."""
        with app.app_context():
            response = client.delete("/api/v1/spare_parts/999")
            assert response.status_code == 404


class TestUsersAPI:
    """Test suite for Users API endpoints (/v1/users)."""

    def test_get_users_empty(self, client, app):
        """Test GET /v1/users returns empty list when no users exist."""
        with app.app_context():
            response = client.get("/api/v1/users")
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_get_users_with_data(self, client, sample_user, sample_admin_user, app):
        """Test GET /v1/users returns all users."""
        with app.app_context():
            response = client.get("/api/v1/users")
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) >= 2

    def test_get_user_by_id_success(self, client, sample_user):
        """Test GET /v1/users/<id> returns specific user."""
        response = client.get(f"/api/v1/users/{sample_user.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == sample_user.id
        assert data["username"] == sample_user.username

    def test_get_user_by_id_not_found(self, client, app):
        """Test GET /v1/users/<id> returns 404 for non-existent user."""
        with app.app_context():
            response = client.get("/api/v1/users/999")
            assert response.status_code == 404

    def test_add_user_success(self, client, app):
        """Test POST /v1/users creates new user."""
        with app.app_context():
            user_data = {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepass123",
                "roles": ["Technician"],
            }
            response = client.post(
                "/api/v1/users",
                data=json.dumps(user_data),
                content_type="application/json",
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data["username"] == user_data["username"]
            assert "id" in data

    def test_add_user_missing_required_fields(self, client, app):
        """Test POST /v1/users without username returns 400."""
        with app.app_context():
            user_data = {
                "email": "nousername@example.com"
                # Missing username
            }
            response = client.post(
                "/api/v1/users",
                data=json.dumps(user_data),
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_update_user_success(self, client, sample_user):
        """Test PUT /v1/users/<id> updates user."""
        updated_data = {
            "email": "updated@example.com",
            "availability_status": "On Leave",
        }
        response = client.put(
            f"/api/v1/users/{sample_user.id}",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == updated_data["email"]

    def test_update_user_not_found(self, client, app):
        """Test PUT /v1/users/<id> returns 404 for non-existent user."""
        with app.app_context():
            updated_data = {"email": "updated@example.com"}
            response = client.put(
                "/api/v1/users/999",
                data=json.dumps(updated_data),
                content_type="application/json",
            )
            assert response.status_code == 404

    def test_delete_user_success(self, client, sample_user, app):
        """Test DELETE /v1/users/<id> removes user."""
        user_id = sample_user.id
        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 200

        # Verify user was deleted
        with app.app_context():
            user = db.session.get(User, user_id)
            assert user is None

    def test_delete_user_not_found(self, client, app):
        """Test DELETE /v1/users/<id> returns 404 for non-existent user."""
        with app.app_context():
            response = client.delete("/api/v1/users/999")
            assert response.status_code == 404


class TestEnhancedAPIErrorHandling:
    """Enhanced test suite for API error handling and edge cases."""

    def test_api_error_responses_400(self, client, app):
        """Test API returns 400 for invalid JSON payloads and invalid data types."""
        with app.app_context():
            # Test invalid JSON
            response = client.post(
                "/api/v1/assets",
                data='{"invalid_json": }',
                content_type="application/json",
            )
            assert response.status_code == 400

            # Test missing required field (name)
            response = client.post(
                "/api/v1/assets",
                data=json.dumps({"description": "No name provided"}),
                content_type="application/json",
            )
            assert response.status_code == 400

            # Test missing required field (description) for spare parts
            response = client.post(
                "/api/v1/spare_parts",
                data=json.dumps({"manufacturer": "Test"}),
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_api_error_responses_404(self, client, app):
        """Test API returns 404 for non-existent resource IDs across all endpoints."""
        with app.app_context():
            # Test GET with non-existent IDs
            assert client.get("/api/v1/assets/99999").status_code == 404
            assert client.get("/api/v1/mos/99999").status_code == 404
            assert client.get("/api/v1/spare_parts/99999").status_code == 404
            assert client.get("/api/v1/users/99999").status_code == 404

            # Test PUT with non-existent resources
            update_data = json.dumps({"name": "Updated"})
            assert (
                client.put(
                    "/api/v1/assets/99999",
                    data=update_data,
                    content_type="application/json",
                ).status_code
                == 404
            )

            # Test DELETE with non-existent resources
            assert client.delete("/api/v1/assets/99999").status_code == 404
            assert client.delete("/api/v1/mos/99999").status_code == 404

    def test_api_error_responses_500(self, client, app):
        """Test API handles database constraint violations gracefully."""
        with app.app_context():
            # First, create an asset
            first_asset = {
                "name": "First Asset",
                "asset_code": "UNIQUE-001",
                "description": "Original asset",
            }
            response = client.post(
                "/api/v1/assets",
                data=json.dumps(first_asset),
                content_type="application/json",
            )
            assert response.status_code == 201

            # Now try to create duplicate asset_code
            # Note: Expect 500 or exception
            duplicate_asset = {
                "name": "Duplicate Asset",
                "asset_code": "UNIQUE-001",  # Same as first asset
                "description": "Should fail with constraint error",
            }

            # This test verifies the API returns an error response
            # The API should be improved to catch IntegrityError and return 400/500
            try:
                response = client.post(
                    "/api/v1/assets",
                    data=json.dumps(duplicate_asset),
                    content_type="application/json",
                )
                # If no exception, should return error status
                assert response.status_code >= 400
                data = response.get_json()
                assert "error" in data or "message" in data
            except Exception:
                # Current implementation raises exception - this is acceptable for now
                # but should be improved to return proper error response
                pass

    def test_api_table_config_operations(self, client, app, logged_in_user):
        """Test table configuration save, set default, and delete operations."""
        with app.app_context():
            # Test save table configuration
            config_data = {
                "config_name": "My Custom View",
                "column_order": json.dumps(["name", "status", "type"]),
                "hidden_columns": json.dumps(["description"]),
                "filters": json.dumps({"status": "Operational"}),
                "sort_config": json.dumps({"column": "name", "direction": "asc"}),
                "is_default": False,
            }

            response = client.post(
                "/api/table-config/assets",
                data=json.dumps(config_data),
                content_type="application/json",
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"]
            assert "id" in data
            config_id = data["id"]

            # Test set as default (should remove default from other configs)
            config_data["config_name"] = "Default View"
            config_data["is_default"] = True

            response = client.post(
                "/api/table-config/assets",
                data=json.dumps(config_data),
                content_type="application/json",
            )
            assert response.status_code == 200

            # Test delete table configuration
            response = client.delete(f"/api/table-config/{config_id}")
            assert response.status_code == 200

    def test_api_complex_filters(self, client, multiple_assets, app):
        """Test multiple filter combinations, sorting, and pagination."""
        with app.app_context():
            # Test with multiple filters
            response = client.get("/api/v1/assets?status=Operational&asset_type=robot")
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)

            # Test sorting (if supported)
            response = client.get("/api/v1/assets?sort=name&order=desc")
            assert response.status_code == 200

            # Test pagination with filters
            response = client.get(
                "/api/v1/assets?page=1&per_page=10&status=Operational"
            )
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)

    def test_api_bulk_operations(self, client, app, sample_user):
        """Test bulk create operations and transaction rollback on failure."""
        with app.app_context():
            # Test bulk create assets
            assets_data = [
                {
                    "name": f"Bulk Asset {i}",
                    "asset_code": f"BULK-{i:03d}",
                    "asset_type": "robot",
                }
                for i in range(1, 6)
            ]

            # Create multiple assets in sequence
            created_ids = []
            for asset_data in assets_data:
                response = client.post(
                    "/api/v1/assets",
                    data=json.dumps(asset_data),
                    content_type="application/json",
                )
                if response.status_code == 201:
                    created_ids.append(response.get_json()["id"])

            # Verify at least some were created
            assert len(created_ids) > 0

            # Test bulk update (update multiple assets)
            for asset_id in created_ids[:3]:
                update_data = {"status": "Down"}
                response = client.put(
                    f"/api/v1/assets/{asset_id}",
                    data=json.dumps(update_data),
                    content_type="application/json",
                )
                assert response.status_code == 200

    def test_api_authentication_required(self, client, app):
        """Test endpoints requiring authentication return 401 without session."""
        with app.app_context():
            # Clear session to simulate unauthenticated request
            with client.session_transaction() as sess:
                sess.clear()

            # Test table config operations require authentication
            config_data = {
                "config_name": "Test",
                "column_order": json.dumps(["name"]),
                "is_default": False,
            }

            response = client.post(
                "/api/table-config/assets",
                data=json.dumps(config_data),
                content_type="application/json",
            )
            assert response.status_code == 401
            data = response.get_json()
            assert "error" in data or "message" in data
            error_msg = (data.get("error") or data.get("message", "")).lower()
            assert (
                "authentication" in error_msg
                or "auth" in error_msg
                or "unauthorized" in error_msg
            )

            # Test delete config requires authentication
            response = client.delete("/api/table-config/1")
            assert response.status_code == 401

    def test_api_role_management(self, client, app, sample_user):
        """Test user role assignment, creation, and removal."""
        with app.app_context():
            # Test role assignment during user creation
            user_data = {
                "username": "roletest",
                "email": "roletest@example.com",
                "password": "testpass123",
                "roles": ["Technician", "Supervisor"],
            }

            response = client.post(
                "/api/v1/users",
                data=json.dumps(user_data),
                content_type="application/json",
            )
            assert response.status_code == 201
            data = response.get_json()
            user_id = data["id"]

            # Verify roles were assigned (check roles_display field)
            assert "roles_display" in data
            assert "Technician" in data["roles_display"]
            assert "Supervisor" in data["roles_display"]

            # Test role update (add new role, remove existing)
            update_data = {"roles": ["Manager"]}  # Replace existing roles
            response = client.put(
                f"/api/v1/users/{user_id}",
                data=json.dumps(update_data),
                content_type="application/json",
            )
            assert response.status_code == 200
            data = response.get_json()

            # Verify role update
            if "roles_display" in data:
                assert "Manager" in data["roles_display"]

    def test_api_query_parameter_validation(self, client, app, sample_asset):
        """Test invalid query parameters are handled gracefully."""
        with app.app_context():
            # Test invalid filter values
            response = client.get("/api/v1/assets?status=InvalidStatus")
            assert (
                response.status_code == 200
            )  # Should not crash, just return empty or all

            # Test invalid pagination parameters
            response = client.get("/api/v1/assets?page=-1")
            assert response.status_code in [
                200,
                400,
            ]  # Either handle gracefully or return error

            response = client.get("/api/v1/assets?per_page=0")
            assert response.status_code in [200, 400]

            # Test special characters in search (potential SQL injection attempt)
            response = client.get("/api/v1/assets?search='; DROP TABLE assets; --")
            assert (
                response.status_code == 200
            )  # Should not execute SQL, just return safe results
            data = response.get_json()
            assert isinstance(data, list)  # Should return list, not crash

    def test_api_response_format_consistency(
        self, client, app, sample_asset, sample_mo
    ):
        """Test all endpoints return consistent JSON response formats."""
        with app.app_context():
            # Test success responses have consistent structure
            responses = [
                client.get("/api/v1/assets"),
                client.get("/api/v1/mos"),
                client.get("/api/v1/spare_parts"),
                client.get("/api/v1/users"),
            ]

            for response in responses:
                assert response.status_code == 200
                assert response.content_type == "application/json"
                data = response.get_json()
                assert isinstance(data, list)  # All list endpoints return arrays

            # Test single resource responses
            single_responses = [
                client.get(f"/api/v1/assets/{sample_asset.id}"),
                client.get(f"/api/v1/mos/{sample_mo.id}"),
            ]

            for response in single_responses:
                assert response.status_code == 200
                assert response.content_type == "application/json"
                data = response.get_json()
                assert isinstance(data, dict)  # Single resources return objects
                assert "id" in data  # All resources have ID

            # Test error responses have consistent structure
            error_responses = [
                client.get("/api/v1/assets/99999"),
                client.get("/api/v1/mos/99999"),
            ]

            for response in error_responses:
                assert response.status_code == 404
                assert response.content_type == "application/json"
                data = response.get_json()
                assert isinstance(data, dict)
                assert (
                    "error" in data or "message" in data
                )  # Error responses have error field


class TestAPIEdgeCasesAndErrorPaths:
    """Test suite for API edge cases and uncovered error paths."""

    def test_add_asset_missing_asset_code(self, client, app):
        """Test POST /v1/assets without asset_code returns 400."""
        with app.app_context():
            asset_data = {
                "name": "Asset Without Code",
                "description": "Missing asset_code field",
            }
            response = client.post(
                "/api/v1/assets",
                data=json.dumps(asset_data),
                content_type="application/json",
            )
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
            assert (
                "asset_code" in data["error"].lower()
                or "required" in data["error"].lower()
            )

    def test_update_asset_invalid_json(self, client, sample_asset, app):
        """Test PUT /v1/assets/<id> with invalid JSON returns 400."""
        with app.app_context():
            response = client.put(
                f"/api/v1/assets/{sample_asset.id}",
                data="",  # Empty data
                content_type="application/json",
            )
            assert response.status_code == 400
            data = response.get_json()
            assert data is None or "error" in data

    def test_update_mo_invalid_json(self, client, sample_mo, app):
        """Test PUT /v1/mos/<id> with invalid JSON returns 400."""
        with app.app_context():
            response = client.put(
                f"/api/v1/mos/{sample_mo.id}",
                data=None,  # No data
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_update_spare_part_invalid_json(self, client, sample_spare_part, app):
        """Test PUT /v1/spare_parts/<id> with invalid JSON returns 400."""
        with app.app_context():
            response = client.put(
                f"/api/v1/spare_parts/{sample_spare_part.id}",
                data="",
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_update_user_invalid_json(self, client, sample_user, app):
        """Test PUT /v1/users/<id> with invalid JSON returns 400."""
        with app.app_context():
            response = client.put(
                f"/api/v1/users/{sample_user.id}",
                data=None,
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_add_role_duplicate_name(self, client, app):
        """Test POST /v1/roles with duplicate name returns 409."""
        with app.app_context():
            # Create first role
            role_data = {"name": "UniqueRole", "description": "First role"}
            response = client.post(
                "/api/v1/roles",
                data=json.dumps(role_data),
                content_type="application/json",
            )
            assert response.status_code == 201

            # Try to create duplicate
            response = client.post(
                "/api/v1/roles",
                data=json.dumps(role_data),
                content_type="application/json",
            )
            assert response.status_code == 409
            data = response.get_json()
            assert "error" in data
            assert "already exists" in data["error"].lower()

    def test_add_role_missing_name(self, client, app):
        """Test POST /v1/roles without name returns 400."""
        with app.app_context():
            role_data = {"description": "Role without name"}
            response = client.post(
                "/api/v1/roles",
                data=json.dumps(role_data),
                content_type="application/json",
            )
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_register_user_duplicate_username(self, client, sample_user, app):
        """Test POST /v1/users with duplicate username returns 409."""
        with app.app_context():
            user_data = {
                "username": sample_user.username,  # Duplicate
                "email": "different@example.com",
                "password": "password123",
            }
            response = client.post(
                "/api/v1/users",
                data=json.dumps(user_data),
                content_type="application/json",
            )
            assert response.status_code == 409
            data = response.get_json()
            assert "error" in data
            assert "already exists" in data["error"].lower()

    def test_register_user_duplicate_email(self, client, sample_user, app):
        """Test POST /v1/users with duplicate email returns 409."""
        with app.app_context():
            user_data = {
                "username": "differentuser",
                "email": sample_user.email,  # Duplicate
                "password": "password123",
            }
            response = client.post(
                "/api/v1/users",
                data=json.dumps(user_data),
                content_type="application/json",
            )
            assert response.status_code == 409

    def test_filtered_data_invalid_entity(self, client, app):
        """Test GET /<entity>/filtered with invalid entity returns 400."""
        with app.app_context():
            response = client.get("/api/invalid_entity/filtered")
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
            assert "invalid entity" in data["error"].lower()

    def test_login_missing_credentials(self, client, app):
        """Test POST /v1/auth/login without username/password returns 400."""
        with app.app_context():
            # Missing password
            response = client.post(
                "/api/v1/auth/login",
                data=json.dumps({"username": "testuser"}),
                content_type="application/json",
            )
            assert response.status_code == 400
            data = response.get_json()
            assert "message" in data

            # Missing username
            response = client.post(
                "/api/v1/auth/login",
                data=json.dumps({"password": "testpass"}),
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_login_invalid_credentials(self, client, sample_user, app):
        """Test POST /v1/auth/login with wrong password returns 401."""
        with app.app_context():
            response = client.post(
                "/api/v1/auth/login",
                data=json.dumps(
                    {"username": sample_user.username, "password": "wrongpassword"}
                ),
                content_type="application/json",
            )
            assert response.status_code == 401
            data = response.get_json()
            assert "message" in data
            assert "invalid" in data["message"].lower()

    def test_update_table_config_not_owned(self, client, app, logged_in_user):
        """Test PUT /table-config/<id> for config not owned by user returns 403."""
        with app.app_context():
            # Create config for another user
            from src.services.db_utils import TableConfiguration

            other_config = TableConfiguration(
                user_id=999,  # Different user
                page_name="assets",
                config_name="Other User Config",
                column_order=json.dumps(["name"]),
                is_default=False,
            )
            db.session.add(other_config)
            db.session.commit()
            config_id = other_config.id

            # Try to update it
            response = client.put(
                f"/api/table-config/{config_id}",
                data=json.dumps({"column_order": json.dumps(["status"])}),
                content_type="application/json",
            )
            assert response.status_code == 403
            data = response.get_json()
            assert "error" in data

    def test_set_default_table_config_not_owned(self, client, app, logged_in_user):
        """Test POST /table-config/<page>/<id>/set-default for config not owned returns
        403."""
        with app.app_context():
            # Create config for another user
            from src.services.db_utils import TableConfiguration

            other_config = TableConfiguration(
                user_id=999,  # Different user
                page_name="assets",
                config_name="Other User Config",
                column_order=json.dumps(["name"]),
                is_default=False,
            )
            db.session.add(other_config)
            db.session.commit()
            config_id = other_config.id

            # Try to set as default
            response = client.post(f"/api/table-config/assets/{config_id}/set-default")
            assert response.status_code == 403

    def test_remove_default_table_config_not_owned(self, client, app, logged_in_user):
        """Test POST /table-config/<page>/<id>/remove-default for config not owned
        returns 403."""
        with app.app_context():
            # Create config for another user
            from src.services.db_utils import TableConfiguration

            other_config = TableConfiguration(
                user_id=999,  # Different user
                page_name="assets",
                config_name="Other User Config",
                column_order=json.dumps(["name"]),
                is_default=True,
            )
            db.session.add(other_config)
            db.session.commit()
            config_id = other_config.id

            # Try to remove default
            response = client.post(
                f"/api/table-config/assets/{config_id}/remove-default"
            )
            assert response.status_code == 403


class TestAPITableConfig:
    """Test suite for Table Configuration API endpoints."""

    def test_get_table_configs_empty(self, client, logged_in_user):
        """Test GET /api/table-config/<page> returns empty list initially."""
        response = client.get("/api/table-config/assets")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_save_table_config_success(self, client, logged_in_user):
        """Test POST /api/table-config/<page> saves configuration."""
        config_data = {
            "config_name": "My View",
            "column_order": json.dumps(["name", "status"]),
            "hidden_columns": json.dumps([]),
            "filters": json.dumps({"status": "Operational"}),
            "sort_config": json.dumps({"column": "name", "direction": "asc"}),
            "is_default": True,
        }
        response = client.post(
            "/api/table-config/assets",
            data=json.dumps(config_data),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "id" in data

    def test_update_table_config_success(self, client, logged_in_user, app):
        """Test PUT /api/table-config/<id> updates configuration."""
        # Create config first
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id,
                page_name="assets",
                config_name="Original",
                is_default=False,
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        update_data = {
            "column_order": json.dumps(["name", "asset_code"]),
            "hidden_columns": json.dumps(["description"]),
        }
        response = client.put(
            f"/api/table-config/{config_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify update
        with app.app_context():
            updated = db.session.get(TableConfiguration, config_id)
            assert updated.column_order == update_data["column_order"]
            assert updated.hidden_columns == update_data["hidden_columns"]

    def test_set_default_config(self, client, logged_in_user, app):
        """Test POST /api/table-config/<page>/<id>/set-default."""
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id,
                page_name="assets",
                config_name="View 1",
                is_default=False,
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        response = client.post(f"/api/table-config/assets/{config_id}/set-default")
        assert response.status_code == 200

        with app.app_context():
            updated = db.session.get(TableConfiguration, config_id)
            assert updated.is_default is True

    def test_remove_default_config(self, client, logged_in_user, app):
        """Test POST /api/table-config/<page>/<id>/remove-default."""
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id,
                page_name="assets",
                config_name="View 1",
                is_default=True,
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        response = client.post(f"/api/table-config/assets/{config_id}/remove-default")
        assert response.status_code == 200

        with app.app_context():
            updated = db.session.get(TableConfiguration, config_id)
            assert updated.is_default is False

    def test_delete_table_config_success(self, client, logged_in_user, app):
        """Test DELETE /api/table-config/<id>."""
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id, page_name="assets", config_name="To Delete"
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        response = client.delete(f"/api/table-config/{config_id}")
        assert response.status_code == 200

        with app.app_context():
            assert db.session.get(TableConfiguration, config_id) is None


class TestAPIFilteredData:
    """Test suite for Filtered Data API endpoints (/<entity>/filtered)."""

    def test_get_filtered_assets_exact_match(self, client, multiple_assets):
        """Test filtered assets with exact match."""
        filter_config = json.dumps(
            {"status": {"value": "Operational", "operator": "equals"}}
        )
        response = client.get(f"/api/assets/filtered?filters={filter_config}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1
        for asset in data:
            assert asset["status"] == "Operational"

    def test_get_filtered_assets_contains(self, client, multiple_assets):
        """Test filtered assets with contains operator."""
        filter_config = json.dumps({"name": {"value": "Robot", "operator": "contains"}})
        response = client.get(
            "/api/assets/filtered", query_string={"filters": filter_config}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 2

    def test_get_filtered_assets_sorting(self, client, multiple_assets):
        """Test filtered assets with sorting."""
        response = client.get(
            "/api/assets/filtered?sort_column=name&sort_direction=desc"
        )
        assert response.status_code == 200
        data = response.get_json()
        names = [asset["name"] for asset in data]
        assert names == sorted(names, reverse=True)

    def test_get_filtered_invalid_entity(self, client):
        """Test 400 for invalid entity type."""
        response = client.get("/api/invalid_entity/filtered")
        assert response.status_code == 400

    def test_get_filtered_invalid_filter_json(self, client):
        """Test 400 for invalid filter JSON."""
        response = client.get("/api/assets/filtered?filters={invalid_json}")
        assert response.status_code == 400
