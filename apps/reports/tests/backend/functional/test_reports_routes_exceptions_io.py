"""I/O and refresh report-route exception scenarios."""

from unittest.mock import MagicMock, patch

from flask import session

from apps.reports.src import models as report_models
from apps.reports.src.routes.reports import (
    _sync_file_reports,
    delete_report,
    download_report,
    export_report,
    report_detail,
)
from src.services.db_utils import db


class TestDownloadReportCoverage:
    """Tests for download_report route coverage."""

    def test_download_report_file_exists(self, app, tmp_path):
        """Test download when file exists."""
        test_file = tmp_path / "test_report.txt"
        test_file.write_text("Test content")

        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                file_path=str(test_file),
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = download_report(rid)
                # Should return file
                assert response is not None

    def test_download_report_file_missing(self, app):
        """Test download when file does not exist."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                file_path="/nonexistent/file.txt",
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = download_report(rid)
                # Should redirect
                assert response.status_code == 302


class TestDeleteReportCoverage:
    """Tests for delete_report route coverage."""

    def test_delete_report_success(self, app, tmp_path):
        """Test successful report deletion with file."""
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("Delete me")

        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                file_path=str(test_file),
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(method="POST"):
                session["user_id"] = 1
                response = delete_report(rid)
                # Should redirect
                assert response.status_code == 302
                # File should be deleted
                assert not test_file.exists()

    def test_delete_report_db_error(self, app):
        """Test delete when DB error occurs."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(method="POST"):
                session["user_id"] = 1
                with patch.object(
                    db.session, "commit", side_effect=Exception("DB error")
                ):
                    response = delete_report(rid)
                    assert response.status_code == 302


