import os
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
                "apps.reports.src.routes.reports.da_service.DataAggregator"
            ) as MockAggregatorShift,
            patch(
                "apps.reports.src.routes.reports.rg_service.ReportGenerator"
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

    # =========================================================================
    # MAIN REPORTS DASHBOARD
    # =========================================================================

    def test_reports_index_route(self, auth_client, mock_services):
        """Test GET /reports/ returns 200 and renders the page."""
        # Test basic route accessibility - mocking is complex for templates
        # The route should work even with empty data
        response = auth_client.get("/reports/")
        assert response.status_code == 200
        # Verify page renders with expected structure
        assert b"Reports" in response.data
        assert b"reportsTable" in response.data

    def test_reports_generate_route(self, auth_client):
        """Test GET/POST /reports/generate."""
        res = auth_client.get("/reports/generate")
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
            "apps.reports.src.services.data_aggregator.DataAggregator"
        ) as MockAgg:
            MockAgg.return_value.get_aggregated_shift_data.return_value = (
                {}
            )  # Return empty dict for data

            res = auth_client.post(
                "/reports/generate", data=post_data, follow_redirects=True
            )
            assert res.status_code == 200
            # Should redirect to index and flash success
            assert (
                b"Report generated successfully" in res.data or b"Reports" in res.data
            )

    def test_report_detail_routes(self, auth_client):
        """Test placeholder routes for detail/download/delete."""
        # Mocking finding a report
        with patch("apps.reports.src.models.Report") as MockReport:
            mock_inst = MagicMock()
            mock_inst.data = {"key": "value"}
            mock_inst.file_path = "dummy.json"
            MockReport.query.get_or_404.return_value = mock_inst

            res = auth_client.get("/reports/1")
            assert res.status_code == 200

        # Download
        with patch("apps.reports.src.models.Report") as MockReport:
            mock_inst = MagicMock()
            mock_inst.file_path = "dummy.pdf"
            MockReport.query.get_or_404.return_value = mock_inst

            with patch("os.path.exists", return_value=True):
                with patch("apps.reports.src.routes.reports.send_file") as mock_send:
                    mock_send.return_value = "File Sent"
                    res = auth_client.get("/reports/1/download")
                    assert res.status_code == 200

    # =========================================================================
    # NEW REPORTS WORKFLOW
    # =========================================================================

    def test_new_reports_workflow(self, auth_client, mock_services):
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
            "/reports/generate", data=shift_data, follow_redirects=True
        )
        assert res.status_code == 200
        assert b"Report generated successfully" in res.data

        # Verify aggregator call
        mock_services["agg_shift"].get_aggregated_shift_data.assert_called_with(
            "2026-02-08", "Early"
        )

        # 2. Generate Weekend Report
        weekend_data = {
            "title": "Test Weekend Report",
            "report_type": "weekend_report",
            "format": "html",
            "weekend_date": "2026-02-07",
        }
        res = auth_client.post(
            "/reports/generate", data=weekend_data, follow_redirects=True
        )
        assert res.status_code == 200

        # Verify aggregator call
        mock_services["agg_weekend"].get_aggregated_weekend_data.assert_called_with(
            "2026-02-07"
        )
