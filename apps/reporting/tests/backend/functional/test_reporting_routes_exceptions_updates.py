"""Update-focused report-route exception scenarios."""

from unittest.mock import patch

from flask import session

from apps.reporting.src import models as report_models
from apps.reporting.src.routes.reporting import update_report_data
from src.services.db_utils import db


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
                from apps.reporting.src.routes.reporting import update_report_data

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
                from apps.reporting.src.routes.reporting import update_report_data

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
                from apps.reporting.src.routes.reporting import update_report_data

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
                from apps.reporting.src.routes.reporting import update_report_data

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
                from apps.reporting.src.routes.reporting import update_report_data

                res = update_report_data(rid)
                # Response is dict on success, tuple on error
                if isinstance(res, tuple):
                    assert res[1] == 200
                else:
                    assert res.get("success") is True


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


class TestUpdateReportBranchCoverage:
    def test_update_header_weekend_report_sets_top_level_shift(self, app):
        """Weekend-report header update must write shift/team_name at top level."""
        with app.app_context():
            report = report_models.Report(
                title="Weekend Header",
                report_type="weekend_report",
                generated_by=1,
                data={"weekend_info": {}},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "header",
                    "shift": "Night",
                    "team_name": "Weekend Team",
                },
            ):
                session["user_id"] = 1
                response = update_report_data(rid)

            payload = response[0] if isinstance(response, tuple) else response
            assert payload["success"] is True
            refreshed = report_models.Report.query.get(rid)
            assert refreshed.data["shift"] == "Night"
            assert refreshed.data["team_name"] == "Weekend Team"

    def test_update_handover_edit_preserves_existing_mo_id(self, app):
        """Editing a handover item must keep the existing mo_id from the DB record."""
        with app.app_context():
            report = report_models.Report(
                title="Handover Edit",
                report_type="shift_report",
                generated_by=1,
                data={
                    "report_info": {
                        "handover_from_previous": [
                            {"mo_id": 42, "title": "Old", "description": "Existing"}
                        ]
                    }
                },
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "handover_from",
                    "action": "edit",
                    "index": 0,
                    "asset": "AST-1",
                    "title": "New Title",
                    "description": "Updated",
                },
            ):
                session["user_id"] = 1
                response = update_report_data(rid)

            payload = response[0] if isinstance(response, tuple) else response
            assert payload["success"] is True
            refreshed = report_models.Report.query.get(rid)
            item = refreshed.data["report_info"]["handover_from_previous"][0]
            assert item["mo_id"] == 42
            assert item["title"] == "New Title"
            assert item["description"] == "Updated"

    def test_update_weekend_handover_syncs_instructions_on_edit(self, app):
        with app.app_context():
            report = report_models.Report(
                title="Weekend Handover Sync",
                report_type="weekend_report",
                generated_by=1,
                data={
                    "handover_instructions": [
                        {"title": "Old", "description": "Instruction"}
                    ]
                },
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "handover",
                    "action": "edit",
                    "index": 0,
                    "title": "Updated",
                    "description": "Keep watching",
                },
            ):
                session["user_id"] = 1
                update_report_data(rid)

            refreshed = report_models.Report.query.get(rid)
            assert refreshed.data["handover_instructions"][0]["title"] == "Updated"
            assert (
                refreshed.data["handover_to_next"][0]["description"] == "Keep watching"
            )

    def test_update_breakdown_edit_preserves_existing_mo_id(self, app):
        with app.app_context():
            report = report_models.Report(
                title="Breakdown Preserve",
                report_type="shift_report",
                generated_by=1,
                data={
                    "breakdowns": [
                        {"mo_id": 88, "description": "Old", "duration": "5m"}
                    ]
                },
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "breakdown",
                    "action": "edit",
                    "index": 0,
                    "description": "New desc",
                    "duration": "9m",
                },
            ):
                session["user_id"] = 1
                update_report_data(rid)

            refreshed = report_models.Report.query.get(rid)
            item = refreshed.data["breakdowns"][0]
            assert item["mo_id"] == 88
            assert item["duration"] == "9m"

    def test_update_pms_edit_and_delete(self, app):
        with app.app_context():
            report = report_models.Report(
                title="PM Section",
                report_type="weekend_report",
                generated_by=1,
                data={"pms": [{"asset": "PM-1", "description": "Old"}]},
            )
            db.session.add(report)
            db.session.commit()
            rid = report.id

            with app.test_request_context(
                method="POST",
                json={
                    "section": "pms",
                    "action": "edit",
                    "index": 0,
                    "asset": "PM-2",
                    "description": "Updated",
                },
            ):
                session["user_id"] = 1
                update_report_data(rid)

            with app.test_request_context(
                method="POST",
                json={"section": "pms", "action": "delete", "index": 0},
            ):
                session["user_id"] = 1
                update_report_data(rid)

            refreshed = report_models.Report.query.get(rid)
            assert refreshed.data["pms"] == []