class TestExportReportCoverage:
    """Tests for export_report route coverage."""

    def test_export_report_no_data(self, app):
        """Test export when no data available."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                data=None,
                file_path=None,
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = export_report(rid, "txt")
                # Should redirect with flash
                assert response.status_code == 302

    def test_export_report_from_json_file(self, app, tmp_path):
        """Test export loading data from JSON file."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"title": "Test", "test": "data"}')

        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                data=None,
                file_path=str(json_file),
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                with patch(
                    "apps.reports.src.services.report_generator."
                    "ReportGenerator.generate_report"
                ) as mock_gen:
                    mock_gen.return_value = str(tmp_path / "out.txt")
                    (tmp_path / "out.txt").write_text("export")
                    response = export_report(rid, "txt")
                    assert response is not None

    def test_export_report_string_parameters(self, app, tmp_path):
        """Test export with string parameters (JSON encoded)."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                data={"test": "data"},
                parameters='{"date": "2026-01-01"}',
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                with patch(
                    "apps.reports.src.services.report_generator."
                    "ReportGenerator.generate_report"
                ) as mock_gen:
                    mock_gen.return_value = str(tmp_path / "out.txt")
                    (tmp_path / "out.txt").write_text("export")
                    response = export_report(rid, "txt")
                    assert response is not None

    def test_export_report_generator_exception(self, app):
        """Test export when generator raises exception."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                data={"test": "data"},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                with patch(
                    "apps.reports.src.services.report_generator."
                    "ReportGenerator.generate_report",
                    side_effect=Exception("Gen error"),
                ):
                    response = export_report(rid, "txt")
                    # Should redirect
                    assert response.status_code == 302

    def test_export_report_file_not_created(self, app):
        """Test export when file not created."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="TXT",
                generated_by=1,
                data={"test": "data"},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                with patch(
                    "apps.reports.src.services.report_generator."
                    "ReportGenerator.generate_report",
                    return_value="/nonexistent/path.txt",
                ):
                    response = export_report(rid, "txt")
                    # Should redirect
                    assert response.status_code == 302


class TestReportsRouteRefreshScenarios:
    def test_sync_file_reports_returns_when_reports_dir_missing(self, app):
        with app.app_context():
            with (
                patch(
                    "apps.reports.src.routes.reports.rg_service.ReportGenerator"
                ) as mock_rg,
                patch(
                    "apps.reports.src.routes.reports.os.path.exists",
                    return_value=False,
                ),
            ):
                mock_rg.return_value.reports_dir = "C:/tmp/missing-reports"
                _sync_file_reports()

    def test_sync_file_reports_imports_new_json_and_infers_report_types(self, app):
        added = {}

        def capture_add_all(items):
            added["items"] = items

        with app.app_context():
            with (
                patch(
                    "apps.reports.src.routes.reports.rg_service.ReportGenerator"
                ) as mock_rg,
                patch(
                    "apps.reports.src.routes.reports.os.path.exists",
                    return_value=True,
                ),
                patch(
                    "apps.reports.src.routes.reports.os.listdir",
                    return_value=["shift_a.json", "weekend_b.json", "existing.json"],
                ),
                patch("apps.reports.src.routes.reports.open", create=True),
                patch(
                    "apps.reports.src.routes.reports.json.load",
                    side_effect=[
                        {
                            "title": "Shift A",
                            "generated_at": "not-an-iso",
                            "shift_info": {"shift": "Night"},
                        },
                        {
                            "title": "Weekend B",
                            "generated_at": "2026-03-10T10:00:00",
                            "weekend_info": {"shift": "Early"},
                        },
                        {
                            "title": "Existing",
                            "report_type": "shift_report",
                        },
                    ],
                ),
                patch(
                    "apps.reports.src.routes.reports.db.session.add_all",
                    side_effect=capture_add_all,
                ),
                patch("apps.reports.src.routes.reports.db.session.commit"),
                patch(
                    "apps.reports.src.routes.reports.report_models.Report.query"
                ) as mock_query,
            ):
                base = "C:/tmp/reports"
                mock_rg.return_value.reports_dir = base
                mock_query.with_entities.return_value.all.return_value = [
                    (f"{base}\\existing.json",),
                    (f"{base}/existing.json",),
                ]

                _sync_file_reports()

        imported = added["items"]
        assert len(imported) == 2
        assert {r.report_type for r in imported} == {"shift_report", "weekend_report"}

    def test_report_detail_weekend_flattens_handover_when_queries_fail(self, app):
        with app.app_context():
            report = report_models.Report(
                title="Weekend Seeded",
                report_type="weekend_report",
                generated_by=1,
                data={
                    "report_info": {
                        "date": "2026-03-10",
                        "handover_from_previous": [{"description": "From previous"}],
                        "handover_to_next": [{"description": "To next"}],
                    }
                },
            )
            db.session.add(report)
            db.session.commit()

            with app.test_request_context():
                session["user_id"] = 1
                with (
                    patch(
                        "apps.reports.src.routes.reports.db.session.query",
                        side_effect=Exception("teams failed"),
                    ),
                    patch("src.services.db_utils.Asset.query") as mock_asset_query,
                    patch(
                        "src.services.db_utils.MaintenanceOrder.query"
                    ) as mock_mo_query,
                    patch("src.services.db_utils.SparePart.query") as mock_sp_query,
                    patch(
                        "apps.reports.src.routes.reports.render_template"
                    ) as mock_render,
                ):
                    mock_asset_query.with_entities.side_effect = Exception(
                        "assets failed"
                    )
                    mock_mo_query.with_entities.side_effect = Exception("mo failed")
                    mock_sp_query.with_entities.side_effect = Exception("spare failed")
                    mock_render.side_effect = lambda _template, **kwargs: kwargs
                    context = report_detail(report.id)

        assert context["data"]["handover_to_next"][0]["description"] == "To next"
        assert (
            context["data"]["handover_from_previous"][0]["description"]
            == "From previous"
        )
        assert "Red Shift" in context["teams"]

    def test_report_detail_technician_count_falls_back_to_role_query(self, app):
        with app.app_context():
            report = report_models.Report(
                title="Shift Fallback",
                report_type="shift_report",
                generated_by=1,
                data={"report_info": {"team_name": "Red Team"}, "attendance": 0},
            )
            db.session.add(report)
            db.session.commit()

            with app.test_request_context():
                session["user_id"] = 1
                with (
                    patch(
                        "apps.reports.src.routes.reports.render_template"
                    ) as mock_render,
                    patch("src.services.db_utils.Team.query") as mock_team_query,
                    patch("src.services.db_utils.User.query") as mock_user_query,
                    patch("src.services.db_utils.Role.query") as mock_role_query,
                ):
                    missing_team_q = MagicMock()
                    missing_team_q.first.return_value = None
                    fallback_team = MagicMock(name="Team A")
                    fallback_team_q = MagicMock()
                    fallback_team_q.first.return_value = fallback_team
                    mock_team_query.filter_by.side_effect = [
                        missing_team_q,
                        fallback_team_q,
                    ]

                    mock_user_query.filter_by.return_value.count.return_value = 0
                    mock_role = MagicMock(name="Technician")
                    mock_role_query.filter_by.return_value.first.return_value = (
                        mock_role
                    )
                    mock_user_query.filter.return_value.count.return_value = 2

                    mock_render.side_effect = lambda _template, **kwargs: kwargs
                    context = report_detail(report.id)

        assert context["technician_count"] == 2
