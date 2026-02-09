from unittest.mock import patch

import pytest

from apps.reports.src import models as report_models


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


def test_reports_access_no_login(client):
    """Test accessing reports page without login."""
    response = client.get("/reports/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_reports_list_page(logged_in_client):
    """Test accessing the reports list page."""
    response = logged_in_client.get("/reports/")
    assert response.status_code == 200
    # The title in base template or reports template
    assert b"Reports" in response.data


def test_generate_report_page_get(logged_in_client):
    """Test accessing the report generation page via GET."""
    response = logged_in_client.get("/reports/generate")
    assert response.status_code == 200
    assert b"Generate Report" in response.data


def test_generate_report_no_title(logged_in_client):
    """Test generating a report without a title."""
    response = logged_in_client.post(
        "/reports/generate", data={"report_type": "shift_report"}, follow_redirects=True
    )
    assert b"Report Title is required" in response.data


def test_generate_report_no_type(logged_in_client):
    """Test generating a report without a type."""
    response = logged_in_client.post(
        "/reports/generate", data={"title": "Test Report"}, follow_redirects=True
    )
    assert b"Report Type is required" in response.data


def test_generate_shift_report_missing_date(logged_in_client):
    """Test generating a shift report without a date."""
    response = logged_in_client.post(
        "/reports/generate",
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
        "/reports/generate",
        data={"title": "Test Weekend Report", "report_type": "weekend_report"},
        follow_redirects=True,
    )
    assert b"Weekend Date is required" in response.data


@patch(
    "apps.reports.src.services.data_aggregator.DataAggregator.get_aggregated_shift_data"
)
def test_generate_shift_report_success(mock_get_data, logged_in_client, sample_user):
    """Test successfully generating a shift report."""
    mock_get_data.return_value = {
        "shift_info": {"team_name": "Test Team"},
        "pms": [],
        "mos": [],
    }

    response = logged_in_client.post(
        "/reports/generate",
        data={
            "title": "Valid Shift Report",
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

    # Verify report was created in DB
    report = report_models.Report.query.filter_by(title="Valid Shift Report").first()
    assert report is not None
    assert report.generated_by == sample_user.id
    data = report.data
    assert "handover_from_previous" in data["shift_info"]
    assert data["shift_info"]["handover_from_previous"] == ["Note 1", "Note 2"]


@patch(
    "apps.reports.src.services.data_aggregator.DataAggregator"
    ".get_aggregated_weekend_data"
)
def test_generate_weekend_report_success(mock_get_data, logged_in_client):
    """Test successfully generating a weekend report."""
    mock_get_data.return_value = {"summary": "Weekend stuff"}

    response = logged_in_client.post(
        "/reports/generate",
        data={
            "title": "Valid Weekend Report",
            "report_type": "weekend_report",
            "weekend_date": "2023-10-28",
            "handover_to_next": "Instruction 1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Report generated successfully" in response.data

    report = report_models.Report.query.filter_by(title="Valid Weekend Report").first()
    assert report is not None
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

    response = logged_in_client.get(f"/reports/{report_id}")
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
        f"/reports/{report_id}/update",
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
        f"/reports/{report_id}/update",
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
        f"/reports/{report_id}/update",
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
        f"/reports/{report_id}/update",
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
        f"/reports/{report_id}/update", json={"section": "unknown_section"}
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

    response = logged_in_client.get(f"/reports/{report_id}/export/markdown")
    # If successful, it sends file.
    assert response.status_code == 200
    assert (
        "text/markdown" in response.headers["Content-Type"]
        or "application/octet-stream" in response.headers["Content-Type"]
    )
