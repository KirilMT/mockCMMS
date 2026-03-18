from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.reporting.src import models as report_models
from src.services.db_utils import Asset, MaintenanceOrder, db


@pytest.fixture
def logged_in_client(client, sample_user):
    """Fixture to provide a client with a logged-in user."""
    # Log in properly via the login route
    client.post(
        "/login",
        data={"username": "testuser", "password": "testpass123"},
        follow_redirects=True,
    )
    return client


def test_reporting_access_no_login(client):
    """Test accessing reporting page without login."""
    response = client.get("/reporting/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_reporting_list_page(logged_in_client):
    """Test accessing the reporting list page."""
    response = logged_in_client.get("/reporting/")
    assert response.status_code == 200
    # The title in base template or reporting template
    assert b"Reporting" in response.data


def test_generate_report_page_get(logged_in_client):
    """Test accessing the report generation page via GET."""
    response = logged_in_client.get("/reporting/generate")
    assert response.status_code == 200
    assert b"Generate Report" in response.data


def test_generate_report_no_type(logged_in_client):
    """Test generating a report without a type."""
    response = logged_in_client.post(
        "/reporting/generate", data={}, follow_redirects=True
    )
    assert b"Report Type is required" in response.data


def test_generate_shift_report_missing_date(logged_in_client):
    """Test generating a shift report without a date."""
    response = logged_in_client.post(
        "/reporting/generate",
        data={
            "title": "Test Shift Report",
            "report_type": "shift_report",
            "shift_name": "Early",
        },
        follow_redirects=True,
    )
    assert b"Shift Date is required" in response.data


def test_generate_weekend_report_missing_date(logged_in_client):
    """Test generating a weekend report without a date."""
    response = logged_in_client.post(
        "/reporting/generate",
        data={"title": "Test Weekend Report", "report_type": "weekend_report"},
        follow_redirects=True,
    )
    assert b"Weekend Date is required" in response.data


@patch(
    "apps.reporting.src.services.data_aggregator.DataAggregator."
    "get_aggregated_shift_data"
)
def test_generate_shift_report_success(mock_get_data, logged_in_client, sample_user):
    """Test successfully generating a shift report."""
    mock_get_data.return_value = {
        "shift_info": {"team_name": "Test Team"},
        "pms": [],
        "mos": [],
    }

    response = logged_in_client.post(
        "/reporting/generate",
        data={
            "report_type": "shift_report",
            "shift_date": "2023-10-27",
            "shift_name": "Early",
            "handover_from_previous": "Note 1\r\nNote 2",
            "handover_to_next": "Next 1\r\nNext 2",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Report generated successfully" in response.data

    # Verify report was created in DB (title is now auto-generated)
    report = (
        report_models.Report.query.filter_by(
            report_type="shift_report", generated_by=sample_user.id
        )
        .order_by(report_models.Report.id.desc())
        .first()
    )
    assert report is not None
    assert report.generated_by == sample_user.id
    # Verify title contains the key info
    assert "2023-10-27" in report.title
    assert "Early" in report.title
    data = report.data
    assert "handover_from_previous" in data["shift_info"]
    handover_items = data["shift_info"]["handover_from_previous"]
    assert any(
        item == "Note 1"
        or item == "Note 2"
        or (isinstance(item, dict) and item.get("description") in {"Note 1", "Note 2"})
        for item in handover_items
    )


@patch(
    "apps.reporting.src.services.data_aggregator.DataAggregator"
    ".get_aggregated_weekend_data"
)
def test_generate_weekend_report_success(mock_get_data, logged_in_client):
    """Test successfully generating a weekend report."""
    mock_get_data.return_value = {"summary": "Weekend stuff", "report_info": {}}

    response = logged_in_client.post(
        "/reporting/generate",
        data={
            "report_type": "weekend_report",
            "weekend_date": "2023-10-28",
            "handover_to_next": "Instruction 1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Report generated successfully" in response.data

    report = (
        report_models.Report.query.filter_by(report_type="weekend_report")
        .order_by(report_models.Report.id.desc())
        .first()
    )
    assert report is not None
    # Check title contains the date
    assert "2023-10-28" in report.title
    # Check that handover_to_next was mapped to handover_instructions
    assert report.data["handover_instructions"] == ["Instruction 1"]


def test_report_detail(logged_in_client, app):
    """Test viewing report detail."""
    # Create a dummy report
    with app.app_context():
        report = report_models.Report(
            title="Detail Test",
            report_type="shift_report",
            parameters={},
            data={"shift_info": {"team_name": "NonExistent"}},
            generated_by=1,  # Assuming user id 1
        )
        report_models.db.session.add(report)
        report_models.db.session.commit()
        report_id = report.id

    response = logged_in_client.get(f"/reporting/{report_id}")
    assert response.status_code == 200
    assert b"Detail Test" in response.data


def test_update_report_data_header(logged_in_client, app):
    """Test updating report header."""
    with app.app_context():
        report = report_models.Report(
            title="Update Test", report_type="shift_report", data={}
        )
        report_models.db.session.add(report)
        report_models.db.session.commit()
        report_id = report.id

    response = logged_in_client.post(
        f"/reporting/{report_id}/update",
        json={"section": "header", "shift": "Late", "team_name": "Team B"},
    )

    assert response.status_code == 200
    assert response.json["success"] is True

    with app.app_context():
        updated_report = report_models.Report.query.get(report_id)
        assert updated_report.data["shift_info"]["shift"] == "Late"
        assert updated_report.data["team_name"] == "Team B"


def test_update_report_data_handover_add(logged_in_client, app):
    """Test adding handover item."""
    with app.app_context():
        report = report_models.Report(
            title="Handover Test", report_type="shift_report", data={"shift_info": {}}
        )
        report_models.db.session.add(report)
        report_models.db.session.commit()
        report_id = report.id

    response = logged_in_client.post(
        f"/reporting/{report_id}/update",
        json={
            "section": "handover_to",
            "action": "add",
            "description": "New Task",
            "title": "Task Title",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        updated_report = report_models.Report.query.get(report_id)
        # handover_to maps to handover_to_next
        handovers = updated_report.data["shift_info"]["handover_to_next"]
        assert len(handovers) == 1
        assert handovers[0]["title"] == "Task Title"
        assert handovers[0]["description"] == "New Task"


def test_update_report_data_breakdown_edit(logged_in_client, app):
    """Test editing breakdown item."""
    with app.app_context():
        report = report_models.Report(
            title="Breakdown Test",
            report_type="shift_report",
            data={"breakdowns": [{"description": "Old"}]},
        )
        report_models.db.session.add(report)
        report_models.db.session.commit()
        report_id = report.id

    response = logged_in_client.post(
        f"/reporting/{report_id}/update",
        json={
            "section": "breakdown",
            "action": "edit",
            "index": 0,
            "description": "Updated",
            "duration": "1h",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        updated_report = report_models.Report.query.get(report_id)
        assert updated_report.data["breakdowns"][0]["description"] == "Updated"
        assert updated_report.data["breakdowns"][0]["duration"] == "1h"


def test_update_report_data_activities_delete(logged_in_client, app):
    """Test deleting activity."""
    with app.app_context():
        report = report_models.Report(
            title="Act Test",
            report_type="shift_report",
            data={"break_activities": [{"title": "To Delete"}]},
        )
        report_models.db.session.add(report)
        report_models.db.session.commit()
        report_id = report.id

    response = logged_in_client.post(
        f"/reporting/{report_id}/update",
        json={
            "section": "activities",
            "action": "delete",
            "index": 0,
            "type": "flux_ticket",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        updated_report = report_models.Report.query.get(report_id)
        assert len(updated_report.data["break_activities"]) == 0


def test_update_unknown_section(logged_in_client, app):
    """Test updating unknown section."""
    with app.app_context():
        report = report_models.Report(title="Unknown", report_type="test")
        report_models.db.session.add(report)
        report_models.db.session.commit()
        report_id = report.id

    response = logged_in_client.post(
        f"/reporting/{report_id}/update", json={"section": "unknown_section"}
    )

    assert response.status_code == 400
    assert response.json["success"] is False
    assert response.json["error"] == "Unknown section or action"


def test_export_report_markdown(logged_in_client, app):
    """Test exporting report to markdown."""
    with app.app_context():
        report = report_models.Report(
            title="Export Test",
            report_type="shift_report",
            data={
                "shift_info": {
                    "team_name": "Team A",
                    "handover_from_previous": [
                        "Note 1",
                        {"asset": "A1", "title": "T1", "description": "D1"},
                    ],
                },
                "breakdowns": [
                    {
                        "equipment_line": "B1",
                        "timestamp": "2023-10-10 12:00:00",
                        "duration": "30m",
                        "description": "Fault 1",
                    }
                ],
            },
        )
        report_models.db.session.add(report)
        report_models.db.session.commit()
        report_id = report.id

    # Mock send_file to avoid actual file system response issues in test client
    # But wait, send_file returns a response object.
    # We can just check content-type or if it returns 200.
    # Also we need to verify report_generator was called?
    # No, we want to exercise the code in report_generator.

    # We need to NOT mock ReportGenerator if we want coverage.

    response = logged_in_client.get(f"/reporting/{report_id}/export/markdown")
    # If successful, it sends file.
    assert response.status_code == 200
    assert (
        "text/markdown" in response.headers["Content-Type"]
        or "application/octet-stream" in response.headers["Content-Type"]
    )


class TestReportingBackendWorkflows:
    """Consolidated backend tests for Reporting application."""

    @pytest.fixture(autouse=True)
    def setup_app_context(self, app):
        with app.app_context():
            # Setup necessary table for tests
            # We are mocking behavior mostly, but for functional tests using client/db
            # we need robust mocks or real in-memory db.
            # Here we rely on app context setup.
            yield

    @pytest.fixture
    def mock_services(self):
        # Patch the CLASSES using the reference in the ROUTE module
        # This is more robust as it uses the name bound in the route file
        with (
            patch(
                "apps.reporting.src.routes.reporting.da_service.DataAggregator"
            ) as MockAggregatorShift,
            patch(
                "apps.reporting.src.routes.reporting.rg_service.ReportGenerator"
            ) as MockGeneratorShift,
        ):
            # No need to mock db session here if we are not testing db_connection
            # get_db_connection was removed.

            yield {
                "agg_shift": MockAggregatorShift.return_value,
                "gen_shift": MockGeneratorShift.return_value,
                "agg_weekend": MockAggregatorShift.return_value,
                "gen_weekend": MockGeneratorShift.return_value,
            }

    def test_reporting_index_route(self, auth_client, mock_services):
        """Test GET /reporting/ returns 200 and renders the page."""
        # Test basic route accessibility - mocking is complex for templates
        # The route should work even with empty data
        response = auth_client.get("/reporting/")
        assert response.status_code == 200
        # Verify page renders with expected structure
        assert b"Reporting" in response.data
        assert b"reportingTable" in response.data

    def test_reporting_generate_route(self, auth_client):
        """Test GET/POST /reporting/generate."""
        res = auth_client.get("/reporting/generate")
        assert res.status_code == 200

        # POST without data fails (missing required fields)
        # We need to send data to satisfy NOT NULL constraints if we want 200/302
        # Or assert that it handles failure gracefully (e.g. 200 with error, or
        # raise exception)
        # The route expects 'title', 'report_type' in form.

        post_data = {
            "title": "Test Title",
            "report_type": "shift_report",  # Valid type
            "format": "html",
        }

        # We need to mock aggregator call inside route OR let it fail deeper
        # Ideally, use the mock_services fixture
        with patch(
            "apps.reporting.src.services.data_aggregator.DataAggregator"
        ) as MockAgg:
            MockAgg.return_value.get_aggregated_shift_data.return_value = (
                {}
            )  # Return empty dict for data

            res = auth_client.post(
                "/reporting/generate", data=post_data, follow_redirects=True
            )
            assert res.status_code == 200
            # Should redirect to index and flash success
            assert (
                b"Report generated successfully" in res.data or b"Reporting" in res.data
            )

    def test_report_detail_routes(self, auth_client):
        """Test placeholder routes for detail/download/delete."""
        # Mocking finding a report
        with patch("apps.reporting.src.models.Report") as MockReport:
            mock_inst = MagicMock()
            mock_inst.data = {"key": "value"}
            mock_inst.file_path = "dummy.json"
            MockReport.query.get_or_404.return_value = mock_inst

            res = auth_client.get("/reporting/1")
            assert res.status_code == 200

        # Download
        with patch("apps.reporting.src.models.Report") as MockReport:
            mock_inst = MagicMock()
            mock_inst.file_path = "dummy.pdf"
            MockReport.query.get_or_404.return_value = mock_inst

            with patch("os.path.exists", return_value=True):
                with patch(
                    "apps.reporting.src.routes.reporting.send_file"
                ) as mock_send:
                    mock_send.return_value = "File Sent"
                    res = auth_client.get("/reporting/1/download")
                    assert res.status_code == 200

    def test_new_reporting_workflow(self, auth_client, mock_services):
        """Test the full report generation workflow (Shift and Weekend)."""
        # Ensure generator returns a string path, not a mock object
        mock_services["gen_shift"].generate_report.return_value = "dummy_shift.json"
        mock_services["gen_weekend"].generate_report.return_value = "dummy_weekend.json"

        # Ensure aggregator returns JSON-serializable dict, not MagicMock
        mock_services["agg_shift"].get_aggregated_shift_data.return_value = {
            "shift_info": {}
        }
        mock_services["agg_weekend"].get_aggregated_weekend_data.return_value = {
            "weekend_info": {}
        }

        # 1. Generate Shift Report
        shift_data = {
            "title": "Test Shift Report",
            "report_type": "shift_report",
            "format": "html",
            "shift_date": "2026-02-08",
            "shift_name": "Early",
        }
        res = auth_client.post(
            "/reporting/generate", data=shift_data, follow_redirects=True
        )
        assert res.status_code == 200
        assert b"Report generated successfully" in res.data

        # Verify aggregator call
        mock_services["agg_shift"].get_aggregated_shift_data.assert_called_once()
        shift_args, shift_kwargs = mock_services[
            "agg_shift"
        ].get_aggregated_shift_data.call_args
        assert shift_args[0] == "2026-02-08"
        assert shift_args[1] == "Early"
        assert "team_id" in shift_kwargs

        # 2. Generate Weekend Report
        weekend_data = {
            "title": "Test Weekend Report",
            "report_type": "weekend_report",
            "format": "html",
            "weekend_date": "2026-02-07",
        }
        res = auth_client.post(
            "/reporting/generate", data=weekend_data, follow_redirects=True
        )
        assert res.status_code == 200

        # Verify aggregator call
        mock_services["agg_weekend"].get_aggregated_weekend_data.assert_called_once()
        weekend_args, weekend_kwargs = mock_services[
            "agg_weekend"
        ].get_aggregated_weekend_data.call_args
        assert weekend_args[0] == "2026-02-07"
        assert "team_id" in weekend_kwargs


def test_reporting_list_generated_by_resolution(auth_client, app):
    """Test that generated_by user resolution works in reporting list."""
    # auth_client already has session set up with a valid user

    # Mock DB query for Report
    with patch("apps.reporting.src.models.Report.query") as mock_report_query:
        # Mock Reporting
        mock_report = MagicMock()
        mock_report.generated_by = 1
        mock_report.to_dict.return_value = {"id": 1, "title": "Test Report"}
        mock_report.generated_on.desc.return_value = "desc_obj"

        mock_report_query.order_by.return_value.all.return_value = [mock_report]

        # Mock User query - since User is imported inside, we patch where it is defined
        with patch("src.services.db_utils.User.query") as mock_user_query:
            mock_user = MagicMock()
            mock_user.username = "TestUser"
            # filter_by(id=1).first()
            mock_user_query.filter_by.return_value.first.return_value = mock_user

            resp = auth_client.get("/reporting/")
            assert (
                resp.status_code == 200
            ), f"Status: {resp.status_code}, Location: {resp.headers.get('Location')}"


def test_reporting_list_generated_by_exception(auth_client, app):
    """Test exception handling during user resolution."""
    # auth_client already has session set up

    with patch("apps.reporting.src.models.Report.query") as mock_report_query:
        mock_report = MagicMock()
        mock_report.generated_by = 1
        mock_report.to_dict.return_value = {"id": 1}
        mock_report_query.order_by.return_value.all.return_value = [mock_report]

        # Patch User query to raise exception
        with patch("src.services.db_utils.User.query") as mock_user_query:
            mock_user_query.filter_by.side_effect = Exception("User DB Error")

            resp = auth_client.get("/reporting/")
            assert resp.status_code == 200


def test_generate_shift_report_missing_shift_info(auth_client, app):
    """Test generating shift report when data aggregator returns data without
    shift_info."""
    with patch("apps.reporting.src.services.data_aggregator.DataAggregator") as MockAgg:
        # return empty dict (no shift_info)
        MockAgg.return_value.get_aggregated_shift_data.return_value = {}

        with patch("apps.reporting.src.models.Report") as MockReportModel:
            # Just mock the model instantiation to verify call args or avoid crashes.

            # Mock db.session.add/commit to avoid detached instance errors.
            with patch("src.services.db_utils.db.session"):
                resp = auth_client.post(
                    "/reporting/generate",
                    data={
                        "report_type": "shift_report",
                        "shift_date": "2023-01-01",
                        "shift_name": "Early",
                        "handover_from_previous": "Note 1",
                        "handover_to_next": "Note 2",
                    },
                )

                assert resp.status_code == 302
                # Handovers are now stored in root data with report_type
                # Call args can be inspected if needed.
                call_args = MockReportModel.call_args[1]
                data = call_args["data"]
                # Check handovers in either root or shift_info
                assert data.get("handover_from_previous") == ["Note 1"] or data.get(
                    "shift_info", {}
                ).get("handover_from_previous") == ["Note 1"]
                assert data.get("handover_to_next") == ["Note 2"] or data.get(
                    "shift_info", {}
                ).get("handover_to_next") == ["Note 2"]


def test_report_detail_exceptions(auth_client, app):
    """Test exceptions in report_detail fetch logic."""
    # Mock Report.query.get_or_404
    with patch("apps.reporting.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.report_type = "shift_report"
        mock_report.data = {"team_name": "Team A"}
        mock_query.get_or_404.return_value = mock_report

        # 1. Test Team query exception
        with patch("src.services.db_utils.db.session.query") as mock_db_query:
            mock_db_query.side_effect = Exception("Team Query Fail")

            # 2. Test Asset query exception
            with patch("src.services.db_utils.Asset.query") as mock_asset_query:
                # Asset query is a property on model usually, but if it is query object
                # Asset.query.with_entities...
                mock_asset_query.with_entities.side_effect = Exception("Asset Fail")

                # 3. Test config load exception is hard to trigger unless file missing
                # or invalid json.
                # We can patch open

                resp = auth_client.get("/reporting/1")
                assert resp.status_code == 200


def test_update_report_data_header_mock(auth_client, app):
    """Test updating header section."""
    with patch("apps.reporting.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.data = {"shift_info": {}}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            resp = auth_client.post(
                "/reporting/1/update",
                json={
                    "section": "header",
                    "date": "2023-01-01",
                    "shift": "Early",
                    "team_name": "Team New",
                    "team_color": "#ffffff",
                },
            )
            assert resp.status_code == 200
            assert mock_report.data["shift_info"]["team_name"] == "Team New"
            assert mock_report.data["team_color"] == "#ffffff"


def test_update_report_data_metadata(auth_client, app):
    """Test updating metadata section."""
    with patch("apps.reporting.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.data = {}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            resp = auth_client.post(
                "/reporting/1/update",
                json={
                    "section": "metadata",
                    "key": "some_key",
                    "value": "some_value",
                },
            )
            assert resp.status_code == 200
            assert mock_report.data["some_key"] == "some_value"


def test_update_report_handover_initialization(auth_client, app):
    """Test handover list initialization when missing."""
    with patch("apps.reporting.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        # Data has no shift_info
        mock_report.data = {}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            # Add item to handover_from, trigger init of shift_info and list
            resp = auth_client.post(
                "/reporting/1/update",
                json={
                    "section": "handover_from",
                    "action": "add",
                    "description": "New Item",
                },
            )
            assert resp.status_code == 200
            assert "shift_info" in mock_report.data
            assert "handover_from_previous" in mock_report.data["shift_info"]
            assert len(mock_report.data["shift_info"]["handover_from_previous"]) == 1

            # Now test handover_to
            mock_report.data = {}  # Reset
            resp = auth_client.post(
                "/reporting/1/update",
                json={
                    "section": "handover_to",
                    "action": "add",
                    "description": "New Item",
                },
            )
            assert resp.status_code == 200
            assert "handover_to_next" in mock_report.data["shift_info"]


def test_update_report_activities_add(auth_client, app):
    """Test adding activities (Engineering Support vs Flux)."""
    with patch("apps.reporting.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.data = {}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            # Add Engineering Support
            resp = auth_client.post(
                "/reporting/1/update",
                json={
                    "section": "activities",
                    "action": "add",
                    "type": "engineering_support",  # Trigger target_key value.
                    "description": "Eng Item",
                },
            )
            assert resp.status_code == 200
            assert "engineering_support" in mock_report.data
            assert len(mock_report.data["engineering_support"]) == 1

            # Delete item
            resp = auth_client.post(
                "/reporting/1/update",
                json={
                    "section": "engineering_support",
                    "action": "delete",
                    "index": 0,
                },
            )
            assert resp.status_code == 200
            assert len(mock_report.data["engineering_support"]) == 0


def test_report_detail_technician_count_logic(auth_client, app):
    """Test technician count logic branches."""
    # Mock Report.query.get_or_404
    with patch("apps.reporting.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.report_type = "shift_report"
        # Case 1: attendance_total is in data
        mock_report.data = {"attendance_total": 5}
        mock_query.get_or_404.return_value = mock_report

        auth_client.get("/reporting/1")
        # We can check context but that's harder without capture_templates
        # We assume it runs without error covering the lines

        # Case 2: No attendance_total, but team_name in shift_info
        mock_report.data = {"shift_info": {"team_name": "Team A"}}

        with patch("src.services.db_utils.Team.query") as mock_team_q:
            mock_team = MagicMock()
            mock_team_q.filter_by.return_value.first.return_value = mock_team

            with patch("src.services.db_utils.User.query") as mock_user_q:
                mock_user_q.filter_by.return_value.count.return_value = 10

                resp = auth_client.get("/reporting/1")
                assert resp.status_code == 200


def test_generate_shift_report_handles_naive_completion_timestamps(
    logged_in_client, app
):
    """Generate shift report with naive timestamps.

    Successfully when completed corrective MOs use naive datetimes.
    """
    with app.app_context():
        asset = Asset(name="Report Asset", asset_code="RPT-NAIVE-001")
        db.session.add(asset)
        db.session.flush()

        db.session.add(
            MaintenanceOrder(
                asset_id=asset.id,
                description="Corrective completed during night shift",
                order_type="Corrective",
                status="Completed",
                created_at=datetime(2026, 3, 6, 17, 30),
                modified_on=datetime(2026, 3, 6, 19, 35),
            )
        )
        db.session.commit()

    response = logged_in_client.post(
        "/reporting/generate",
        data={
            "report_type": "shift_report",
            "shift_date": "2026-03-06",
            "shift_name": "Night",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Report generated successfully" in response.data


def test_shift_report_detail_renders_mo_and_asset_links(logged_in_client, app):
    """Shift report detail should render linked asset code and MO links in sections."""
    with app.app_context():
        asset = Asset(name="Link Test Asset", asset_code="AST-9001")
        db.session.add(asset)
        db.session.flush()

        mo = MaintenanceOrder(
            asset_id=asset.id,
            description="Link integrity check",
            order_type="Reactive",
            status="In Progress",
            priority="High",
        )
        db.session.add(mo)
        db.session.flush()

        report = report_models.Report(
            title="Shift Link Test",
            report_type="shift_report",
            data={
                "report_info": {
                    "date": "2026-03-06",
                    "shift": "Night",
                    "team_name": "Team A",
                    "handover_from_previous": [
                        {
                            "mo_id": f"MO-{mo.id}",
                            "asset": "AST-9001",
                            "title": "Instruction",
                            "description": "From previous",
                        }
                    ],
                    "handover_to_next": [
                        {
                            "mo_id": mo.id,
                            "asset": "AST-9001",
                            "title": "Instruction",
                            "description": "To next",
                        }
                    ],
                },
                "breakdowns": [
                    {
                        "id": mo.id,
                        "description": "Breakdown linked to MO",
                        "timestamp": "19:30",
                        "duration": "20",
                    }
                ],
            },
            generated_by=1,
        )
        report_models.db.session.add(report)
        report_models.db.session.commit()

        report_id = report.id
        asset_id = asset.id
        mo_id = mo.id

    response = logged_in_client.get(f"/reporting/{report_id}")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert f"/assets/{asset_id}" in html
    assert "AST-9001" in html
    assert f"/maintenance_orders/{mo_id}" in html
    assert f"MO-{mo_id}" in html
