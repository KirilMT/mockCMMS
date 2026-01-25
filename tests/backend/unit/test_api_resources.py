class TestApiResources:
    """Tests for CRUD operations on API resources."""

    def test_mo_lifecycle(self, client, auth_client, sample_asset, app):
        """Test MO creation, retrieval, update, deletion."""
        # Create (POST)
        mo_data = {
            "asset_id": sample_asset.id,
            "description": "New MO",
            "order_type": "PM",
            "priority": "High",
            "required_skills": ["Welding"],  # Implicitly tests skill creation
        }
        resp = auth_client.post("/api/v1/mos", json=mo_data)
        assert resp.status_code == 201
        mo_id = resp.get_json()["id"]

        # Read (GET)
        resp = auth_client.get(f"/api/v1/mos/{mo_id}")
        assert resp.status_code == 200
        assert resp.get_json()["description"] == "New MO"

        # List (GET)
        resp = auth_client.get("/api/v1/mos")
        assert resp.status_code == 200
        assert len(resp.get_json()) >= 1

        # Update (PUT)
        resp = auth_client.put(
            f"/api/v1/mos/{mo_id}", json={"description": "Updated MO"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["description"] == "Updated MO"

        # Delete (DELETE)
        resp = auth_client.delete(f"/api/v1/mos/{mo_id}")
        assert resp.status_code == 200

        # Verify deleted
        resp = auth_client.get(f"/api/v1/mos/{mo_id}")
        assert resp.status_code == 404

    def test_spare_part_lifecycle(self, client, auth_client, app):
        """Test Spare Part CRUD."""
        # Create
        sp_data = {"description": "Bearing", "manufacturer": "SKF", "stock_quantity": 5}
        resp = auth_client.post("/api/v1/spare_parts", json=sp_data)
        assert resp.status_code == 201
        sp_id = resp.get_json()["id"]

        # Update
        resp = auth_client.put(
            f"/api/v1/spare_parts/{sp_id}", json={"stock_quantity": 10}
        )
        assert resp.status_code == 200
        assert resp.get_json()["stock_quantity"] == 10

        # Delete
        resp = auth_client.delete(f"/api/v1/spare_parts/{sp_id}")
        assert resp.status_code == 200

    def test_user_lifecycle(self, client, auth_client, app):
        """Test User CRUD."""
        # Create
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "pass",
            "roles": ["Admin"],
        }
        # Endpoint handles role creation if missing
        resp = auth_client.post("/api/v1/users", json=user_data)
        assert resp.status_code == 201
        user_id = resp.get_json()["id"]

        # Update
        resp = auth_client.put(
            f"/api/v1/users/{user_id}", json={"email": "updated@example.com"}
        )
        assert resp.status_code == 200

        # Delete
        resp = auth_client.delete(f"/api/v1/users/{user_id}")
        assert resp.status_code == 200

    def test_auth_endpoints(self, client, sample_user):
        """Test Login/Logout."""
        # Login
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "username": sample_user.username,
                "password": "testpass123",  # password set in fixture?
            },
        )
        assert resp.status_code == 200

        # Logout
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

    def test_roles_api(self, auth_client):
        """Test Roles API."""
        resp = auth_client.post("/api/v1/roles", json={"name": "Supervisor"})
        # 201 or 409 if exists.
        # But if we rely on clean db per test, 201.
        if resp.status_code == 409:
            # Already exists, fetch it
            pass
        else:
            assert resp.status_code == 201

        resp = auth_client.get("/api/v1/roles")
        assert resp.status_code == 200
        assert any(r["name"] == "Supervisor" for r in resp.get_json())
