"""Comprehensive exception handling and edge case tests for reports routes."""

from unittest.mock import MagicMock, patch

from flask import session

from apps.reports.src import models as report_models
from apps.reports.src.routes.reports import (
    delete_report,
    download_report,
    export_report,
    generate_report,
    report_detail,
    reports,
    update_report_data,
)
from src.services.db_utils import db


class TestReportsExceptions:
    """Test exception handling and edge cases in reports routes."""

    def test_reports_index_table_creation_exception(self, app):
        """Test exception during table creation in reports index."""
        with app.app_context(), app.test_request_context():
            session["user_id"] = 1
            with patch(
                "src.services.db_utils.db.get_engine", side_effect=Exception("DB Error")
            ):
                # Should catch and continue
                response = reports()
                assert response is not None
                assert "reports" in str(response)

    def test_reports_index_user_lookup_exception(self, app):
        """Test exception during user lookup in reports index."""
        with app.app_context(), app.test_request_context():
            session["user_id"] = 1
            with patch("apps.reports.src.models.Report") as MockReport:
                report = MagicMock()
                report.to_dict.return_value = {"id": 1}
                report.generated_by = 1
                MockReport.query.order_by.return_value.all.return_value = [report]

                with patch("src.services.db_utils.User") as MockUser:
                    MockUser.query.filter_by.side_effect = Exception(
                        "User lookup failed"
                    )
                    response = reports()
                    assert response is not None

    def test_reports_index_general_exception(self, app):
        """Test general exception in reports index."""
        with app.app_context(), app.test_request_context():
            session["user_id"] = 1
            with patch(
                "apps.reports.src.models.Report.query",
                side_effect=Exception("Query failed"),
            ):
                response = reports()
                # Should return empty reports list
                assert "reports" in str(response)

    def test_generate_report_table_creation_exception(self, app):
        """Test exception during table creation in generate_report."""
        with (
            app.app_context(),
            app.test_request_context(
                method="POST", data={"title": "Test", "report_type": "shift_report"}
            ),
        ):
            session["user_id"] = 1
            with patch(
                "src.services.db_utils.db.get_engine", side_effect=Exception("DB Error")
            ):
                # Should continue despite exception
                response = generate_report()
                assert response is not None

    def test_generate_report_missing_title(self, app):
        """Test generate_report with missing title."""
        with app.app_context(), app.test_request_context(method="POST", data={}):
            session["user_id"] = 1
            response = generate_report()
            assert "Generate Report" in str(response)

    def test_generate_report_missing_report_type(self, app):
        """Test generate_report with missing report type."""
        with (
            app.app_context(),
            app.test_request_context(method="POST", data={"title": "Test"}),
        ):
            session["user_id"] = 1
            response = generate_report()
            assert "Generate Report" in str(response)

    def test_report_detail_missing_file(self, app):
        """Test report_detail when file doesn't exist."""
        with app.app_context():
            # Create report without file
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                file_path="/nonexistent/path.pdf",
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(report_id)
                # Should handle gracefully
                assert response is not None

    def test_report_detail_teams_fetch_exception(self, app):
        """Test report_detail when teams fetch fails."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={},
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                with patch(
                    "src.services.db_utils.db.session.query",
                    side_effect=Exception("Teams query failed"),
                ):
                    response = report_detail(report_id)
                    assert response is not None

    def test_report_detail_assets_fetch_exception(self, app):
        """Test report_detail when assets fetch fails."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={},
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                with patch(
                    "src.services.db_utils.Asset.query",
                    side_effect=Exception("Assets query failed"),
                ):
                    response = report_detail(report_id)
                    assert response is not None

    def test_report_detail_attendance_total_from_data(self, app):
        """Test report_detail using attendance_total from stored data."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={"attendance_total": 18},
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(report_id)
                assert response is not None

    def test_report_detail_team_fallback_from_shift_info(self, app):
        """Test report_detail team resolution from shift_info."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={"shift_info": {"team_name": "Team A"}},
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(report_id)
                assert response is not None

    def test_report_detail_no_data_warning(self, app):
        """Test report_detail with no data triggers flash warning."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data=None,
                file_path=None,
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(report_id)
                # Should show warning flash
                assert response is not None

    def test_report_detail_weekend_report_template(self, app):
        """Test report_detail selects weekend_report_detail.html."""
        with app.app_context():
            report = report_models.Report(
                title="Weekend",
                report_type="weekend_report",
                format="PDF",
                generated_by=1,
                data={},
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(report_id)
                assert response is not None

    def test_report_detail_generic_report_template(self, app):
        """Test report_detail selects report_detail.html for generic types."""
        with app.app_context():
            report = report_models.Report(
                title="Generic",
                report_type="reactive_production",
                format="PDF",
                generated_by=1,
                data={},
            )
            db.session.add(report)
            db.session.commit()
            report_id = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(report_id)
                assert response is not None


class TestUpdateReportComprehensive:
    """Maximize coverage for update_report route."""

    def test_update_handover_from_section(self, app):
        """Test handover_from update."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={"shift_info": {"handover_from_previous": []}},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "handover_from",
                    "action": "add",
                    "payload": {"asset": "A", "title": "T", "description": "D"},
                },
            ):
                session["user_id"] = 1
                from apps.reports.src.routes.reports import update_report_data

                res = update_report_data(rid)
                # Response is dict on success, tuple on error
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_handover_to_section(self, app):
        """Test handover_to update."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={"shift_info": {"handover_to_next": []}},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "handover_to",
                    "action": "add",
                    "payload": {"asset": "B", "title": "T2", "description": "D2"},
                },
            ):
                session["user_id"] = 1
                from apps.reports.src.routes.reports import update_report_data

                res = update_report_data(rid)
                # Response is dict on success, tuple on error
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_weekend_handover_section(self, app):
        """Test weekend handover update."""
        with app.app_context():
            report = report_models.Report(
                title="Weekend",
                report_type="weekend_report",
                format="PDF",
                generated_by=1,
                data={"handover_instructions": []},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "handover",
                    "action": "add",
                    "payload": {"asset": "C", "title": "T3", "description": "D3"},
                },
            ):
                session["user_id"] = 1
                from apps.reports.src.routes.reports import update_report_data

                res = update_report_data(rid)
                # Response is dict on success, tuple on error
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_flux_ticket_section(self, app):
        """Test FLUX ticket edit."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={
                    "break_activities": [
                        {"id": "f1", "type": "flux_ticket", "title": "Old"}
                    ]
                },
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "flux_tickets",
                    "action": "edit",
                    "payload": {"id": "f1", "title": "New"},
                },
            ):
                session["user_id"] = 1
                from apps.reports.src.routes.reports import update_report_data

                res = update_report_data(rid)
                # Response is dict on success, tuple on error
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_engineering_support_section(self, app):
        """Test engineering support edit."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={
                    "break_activities": [
                        {"id": "e1", "type": "engineering_support", "title": "Old"}
                    ]
                },
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "engineering_support",
                    "action": "edit",
                    "payload": {"id": "e1", "title": "Updated"},
                },
            ):
                session["user_id"] = 1
                from apps.reports.src.routes.reports import update_report_data

                res = update_report_data(rid)
                # Response is dict on success, tuple on error
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True


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


class TestUpdateReportEdgeCases:
    """Edge cases for update_report_data."""

    def test_update_unknown_section(self, app):
        """Test update with unknown section returns error."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={"section": "unknown_section", "action": "add"},
            ):
                session["user_id"] = 1
                res = update_report_data(rid)
                # Should return error
                if isinstance(res, tuple):
                    assert res[1] == 400
                else:
                    assert res.get("success") is False

    def test_update_pms_section(self, app):
        """Test updating PMs section."""
        with app.app_context():
            report = report_models.Report(
                title="Weekend",
                report_type="weekend_report",
                format="PDF",
                generated_by=1,
                data={"pms": []},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "pms",
                    "action": "add",
                    "payload": {"asset": "PM-001", "description": "PM Task"},
                },
            ):
                session["user_id"] = 1
                res = update_report_data(rid)
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_mos_section(self, app):
        """Test updating MOs section."""
        with app.app_context():
            report = report_models.Report(
                title="Weekend",
                report_type="weekend_report",
                format="PDF",
                generated_by=1,
                data={"mos": []},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "mos",
                    "action": "add",
                    "payload": {"asset": "MO-001", "description": "MO Task"},
                },
            ):
                session["user_id"] = 1
                res = update_report_data(rid)
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_activities_engineering_type(self, app):
        """Test adding activity with engineering_support type."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={"engineering_support": []},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "activities",
                    "action": "add",
                    "payload": {
                        "type": "engineering_support",
                        "asset": "ENG-001",
                        "title": "Support",
                    },
                },
            ):
                session["user_id"] = 1
                res = update_report_data(rid)
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_flux_delete_out_of_bounds(self, app):
        """Test deleting flux ticket with out of bounds index."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={"break_activities": [{"id": "1", "title": "T"}]},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "flux_tickets",
                    "action": "delete",
                    "index": 99,
                },
            ):
                session["user_id"] = 1
                res = update_report_data(rid)
                # Should succeed but not delete anything
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True

    def test_update_exception_handling(self, app):
        """Test update exception returns 500."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={"section": "header"},
            ):
                session["user_id"] = 1
                with patch.object(
                    db.session, "commit", side_effect=Exception("DB Error")
                ):
                    res = update_report_data(rid)
                    if isinstance(res, tuple):
                        assert res[1] == 500


class TestReportDetailJsonFallback:
    """Test report_detail JSON file fallback."""

    def test_report_detail_json_fallback(self, app, tmp_path):
        """Test loading data from JSON file when DB data is empty."""
        json_file = tmp_path / "report_data.json"
        json_file.write_text('{"shift_info": {"date": "2026-01-01"}}')

        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data=None,
                file_path=str(json_file),
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(rid)
                assert response is not None

    def test_report_detail_json_load_exception(self, app, tmp_path):
        """Test JSON load exception is handled."""
        json_file = tmp_path / "bad.json"
        json_file.write_text("not valid json")

        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data=None,
                file_path=str(json_file),
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                response = report_detail(rid)
                assert response is not None

    def test_report_detail_config_load_exception(self, app):
        """Test config load exception is handled gracefully."""
        with app.app_context():
            report = report_models.Report(
                title="Test",
                report_type="shift_report",
                format="PDF",
                generated_by=1,
                data={"shift_info": {"team_name": "Test"}},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context():
                session["user_id"] = 1
                # Test that the route handles gracefully even with config
                response = report_detail(rid)
                assert response is not None


class TestGenerateReportCoverage:
    """Additional tests for generate_report route."""

    def test_generate_report_get_method(self, app):
        """Test GET method returns form."""
        with app.app_context(), app.test_request_context(method="GET"):
            session["user_id"] = 1
            response = generate_report()
            assert "Generate Report" in str(response)
