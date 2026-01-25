import json

from src.services.db_utils import TableConfiguration, db


class TestApiCoverage:
    """Additional tests to boost coverage for api.py."""

    def test_get_table_configs(self, client, app, logged_in_user):
        """Test GET /api/table-config/<page_name>."""
        with app.app_context():
            # Create a dummy config
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

        response = client.get("/api/table-config/assets")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == config_id

    def test_update_table_config(self, client, app, logged_in_user):
        """Test PUT /api/table-config/<config_id>."""
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id,
                page_name="assets",
                config_name="Old Name",
                column_order="[]",
                hidden_columns="[]",
                filters="{}",
                sort_config="{}",
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        update_data = {
            "config_name": "New Name",
            "column_order": "[]",
            "hidden_columns": "[]",
            "filters": "{}",
            "sort_config": "{}",
        }

        response = client.put(
            f"/api/table-config/{config_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.get_json()["success"] is True

        with app.app_context():
            updated = db.session.get(TableConfiguration, config_id)
            assert updated.column_order == "[]"

    def test_update_table_config_not_found(self, client, logged_in_user):
        """Test PUT /api/table-config/9999."""
        response = client.put(
            "/api/table-config/9999",
            data=json.dumps({"config_name": "new"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_set_default_table_config(self, client, app, logged_in_user):
        """Test POST /api/table-config/<page_name>/<config_id>/set-default."""
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id,
                page_name="assets",
                config_name="Default Candidate",
                column_order="{}",
                hidden_columns="[]",
                filters="{}",
                sort_config="{}",
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        response = client.post(f"/api/table-config/assets/{config_id}/set-default")
        assert response.status_code == 200
        assert response.get_json()["success"] is True

        with app.app_context():
            # Check is_default
            updated = db.session.get(TableConfiguration, config_id)
            assert updated.is_default is True

    def test_remove_default_table_config(self, client, app, logged_in_user):
        """Test POST /api/table-config/<page_name>/<config_id>/remove-default."""
        with app.app_context():
            config = TableConfiguration(
                user_id=logged_in_user.id,
                page_name="assets",
                config_name="Default Config",
                column_order="{}",
                hidden_columns="[]",
                filters="{}",
                sort_config="{}",
                is_default=True,
            )
            db.session.add(config)
            db.session.commit()
            config_id = config.id

        response = client.post(f"/api/table-config/assets/{config_id}/remove-default")
        assert response.status_code == 200
        assert response.get_json()["success"] is True

        with app.app_context():
            updated = db.session.get(TableConfiguration, config_id)
            assert updated.is_default is False

    def test_api_invalid_json(self, client, logged_in_user):
        """Test error handling for invalid JSON."""
        # Use existing endpoint that expects JSON
        # Assuming asset 1 exists or doesn't matter for JSON parsing error
        response = client.put(
            "/api/v1/assets/1", data="invalid json", content_type="application/json"
        )
        # This might return 400 (Bad Request) or 404 (if ID invalid check comes first)
        # But validate_json_data usually runs early.
        # Let's check api.py: update_asset calls get_entity_or_404 FIRST.
        # So we need a valid asset ID. Or mock it.
        # Alternatively, find a POST endpoint that parses JSON first.
        # save_table_config? POST /api/table-config/<page> checks validate_json_data.
        response = client.post(
            "/api/table-config/test_page",
            data="invalid json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_api_method_not_allowed(self, client):
        """Test 405 error."""
        # /api/table-config/assets only allows GET and POST
        response = client.put("/api/table-config/assets")
        assert response.status_code == 405
