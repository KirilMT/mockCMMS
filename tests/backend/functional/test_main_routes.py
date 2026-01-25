class TestMainRoutes:
    """Consolidated main routes tests."""

    def test_shift_calendar_route(self, auth_client):
        """Test the shift calendar route."""
        response = auth_client.get("/shift_calendar")
        assert response.status_code == 200
        # Check for calendar elements
        assert (
            b"Shift Calendar" in response.data or b"calendar" in response.data.lower()
        )

    def test_shift_calendar_navigation(self, auth_client):
        """Test shift calendar navigation parameters."""
        response = auth_client.get("/shift_calendar?year=2024&month=1")
        assert response.status_code == 200
        assert b"January" in response.data
        assert b"2024" in response.data

    def test_pm_order_validation_frequency(self, auth_client, sample_asset, app):
        """Test that PM orders require a frequency."""
        with app.app_context():
            mo_data = {
                "asset_id": sample_asset.id,
                "description": "PM Test",
                "order_type": "PM",
                "priority": "High",
                # Missing frequency
            }
            response = auth_client.post(
                "/maintenance_orders/add", data=mo_data, follow_redirects=True
            )
            assert response.status_code == 200
            assert b"Frequency is required" in response.data

    def test_deprecated_technician_route(self, auth_client, sample_user):
        """Test redirection of deprecated technician route."""
        response = auth_client.get(
            f"/technicians/{sample_user.id}", follow_redirects=False
        )
        assert response.status_code == 302
        assert f"/users/{sample_user.id}" in response.location

    def test_planning_redirect(self, auth_client):
        """Test planning route redirect."""
        response = auth_client.get("/planning", follow_redirects=False)
        assert response.status_code == 302

    def test_login_required_decorator(self, client):
        """Test that routes require login."""
        # Try accessing assets page without login
        response = client.get("/assets", follow_redirects=False)
        assert response.status_code == 302
        assert "login" in response.location

    def test_logout(self, auth_client):
        """Test logout functionality."""
        response = auth_client.post("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"logged out" in response.data or b"Login" in response.data

    def test_add_asset_invalid_form(self, auth_client):
        """Test adding asset with invalid form data triggers error handling."""

        # Missing required fields like asset_code
        # In testing mode, with test client, we get a 400 BAD REQUEST response
        response = auth_client.post(
            "/assets/add", data={"name": "Bad Asset"}, follow_redirects=True
        )
        assert response.status_code == 400
