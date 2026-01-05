from src.services.db_utils import Asset, MaintenanceOrder, Role, SparePart, User, db


class TestSimulationUI:
    """Functional tests for the Simulation UI."""

    def test_simulation_dashboard_access(self, client):
        """Test accessing the simulation dashboard."""
        response = client.get("/simulation/")

        assert response.status_code == 200
        assert b"Simulation Tools" in response.data
        assert b"Breakdown Simulation" in response.data
        assert b"Spare Parts" in response.data

    def test_trigger_breakdown(self, client, app):
        """Test triggering a breakdown."""
        with app.app_context():
            # Create an operational asset first
            asset = Asset(asset_code="TEST-BD", name="Test Asset", status="Operational")
            db.session.add(asset)
            db.session.commit()

            response = client.post(
                "/simulation/trigger-breakdown", follow_redirects=True
            )

            assert response.status_code == 200

            # Verify asset status
            updated_asset = Asset.query.filter_by(asset_code="TEST-BD").first()
            assert updated_asset.status == "Offline"

            # Verify MO creation (Reactive)
            mo = MaintenanceOrder.query.filter_by(
                asset_id=updated_asset.id, order_type="Reactive"
            ).first()
            assert mo is not None
            assert mo.priority == "Critical"

    def test_generate_data_ui(self, client, app):
        """Test generating data via UI."""
        with app.app_context():
            initial_count = Asset.query.count()

            # Test Assets
            response = client.post(
                "/simulation/generate",
                data={"type": "assets", "count": 5},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert Asset.query.count() == initial_count + 5

            # Test Spare Parts
            initial_parts = SparePart.query.count()
            response = client.post(
                "/simulation/generate",
                data={"type": "spare_parts", "count": 5},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert SparePart.query.count() == initial_parts + 5

    def test_set_availability(self, client, app):
        """Test setting technician availability."""
        with app.app_context():
            # Create a user and role
            role = Role(name="Technician")
            db.session.add(role)

            user = User(username="sim_tech", email="sim@test.com")
            user.set_password("pass")
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()

            response = client.post(
                "/simulation/set-availability",
                data={"user_id": user.id, "status": "Sick"},
                follow_redirects=True,
            )

            assert response.status_code == 200

            # Check if the UI reflects the new status in the dropdown
            assert b"sim_tech (Sick)" in response.data

            updated_user = db.session.get(User, user.id)
            assert updated_user.availability_status == "Sick"

    def test_generate_users_data(self, client, app):
        """Test generating users via simulation UI."""
        with app.app_context():
            initial_count = User.query.count()

            response = client.post(
                "/simulation/generate",
                data={"type": "users", "count": 3},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert User.query.count() >= initial_count + 3

    def test_generate_orders_data(self, client, app):
        """Test generating maintenance orders via simulation UI."""
        with app.app_context():
            # Create an asset first - orders require assets
            asset = Asset(
                asset_code="TEST-ORD", name="Test Asset", status="Operational"
            )
            db.session.add(asset)
            db.session.commit()

            initial_count = MaintenanceOrder.query.count()

            response = client.post(
                "/simulation/generate",
                data={"type": "orders", "count": 3},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert MaintenanceOrder.query.count() >= initial_count + 3

    def test_generate_invalid_data_type(self, client, app):
        """Test generating data with invalid type shows error."""
        with app.app_context():
            response = client.post(
                "/simulation/generate",
                data={"type": "invalid_type", "count": 5},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert b"Invalid data type selected" in response.data

    def test_trigger_breakdown_no_operational_assets(self, client, app):
        """Test triggering breakdown when no operational assets exist."""
        with app.app_context():
            # Remove all operational assets
            Asset.query.filter_by(status="Operational").delete()
            db.session.commit()

            response = client.post(
                "/simulation/trigger-breakdown", follow_redirects=True
            )

            assert response.status_code == 200
            assert b"No operational assets available" in response.data

    def test_set_availability_user_not_found(self, client, app):
        """Test setting availability for non-existent user."""
        with app.app_context():
            response = client.post(
                "/simulation/set-availability",
                data={"user_id": 99999, "status": "Available"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"User not found" in response.data
