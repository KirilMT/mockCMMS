from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError

from src.routes.api import (
    get_entity_or_404,
    parse_datetime_safe,
    safe_commit,
    sanitize_like_value,
    validate_json_data,
)


class TestApiUtils:
    def test_get_entity_or_404_found(self, app):
        with app.app_context():
            mock_model = MagicMock()
            with patch("src.routes.api.db.session.get", return_value="entity"):
                entity, error = get_entity_or_404(mock_model, 1)
                assert entity == "entity"
                assert error is None

    def test_get_entity_or_404_not_found(self, app):
        with app.app_context():
            mock_model = MagicMock()
            with patch("src.routes.api.db.session.get", return_value=None):
                entity, error = get_entity_or_404(mock_model, 1)
                assert entity is None
                assert error[1] == 404

    def test_validate_json_data_no_data(self, app):
        with app.test_request_context(json=None):
            # Using patch on request.get_json because test_request_context
            # might not returning None for get_json if data is missing
            with patch("src.routes.api.request.get_json", return_value=None):
                data, error = validate_json_data()
                assert error[1] == 400
                assert error[0].json["error"] == "Invalid JSON"

    def test_validate_json_data_missing_fields(self, app):
        with app.test_request_context(json={"a": 1}):
            data, error = validate_json_data(required_fields=["b"])
            assert error[1] == 400
            assert "Missing required fields" in error[0].json["error"]

    def test_safe_commit_success(self, app):
        with app.app_context():
            with patch("src.routes.api.db.session.commit") as mock_commit:
                success, error = safe_commit()
                assert success is True
                assert error is None
                mock_commit.assert_called_once()

    def test_safe_commit_failure(self, app):
        with app.app_context():
            with patch(
                "src.routes.api.db.session.commit",
                side_effect=SQLAlchemyError("DB Error"),
            ):
                with patch("src.routes.api.db.session.rollback") as mock_rollback:
                    success, error = safe_commit()
                    assert success is False
                    assert error[1] == 500
                    mock_rollback.assert_called_once()

    def test_parse_datetime_safe_valid(self):
        dt = parse_datetime_safe("2023-10-27T10:00:00")
        assert dt is not None
        assert dt.year == 2023

    def test_parse_datetime_safe_invalid(self):
        assert parse_datetime_safe(None) is None
        assert parse_datetime_safe("invalid-date") is None

    def test_sanitize_like_value(self):
        assert sanitize_like_value("test") == "test"
        assert sanitize_like_value("test%_") == "test\\%\\_"
        assert sanitize_like_value(123) == "123"


class TestApiResourceErrors:
    # Test error paths that might rely on safe_commit failure

    def test_add_asset_commit_fail(self, client, app):
        with app.app_context():
            with patch(
                "src.routes.api.safe_commit", return_value=(False, ("DB Error", 500))
            ):
                response = client.post(
                    "/api/v1/assets", json={"name": "Test", "asset_code": "A1"}
                )
                assert response.status_code == 500

    def test_update_asset_commit_fail(self, client, app):
        # Need existing asset
        with app.app_context():
            with patch(
                "src.routes.api.get_entity_or_404", return_value=(MagicMock(), None)
            ):
                with patch(
                    "src.routes.api.validate_json_data", return_value=({}, None)
                ):
                    with patch(
                        "src.routes.api.safe_commit",
                        return_value=(False, ("DB Error", 500)),
                    ):
                        response = client.put("/api/v1/assets/1", json={})
                        assert response.status_code == 500

    def test_delete_asset_commit_fail(self, client, app):
        with app.app_context():
            with patch(
                "src.routes.api.get_entity_or_404", return_value=(MagicMock(), None)
            ):
                with patch(
                    "src.routes.api.safe_commit",
                    return_value=(False, ("DB Error", 500)),
                ):
                    response = client.delete("/api/v1/assets/1")
                    assert response.status_code == 500

    # Test MO date parsing errors
    def test_add_mo_invalid_date(self, client, app):
        with app.app_context():
            with patch(
                "src.routes.api.validate_json_data",
                return_value=({"asset_id": 1, "due_date": "invalid"}, None),
            ):
                with patch(
                    "src.routes.api.get_entity_or_404", return_value=(MagicMock(), None)
                ):
                    response = client.post("/api/v1/mos", json={})
                    assert response.status_code == 400
                    assert "Invalid date format" in response.json["error"]

    def test_update_mo_invalid_date(self, client, app):
        with app.app_context():
            with patch(
                "src.routes.api.get_entity_or_404", return_value=(MagicMock(), None)
            ):
                with patch(
                    "src.routes.api.validate_json_data",
                    return_value=({"due_date": "invalid"}, None),
                ):
                    response = client.put("/api/v1/mos/1", json={})
                    assert response.status_code == 400
