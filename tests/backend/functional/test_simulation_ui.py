"""Functional tests for the Simulation UI routes."""

from src.services.db_utils import Asset, MaintenanceOrder, Role, SparePart, User, db


class TestSimulationUI:
    """Functional tests for the Simulation UI."""

    def test_simulation_dashboard_access(self, client):
        """Test accessing the simulation dashboard."""
        # Note: client comes from conftest but uses our local 'app' fixture
        response = client.get("/simulation/")

        assert response.status_code == 200
        assert b"Simulation Tools" in response.data
        assert b"Breakdown Simulation" in response.data
        assert b"Spare Parts" in response.data

    def test_trigger_breakdown(self, client, app):
        """Test triggering a breakdown."""
        # Clean environment to prevent pollution from previous tests
        # Clean environment done via fixtures

        # Step 1: Create an operational asset
        with app.app_context():
            asset = Asset(asset_code="TEST-BD", name="Test Asset", status="Operational")
            db.session.add(asset)
            db.session.commit()
            asset_id = asset.id

        # Step 2: Trigger breakdown via POST
        response = client.post("/simulation/trigger-breakdown", follow_redirects=True)
        assert response.status_code == 200

        # Step 3: Verify in a fresh context
        with app.app_context():
            updated_asset = db.session.get(Asset, asset_id)
            assert updated_asset.status == "Offline"

            # Verify MO creation (Reactive)
            mo = MaintenanceOrder.query.filter_by(
                asset_id=asset_id, order_type="Reactive"
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

        with app.app_context():
            assert Asset.query.count() == initial_count + 5
            initial_parts = SparePart.query.count()

        # Test Spare Parts
        response = client.post(
            "/simulation/generate",
            data={"type": "spare_parts", "count": 5},
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            assert SparePart.query.count() == initial_parts + 5

    def test_set_availability(self, client, app):
        """Test setting technician availability."""
        # Step 1: Create user and role
        with app.app_context():
            role = Role.query.filter_by(name="Technician").first()
            if not role:
                role = Role(name="Technician")
                db.session.add(role)
                db.session.flush()

            user = User(username="sim_tech", email="sim@test.com")
            user.set_password("pass")
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        # Step 2: Update availability
        response = client.post(
            "/simulation/set-availability",
            data={"user_id": user_id, "status": "Sick"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Step 3: Verify in fresh context
        with app.app_context():
            updated_user = db.session.get(User, user_id)
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

        with app.app_context():
            assert User.query.count() >= initial_count + 3

    def test_generate_orders_data(self, client, app):
        """Test generating maintenance orders via simulation UI."""
        # Create an asset first - orders require assets
        with app.app_context():
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

        with app.app_context():
            assert MaintenanceOrder.query.count() >= initial_count + 3

    def test_generate_invalid_data_type(self, client, app):
        """Test generating data with invalid type shows error."""
        response = client.post(
            "/simulation/generate",
            data={"type": "invalid_type", "count": 5},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid data type selected" in response.data

    def test_trigger_breakdown_no_operational_assets(self, client, app):
        """Test triggering breakdown when no operational assets exist."""
        # Remove all operational assets
        with app.app_context():
            Asset.query.filter_by(status="Operational").delete()
            db.session.commit()

        response = client.post("/simulation/trigger-breakdown", follow_redirects=True)

        assert response.status_code == 200
        assert b"No operational assets available" in response.data

    def test_set_availability_user_not_found(self, client, app):
        """Test setting availability for non-existent user."""
        response = client.post(
            "/simulation/set-availability",
            data={"user_id": 99999, "status": "Available"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"User not found" in response.data
