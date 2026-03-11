from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError

from src.routes.api import (
    get_entity_or_404,
    parse_datetime_safe,
    safe_commit,
    sanitize_like_value,
    validate_json_data,
)
from src.services.db_utils import TableConfiguration, db


class TestApiResources:
    """Consolidated CRUD and Utility tests for API resources."""

    # =========================================================================
    # CORE CRUD LIFECYCLE TESTS (Functional/Integration style)
    # =========================================================================

    def test_mo_lifecycle(self, client, auth_client, sample_asset, app):
        """Test MO creation, retrieval, update, deletion."""
        mo_data = {
            "asset_id": sample_asset.id,
            "description": "New MO",
            "order_type": "PM",
            "priority": "High",
            "required_skills": ["Welding"],
        }
        resp = auth_client.post("/api/v1/mos", json=mo_data)
        assert resp.status_code == 201
        mo_id = resp.get_json()["id"]

        resp = auth_client.get(f"/api/v1/mos/{mo_id}")
        assert resp.status_code == 200
        assert resp.get_json()["description"] == "New MO"

        resp = auth_client.put(
            f"/api/v1/mos/{mo_id}", json={"description": "Updated MO"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["description"] == "Updated MO"

        resp = auth_client.delete(f"/api/v1/mos/{mo_id}")
        assert resp.status_code == 200
        assert auth_client.get(f"/api/v1/mos/{mo_id}").status_code == 404

    def test_spare_part_lifecycle(self, client, auth_client, app):
        """Test Spare Part CRUD."""
        sp_data = {"description": "Bearing", "manufacturer": "SKF", "stock_quantity": 5}
        resp = auth_client.post("/api/v1/spare_parts", json=sp_data)
        assert resp.status_code == 201
        sp_id = resp.get_json()["id"]

        resp = auth_client.put(
            f"/api/v1/spare_parts/{sp_id}", json={"stock_quantity": 10}
        )
        assert resp.status_code == 200
        assert resp.get_json()["stock_quantity"] == 10

        resp = auth_client.delete(f"/api/v1/spare_parts/{sp_id}")
        assert resp.status_code == 200

    def test_user_lifecycle(self, client, auth_client, app):
        """Test User CRUD."""
        user_data = {
            "username": "apiuser",
            "email": "api@test.com",
            "password": "pass",
            "roles": ["Admin"],
        }
        resp = auth_client.post("/api/v1/users", json=user_data)
        assert resp.status_code == 201
        user_id = resp.get_json()["id"]

        resp = auth_client.put(
            f"/api/v1/users/{user_id}", json={"email": "updated@test.com"}
        )
        assert resp.status_code == 200

        resp = auth_client.delete(f"/api/v1/users/{user_id}")
        assert resp.status_code == 200

    def test_table_config_lifecycle(self, client, app, logged_in_user):
        """Test TableConfiguration CRUD."""
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id,
                page_name="assets",
                config_name="Test View",
                column_order="[]",
                hidden_columns="[]",
                filters="{}",
                sort_config="{}",
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        # Read
        resp = client.get("/api/table-config/assets")
        assert resp.status_code == 200
        assert any(c["id"] == config_id for c in resp.get_json())

        # Update
        update_data = {"config_name": "New Name"}
        resp = client.put(f"/api/table-config/{config_id}", json=update_data)
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

        # Delete
        resp = client.delete(f"/api/table-config/{config_id}")
        assert resp.status_code == 200

    # =========================================================================
    # INTERNAL API UTILITIES TESTS
    # =========================================================================

    def test_get_entity_or_404(self, app):
        """Test get_entity_or_404 utility with mocks."""
        with app.app_context():
            mock_model = MagicMock()
            with patch("src.routes.api.db.session.get", side_effect=["entity", None]):
                # Found
                entity, error = get_entity_or_404(mock_model, 1)
                assert entity == "entity"
                assert error is None
                # Not Found
                entity, error = get_entity_or_404(mock_model, 2)
                assert entity is None
                assert error[1] == 404

    def test_validate_json_data(self, app):
        """Test JSON validation utility."""
        # Case: No data
        with app.test_request_context(json=None):
            with patch("src.routes.api.request.get_json", return_value=None):
                data, error = validate_json_data()
                assert error[1] == 400
        # Case: Missing fields
        with app.test_request_context(json={"a": 1}):
            data, error = validate_json_data(required_fields=["b"])
            assert "Missing" in error[0].json["error"]

    def test_safe_commit_logic(self, app):
        """Test safe_commit success and failure paths."""
        with app.app_context():
            # Success
            with patch("src.routes.api.db.session.commit"):
                assert safe_commit()[0] is True
            # Failure
            with patch("src.routes.api.db.session.commit", side_effect=SQLAlchemyError):
                with patch("src.routes.api.db.session.rollback") as mock_roll:
                    success, error = safe_commit()
                    assert success is False
                    assert error[1] == 500
                    mock_roll.assert_called_once()

    def test_misc_utils(self):
        """Test small API utilities like datetime parsing and sanitization."""
        assert parse_datetime_safe("2023-10-27T10:00:00").year == 2023
        assert parse_datetime_safe(None) is None
        assert sanitize_like_value("test%_") == "test\\%\\_"

    # =========================================================================
    # ERROR PATHS / DATABASE FAILURES
    # =========================================================================

    def test_resource_commit_failures(self, client, app):
        """Test resource creation/deletion when DB commit fails."""
        with app.app_context():
            with patch(
                "src.routes.api.safe_commit",
                return_value=(False, ({"error": "FAIL"}, 500)),
            ):
                # Add asset fail
                resp = client.post(
                    "/api/v1/assets", json={"name": "T", "asset_code": "A"}
                )
                assert resp.status_code == 500
                # Delete asset fail (mock entity exists)
                with patch(
                    "src.routes.api.get_entity_or_404", return_value=(MagicMock(), None)
                ):
                    resp = client.delete("/api/v1/assets/1")
                    assert resp.status_code == 500

    def test_mo_invalid_date_validation(self, client, app):
        """Test MO routes handle invalid date formats in payload."""
        with app.app_context():
            payload = {
                "asset_id": 1,
                "due_date": "invalid-date",
                "description": "Fixed Test",
                "order_type": "PM",
            }
            with patch(
                "src.routes.api.get_entity_or_404", return_value=(MagicMock(), None)
            ):
                resp = client.post("/api/v1/mos", json=payload)
                assert resp.status_code == 400
                assert "date format" in resp.json["error"].lower()
