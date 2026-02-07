import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Skip all tests in this file if REPORTS_ENABLED is not True
pytestmark = pytest.mark.skipif(
    os.getenv("REPORTS_ENABLED", "true").lower() not in ("true", "1", "t"),
    reason="Reports module is disabled (REPORTS_ENABLED=False)",
)


class TestReportsBackend:
    """Consolidated backend tests for Reports application."""

    @pytest.fixture(autouse=True)
    def setup_app_context(self, app):
        with app.app_context():
            yield

    @pytest.fixture
    def mock_services(self):
        with (
            patch("apps.reports.src.routes.reports.get_db_connection") as mock_db,
            patch(
                "apps.reports.src.routes.incidents.DataAggregator"
            ) as MockAggregatorInc,
            patch(
                "apps.reports.src.routes.incidents.ReportGenerator"
            ) as MockGeneratorInc,
            patch(
                "apps.reports.src.routes.shift_report.DataAggregator"
            ) as MockAggregatorShift,
            patch(
                "apps.reports.src.routes.shift_report.ReportGenerator"
            ) as MockGeneratorShift,
            patch(
                "apps.reports.src.routes.weekend_report.DataAggregator"
            ) as MockAggregatorWeekend,
            patch(
                "apps.reports.src.routes.weekend_report.ReportGenerator"
            ) as MockGeneratorWeekend,
        ):
            mock_session = MagicMock()
            mock_db.return_value.session = mock_session

            yield {
                "db": mock_db,
                "agg_inc": MockAggregatorInc.return_value,
                "gen_inc": MockGeneratorInc.return_value,
                "agg_shift": MockAggregatorShift.return_value,
                "gen_shift": MockGeneratorShift.return_value,
                "agg_weekend": MockAggregatorWeekend.return_value,
                "gen_weekend": MockGeneratorWeekend.return_value,
            }

    # =========================================================================
    # MAIN REPORTS DASHBOARD
    # =========================================================================

    def test_reports_index_route(self, auth_client, mock_services):
        """Test GET /reports/ lists reports."""
        mock_db = mock_services["db"]
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ("reports",)

        row1 = MagicMock(
            id=1,
            title="Rep 1",
            report_type="Shift",
            format="PDF",
            generated_on=datetime.now(),
            generated_by_name="User1",
            parameters="{}",
            file_path="report_1.pdf",
        )
        mock_db.return_value.session.execute.side_effect = [mock_result, [row1]]

        response = auth_client.get("/reports/")
        assert (
            response.status_code == 200
        ), f"Redirect to: {response.headers.get('Location')}"
        assert b"Rep 1" in response.data

    def test_reports_generate_route(self, auth_client):
        """Test GET/POST /reports/generate."""
        res = auth_client.get("/reports/generate")
        assert res.status_code == 200

        res = auth_client.post("/reports/generate", data={})
        assert res.status_code == 302
        assert "/reports" in res.location

    def test_report_detail_routes(self, auth_client):
        """Test placeholder routes for detail/download/delete."""
        res = auth_client.get("/reports/1")
        assert res.status_code == 302

        res = auth_client.get("/reports/1/download")
        assert res.status_code == 302

        res = auth_client.post("/reports/1/delete")
        assert res.status_code == 302

    # =========================================================================
    # INCIDENTS
    # =========================================================================

    def test_incident_list(self, client, mock_services):
        """Test GET /reports/incidents/."""
        mock_services["agg_inc"].get_incidents.return_value = [
            {"id": 1, "description": "Broken Arm"}
        ]
        response = client.get("/reports/incidents/")
        assert response.status_code == 200
        assert b"Broken Arm" in response.data

    def test_new_incident_form(self, client):
        """Test GET /reports/incidents/new."""
        response = client.get("/reports/incidents/new")
        assert response.status_code == 200

    def test_create_incident_success(self, client, app):
        """Test POST /reports/incidents/ creates incident."""
        with app.app_context():
            with patch("src.services.db_utils.db") as mock_db:
                mock_session = MagicMock()
                mock_db.session = mock_session
                data = {
                    "incident_type": "Injury",
                    "equipment_line": "Line A",
                    "description": "Cut finger",
                    "severity": "Low",
                }
                response = client.post("/reports/incidents/", data=data)
                assert response.status_code == 302
                mock_session.add.assert_called()
                mock_session.commit.assert_called()

    def test_aggregate_report(self, client, mock_services):
        """Test GET /reports/incidents/aggregate."""
        mock_services["agg_inc"].get_incidents.return_value = []
        mock_services["gen_inc"].generate_summary_stats.return_value = {"total": 0}

        response = client.get("/reports/incidents/aggregate")
        assert response.status_code == 200

    def test_export_aggregate_report(self, client, mock_services):
        """Test POST /reports/incidents/aggregate/export."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(b"content")
            tmp_path = tmp.name

        mock_services["gen_inc"].generate_report.return_value = tmp_path

        response = client.post(
            "/reports/incidents/aggregate/export",
            data={"start_date": "2024-01-01", "end_date": "2024-01-02"},
        )
        assert response.status_code == 200
        assert response.headers["Content-Disposition"].startswith("attachment")

    # =========================================================================
    # SHIFT REPORTS
    # =========================================================================

    def test_shift_report(self, client, mock_services):
        """Test GET /reports/shift/."""
        mock_services["agg_shift"].get_shift_data.return_value = []
        mock_services["gen_shift"].generate_summary_stats.return_value = {}

        response = client.get("/reports/shift/")
        assert response.status_code == 200

    def test_export_shift_report(self, client, mock_services):
        """Test POST /reports/shift/export."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(b"content")
            tmp_path = tmp.name

        mock_services["gen_shift"].generate_report.return_value = tmp_path

        response = client.post(
            "/reports/shift/export", data={"date": "2024-01-01", "shift": "Morning"}
        )
        assert response.status_code == 200

    # =========================================================================
    # WEEKEND REPORTS
    # =========================================================================

    def test_weekend_report(self, client, mock_services):
        """Test GET /reports/weekend/."""
        mock_services["agg_weekend"].get_weekend_tasks.return_value = []
        mock_services["gen_weekend"].generate_summary_stats.return_value = {}

        response = client.get("/reports/weekend/")
        assert response.status_code == 200

    def test_export_weekend_report(self, client, mock_services):
        """Test POST /reports/weekend/export."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(b"content")
            tmp_path = tmp.name

        mock_services["gen_weekend"].generate_report.return_value = tmp_path

        response = client.post(
            "/reports/weekend/export",
            data={"start_date": "2024-01-01", "end_date": "2024-01-02"},
        )
        assert response.status_code == 200


class TestReportsIncidentsFunctional:
    """High-fidelity functional tests for incidents blueprint routes."""

    def test_incident_list_empty(self, client):
        """Test listing incidents when none exist."""
        from src.services.db_utils import db

        with client.application.app_context():
            db.create_all()
        response = client.get("/reports/incidents/")
        assert response.status_code == 200
        assert b"Incident Reports" in response.data

    def test_create_incident_success(self, client):
        """Test successful incident creation verified in DB."""
        from apps.reports.src.models import Incident
        from src.services.db_utils import db

        with client.application.app_context():
            db.create_all()
        data = {
            "incident_type": "Breakdown",
            "equipment_line": "Line 1",
            "description": "Functional Test failure",
            "severity": "High",
        }
        response = client.post("/reports/incidents/", data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b"Incident logged successfully" in response.data
        with client.application.app_context():
            incident = Incident.query.filter_by(
                description="Functional Test failure"
            ).first()
            assert incident is not None
            assert incident.severity == "High"

    def test_incident_export_success(self, client, tmp_path):
        """Test exporting incidents as CSV using real filesystem path."""
        from apps.reports.src.models import Incident
        from apps.reports.src.services.report_generator import ReportGenerator
        from src.services.db_utils import db

        with client.application.app_context():
            db.create_all()
            inc = Incident(
                incident_type="Maintenance",
                equipment_line="Line 2",
                description="Export Test",
                severity="Low",
                technician_name="TestBot",
            )
            db.session.add(inc)
            db.session.commit()
        data = {"start_date": "2020-01-01", "end_date": "2030-12-31", "format": "csv"}
        with pytest.MonkeyPatch().context() as m:
            m.setattr(ReportGenerator, "reports_dir", str(tmp_path))
            response = client.post("/reports/incidents/aggregate/export", data=data)
            assert response.status_code == 200
            assert response.headers["Content-Disposition"].startswith("attachment")
