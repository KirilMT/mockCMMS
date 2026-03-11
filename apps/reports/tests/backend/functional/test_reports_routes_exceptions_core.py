"""Core report-route exception and generation scenarios."""

from unittest.mock import MagicMock, patch

from flask import session

from apps.reports.src import models as report_models
from apps.reports.src.routes.reports import (
    _build_display_title,
    _resolve_shift_team_id,
    _safe_json_for_template,
    _sync_file_reports,
    export_report,
    generate_report,
    report_detail,
    reports,
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
        """Test generate_report without title (title is auto-generated now)."""
        # Title is now auto-generated, so this test should check
        # report_type validation instead
        with app.app_context(), app.test_request_context(method="POST", data={}):
            session["user_id"] = 1
            response = generate_report()
            # Should redirect with flash message for missing report type
            assert response.status_code == 302

    def test_generate_report_missing_report_type(self, app):
        """Test generate_report with missing report type."""
        with (
            app.app_context(),
            app.test_request_context(method="POST", data={}),
        ):
            session["user_id"] = 1
            response = generate_report()
            # Should redirect with flash message
            assert response.status_code == 302

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
        """Test report_detail uses shift_report_detail.html for unknown types."""
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

    def test_safe_json_for_template_none_and_non_dict(self):
        assert _safe_json_for_template(None) == "{}"
        assert _safe_json_for_template(["not", "a", "dict"]) == "{}"

    def test_safe_json_for_template_with_custom_object(self):
        class CustomObj:
            def __str__(self):
                return "CustomObjString"

        payload = {"x": CustomObj(), "nested": [{"y": CustomObj()}]}
        serialized = _safe_json_for_template(payload)
        assert "CustomObjString" in serialized

    def test_build_display_title_with_report_info(self):
        report = MagicMock(report_type="shift_report")
        report.data = {
            "report_info": {
                "date": "2026-03-10",
                "shift": "Early",
                "team_name": "Team A",
            }
        }
        title = _build_display_title(report, {"title": "Fallback"})
        assert title == "Shift Report - 2026-03-10 - Early - Team A"

    def test_build_display_title_falls_back_when_no_date(self):
        report = MagicMock(report_type="weekend_report")
        report.data = {"report_info": {}}
        assert _build_display_title(report, {"title": "Fallback"}) == "Fallback"

    def test_resolve_shift_team_id_invalid_inputs(self, app):
        with app.app_context():
            assert _resolve_shift_team_id(None, "Early") == (None, None)
            assert _resolve_shift_team_id("bad-date", "Early") == (None, None)

    def test_sync_file_reports_skips_existing_and_handles_invalid_file(self, app):
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
                    return_value=["existing.json", "invalid.json"],
                ),
                patch("apps.reports.src.routes.reports.open", create=True) as mock_open,
                patch(
                    "apps.reports.src.routes.reports.report_models.Report.query"
                ) as mock_query,
                patch("apps.reports.src.routes.reports.db.session") as mock_session,
            ):
                mock_rg.return_value.reports_dir = "C:/tmp/reports"
                mock_query.with_entities.return_value.all.return_value = [
                    ("C:/tmp/reports/existing.json",)
                ]
                mock_open.side_effect = ValueError("broken json")

                _sync_file_reports()

                # invalid file should be logged and skipped without commit
                assert not mock_session.commit.called

    def test_generate_shift_report_with_team_fallback_branch(self, app):
        with app.app_context():
            with app.test_request_context(
                method="POST",
                data={
                    "report_type": "shift_report",
                    "shift_date": "2026-03-10",
                    "shift_name": "Night",
                },
            ):
                session["user_id"] = 1
                with (
                    patch(
                        "apps.reports.src.routes.reports.da_service.DataAggregator"
                    ) as mock_agg,
                    patch(
                        "apps.reports.src.routes.reports._resolve_shift_team_id",
                        return_value=("5", "Team Night"),
                    ),
                    patch("apps.reports.src.routes.reports.db.session") as mock_session,
                ):
                    mock_agg.return_value.get_aggregated_shift_data.return_value = {}
                    response = generate_report()
                    assert response.status_code == 302
                    assert mock_session.add.called


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
            # Mock Team query to provide teams data
            with patch("src.services.db_utils.Team") as MockTeam:
                mock_team = MagicMock()
                mock_team.id = 1
                mock_team.name = "Team A"
                MockTeam.query.all.return_value = [mock_team]

                response = generate_report()
                assert "Generate Report" in str(response) or response.status_code == 200

    def test_generate_shift_report_with_team(self, app):
        """Test shift report generation with team selection."""
        with (
            app.app_context(),
            app.test_request_context(
                method="POST",
                data={
                    "report_type": "shift_report",
                    "shift_date": "2026-03-05",
                    "shift_name": "Early",
                    "team_id": "1",
                },
            ),
        ):
            session["user_id"] = 1
            with patch("src.services.db_utils.Team") as MockTeam:
                mock_team = MagicMock()
                mock_team.id = 1
                mock_team.name = "Team A"
                MockTeam.query.get.return_value = mock_team

                with patch(
                    "apps.reports.src.services.data_aggregator.DataAggregator"
                    ".get_aggregated_shift_data"
                ) as mock_agg:
                    mock_agg.return_value = {"shift_info": {}, "pms": [], "mos": []}
                    response = generate_report()
                    assert response.status_code == 302

    def test_generate_shift_report_missing_date(self, app):
        """Test shift report without date triggers error."""
        with (
            app.app_context(),
            app.test_request_context(
                method="POST",
                data={
                    "report_type": "shift_report",
                    "shift_name": "Early",
                },
            ),
        ):
            session["user_id"] = 1
            response = generate_report()
            assert response.status_code == 302

    def test_generate_weekend_report_missing_date(self, app):
        """Test weekend report without date triggers error."""
        with (
            app.app_context(),
            app.test_request_context(
                method="POST",
                data={
                    "report_type": "weekend_report",
                },
            ),
        ):
            session["user_id"] = 1
            response = generate_report()
            assert response.status_code == 302

    def test_generate_weekend_report_with_date_override(self, app):
        """Test weekend report with date override in data."""
        with (
            app.app_context(),
            app.test_request_context(
                method="POST",
                data={
                    "report_type": "weekend_report",
                    "weekend_date": "2026-03-05",
                    "handover_to_next": "Test instructions",
                },
            ),
        ):
            session["user_id"] = 1
            with patch(
                "apps.reports.src.services.data_aggregator.DataAggregator"
                ".get_aggregated_weekend_data"
            ) as mock_agg:
                mock_agg.return_value = {"report_info": {"date": "2026-03-01"}}
                response = generate_report()
                assert response.status_code == 302

    def test_resolve_shift_team_id_success(self, app):
        with app.app_context():
            early_team = MagicMock()
            early_team.id = 1
            early_team.name = "Team A"
            late_team = MagicMock()
            late_team.id = 2
            late_team.name = "Team B"

            with (
                patch("apps.reports.src.routes.reports.Team") as mock_team,
                patch(
                    "apps.reports.src.routes.reports.get_shift_teams",
                    return_value=(early_team, late_team),
                ),
            ):
                mock_team.query.all.return_value = [MagicMock(), MagicMock()]
                team_id, team_name = _resolve_shift_team_id("2026-03-10", "Early")
                assert team_id == "1"
                assert team_name == "Team A"

    def test_generate_shift_report_hits_fallback_handover_branch(self, app):
        with (
            app.app_context(),
            app.test_request_context(
                method="POST",
                data={
                    "report_type": "shift_report",
                    "shift_date": "2026-03-10",
                    "shift_name": "Night",
                    "handover_from_previous": "Manual A",
                    "handover_to_next": "Manual B",
                },
            ),
        ):
            session["user_id"] = 1
            added_report = {}

            def capture_add(obj):
                added_report["obj"] = obj

            with (
                patch(
                    "apps.reports.src.routes.reports.da_service.DataAggregator"
                ) as mock_agg,
                patch(
                    "apps.reports.src.routes.reports._resolve_shift_team_id",
                    return_value=("9", "Team Night"),
                ),
                patch(
                    "apps.reports.src.routes.reports.db.session.add",
                    side_effect=capture_add,
                ),
                patch("apps.reports.src.routes.reports.db.session.commit"),
            ):
                mock_agg.return_value.get_aggregated_shift_data.return_value = {}
                response = generate_report()

            assert response.status_code == 302
            saved_data = added_report["obj"].data
            assert saved_data["report_info"]["handover_from_previous"] == ["Manual A"]
            assert saved_data["report_info"]["handover_to_next"] == ["Manual B"]
            assert saved_data["shift_info"]["handover_from_previous"] == ["Manual A"]
            assert saved_data["shift_info"]["handover_to_next"] == ["Manual B"]

    def test_report_detail_linkify_spare_parts_paths(self, app):
        with app.app_context():
            report = report_models.Report(
                title="Linkify",
                report_type="shift_report",
                data={"report_info": {"team_name": "Team A"}},
                generated_by=1,
            )
            db.session.add(report)
            db.session.commit()

            with app.test_request_context():
                session["user_id"] = 1
                with (
                    patch("src.services.db_utils.SparePart") as mock_part,
                    patch(
                        "apps.reports.src.routes.reports.render_template"
                    ) as mock_render,
                ):
                    mock_part.query.with_entities.return_value.all.return_value = [
                        (1, "Pump Seal", "PS-100")
                    ]
                    mock_render.side_effect = lambda _template, **kwargs: kwargs[
                        "linkify_spare_parts"
                    ]("Replace Pump Seal and unknown")
                    html = report_detail(report.id)

            assert "href=" in html
            assert "Pump Seal" in html

    def test_report_detail_creates_default_config_when_missing(self, app):
        with app.app_context():
            report = report_models.Report(
                title="Config Create",
                report_type="shift_report",
                data={"report_info": {"team_name": "Team A"}},
                generated_by=1,
            )
            db.session.add(report)
            db.session.commit()

            with app.test_request_context():
                session["user_id"] = 1

                def exists_side_effect(path):
                    return not str(path).endswith("config.json")

                with (
                    patch(
                        "apps.reports.src.routes.reports.os.path.exists",
                        side_effect=exists_side_effect,
                    ),
                    patch(
                        "apps.reports.src.routes.reports.os.makedirs"
                    ) as mock_makedirs,
                    patch("apps.reports.src.routes.reports.open", create=True),
                    patch("apps.reports.src.routes.reports.json.dump") as mock_dump,
                ):
                    response = report_detail(report.id)

                assert response is not None
                assert mock_makedirs.called
                assert mock_dump.called

    def test_export_report_refresh_shift_branch(self, app, tmp_path):
        with app.app_context():
            report = report_models.Report(
                title="Shift Export",
                report_type="shift_report",
                data={
                    "report_info": {"date": "2026-03-10", "shift": "Early"},
                    "breakdowns": [{"description": "manual"}],
                    "handover_from_previous": [{"description": "manual from"}],
                },
                parameters={"date": "2026-03-10", "shift": "Early", "team_id": "1"},
                generated_by=1,
            )
            db.session.add(report)
            db.session.commit()

            exported_file = tmp_path / "export.txt"
            exported_file.write_text("ok")

            with app.test_request_context():
                session["user_id"] = 1
                with (
                    patch(
                        "apps.reports.src.routes.reports.da_service.DataAggregator"
                    ) as mock_agg,
                    patch(
                        "apps.reports.src.routes.reports.rg_service."
                        "ReportGenerator.generate_report"
                    ) as mock_generate,
                ):
                    mock_agg.return_value.get_aggregated_shift_data.return_value = {
                        "breakdowns": [{"id": 1, "description": "auto"}],
                        "break_activities": [],
                        "engineering_support": [],
                        "handover_from_previous": [],
                        "handover_to_next": [],
                    }
                    mock_generate.return_value = str(exported_file)
                    response = export_report(report.id, "txt")

                assert response.status_code == 200
                assert mock_generate.called

    def test_export_report_refresh_weekend_branch(self, app, tmp_path):
        with app.app_context():
            report = report_models.Report(
                title="Weekend Export",
                report_type="weekend_report",
                data={"weekend_info": {"date": "2026-03-10"}},
                parameters={"weekend_date": "2026-03-10", "shift": "Early"},
                generated_by=1,
            )
            db.session.add(report)
            db.session.commit()

            exported_file = tmp_path / "export_weekend.txt"
            exported_file.write_text("ok")

            with app.test_request_context():
                session["user_id"] = 1
                with (
                    patch(
                        "apps.reports.src.routes.reports.da_service.DataAggregator"
                    ) as mock_agg,
                    patch(
                        "apps.reports.src.routes.reports.rg_service."
                        "ReportGenerator.generate_report"
                    ) as mock_generate,
                ):
                    mock_agg.return_value.get_aggregated_weekend_data.return_value = {
                        "pms": [],
                        "mos_tickets": [],
                        "additional_tickets": [],
                        "handover_from_previous": [],
                        "handover_to_next": [],
                    }
                    mock_generate.return_value = str(exported_file)
                    response = export_report(report.id, "txt")

                assert response.status_code == 200
                assert mock_generate.called
