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

            updated_user = User.query.get(user.id)
            assert updated_user.availability_status == "Sick"
