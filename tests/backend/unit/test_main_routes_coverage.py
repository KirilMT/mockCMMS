from unittest.mock import MagicMock, patch

from src.routes.main import _get_technicians_and_teams, _process_mo_form
from src.services.db_utils import MaintenanceOrder


class TestMainRouteHelpers:
    def test_process_mo_form_pm_missing_frequency(self, app):
        with app.test_request_context():
            mo = MaintenanceOrder()
            form_data = {
                "asset_id": "1",
                "description": "Test",
                "order_type": "PM",
                # Missing frequency
            }
            # Should return False and flash message
            with patch("src.routes.main.flash") as mock_flash:
                result = _process_mo_form(mo, form_data)
                assert result is False
                mock_flash.assert_called_with(
                    "Frequency is required for PM (Preventive Maintenance) orders.",
                    "error",
                )

    def test_process_mo_form_success(self, app):
        with app.test_request_context():
            mo = MaintenanceOrder()
            form_data = {
                "asset_id": "1",
                "description": "Test",
                "order_type": "Corrective",
                "estimated_completion_time": "120",
                "labour_count": "2",
                "justification": "Fix it",
                "due_date": "2023-10-30",
            }
            with patch(
                "src.routes.main.request", new_callable=MagicMock
            ) as mock_request:
                mock_request.form.getlist.return_value = ["User1"]
                result = _process_mo_form(mo, form_data)
                assert result is True
                assert mo.estimated_completion_time == 120
                assert mo.labour_count == 2
                assert mo.due_date.year == 2023
                assert "User1" in mo.assignees_json

    def test_process_mo_form_invalid_time(self, app):
        """Test processing MO form with invalid time format."""
        with app.test_request_context():
            mo = MagicMock()
            form_data = {
                "order_type": "Corrective",
                "estimated_completion_time": "invalid",
            }
            with patch(
                "src.routes.main.request", new_callable=MagicMock
            ) as mock_request:
                mock_request.form.getlist.return_value = []
                result = _process_mo_form(mo, form_data)
                assert result is True
                assert mo.estimated_completion_time is None

    def test_user_detail_route(self, client, app):
        with app.app_context():
            with client.session_transaction() as sess:
                sess["user_id"] = 1

            with (
                patch("src.routes.main.db") as mock_db,
                patch("src.routes.main.render_template") as mock_render,
                patch("src.routes.main.User") as MockUser,
            ):
                mock_user = MagicMock()
                role = MagicMock()
                role.name = "Technician"
                mock_user.roles = [role]
                mock_user.id = 1

                mock_db.get_or_404.return_value = mock_user

                # Access the route
                response = client.get("/users/1")

                assert response.status_code == 200
                mock_db.get_or_404.assert_called_with(MockUser, 1)
                assert mock_render.called
                args, kwargs = mock_render.call_args
                assert kwargs["is_technician"] is True
                assert kwargs["user"] == mock_user

    def test_get_technicians_and_teams_no_role(self, app):
        with app.app_context():
            with patch("src.routes.main.Role.query.filter_by") as mock_filter:
                mock_filter.return_value.first.return_value = None
                techs, teams = _get_technicians_and_teams()
                assert techs == []
                # Teams should still be fetched
                # (Assuming Team.query.all() works and returns mocked list or empty)

    def test_ticket_page(self, client):
        response = client.get("/tickets/T123")
        assert response.status_code == 200
        assert b"T123" in response.data

    def test_maintenance_grid_page(self, client):
        response = client.get("/maintenance_grid/1,2,3")
        assert response.status_code == 200
        assert b"1,2,3" in response.data

    def test_add_mo_return_to_asset(self, client, app, sample_user, sample_asset):
        with app.app_context():
            with client.session_transaction() as sess:
                sess["user_id"] = sample_user.id

            data = {
                "asset_id": str(sample_asset.id),
                "description": "Test Return To",
                "order_type": "Corrective",
                "priority": "Low",
                "labour_count": "1",
            }
            response = client.post("/maintenance_orders/add?return_to=asset", data=data)
            assert response.status_code == 302
            assert f"/assets/{sample_asset.id}" in response.location

    def test_edit_user_team_and_sp(self, client, app, sample_admin_user, sample_team):
        with app.app_context():
            from src.services.db_utils import SatellitePoint, db

            sp = SatellitePoint(name="SP1")
            db.session.add(sp)
            db.session.commit()

            with client.session_transaction() as sess:
                sess["user_id"] = sample_admin_user.id

            data = {
                "username": "editeduser",
                "email": "edited@example.com",
                "is_active": "on",
                "roles": ["Admin"],
                "team_id": str(sample_team.id),
                "satellite_point_id": str(sp.id),
            }
            response = client.post(f"/users/{sample_admin_user.id}/edit", data=data)
            assert response.status_code == 302

            user = db.session.get(sample_admin_user.__class__, sample_admin_user.id)
            assert user.team_id == sample_team.id
            assert user.satellite_point_id == sp.id

    def test_delete_mo_error(self, client, app, sample_user):
        with app.app_context():
            from src.services.db_utils import MaintenanceOrder, db

            mo = MaintenanceOrder(
                description="To Delete",
                asset_id=1,
                order_type="Corrective",
                priority="Low",
            )
            db.session.add(mo)
            db.session.commit()
            mo_id = mo.id

            with client.session_transaction() as sess:
                sess["user_id"] = sample_user.id

            with patch("src.routes.main.db.session.delete") as mock_delete:
                mock_delete.side_effect = Exception("Delete Error")
                response = client.post(f"/maintenance_orders/{mo_id}/delete")
                assert response.status_code == 302
                # Flash message check (mocking flash is better but let's check
                # session or follow-up)

    def test_spare_part_routes_validations(self, client, app, sample_user):
        with app.app_context():
            from src.services.db_utils import SparePart, db

            part = SparePart(
                description="Part 1",
                manufacturer="M1",
                stock_quantity=10,
                min_quantity=5,
            )
            db.session.add(part)
            db.session.commit()
            part_id = part.id

            with client.session_transaction() as sess:
                sess["user_id"] = sample_user.id

            # Detail
            assert client.get(f"/spare_parts/{part_id}").status_code == 200

            # Edit POST
            data = {
                "description": "Updated",
                "manufacturer": "M2",
                "manufacturer_part_id": "P2",
                "stock_quantity": "20",
                "location": "L2",
                "min_quantity": "10",
            }
            assert (
                client.post(f"/spare_parts/{part_id}/edit", data=data).status_code
                == 302
            )

            # Delete
            assert client.post(f"/spare_parts/{part_id}/delete").status_code == 302
