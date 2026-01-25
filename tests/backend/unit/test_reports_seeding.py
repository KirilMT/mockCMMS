import json
from unittest.mock import MagicMock, patch

import pytest

from apps.reports.src.models import Incident
from apps.reports.src.services.seeding import (
    _get_or_create_incident,
    _load_dummy_data,
    seed_reports_data,
)
from src.services.db_utils import db


class TestReportsSeeding:
    @pytest.fixture(autouse=True)
    def setup_app(self, app):
        with app.app_context():
            # Ensure DB is empty for seeding tests
            Incident.query.delete()
            db.session.commit()
            yield

    def test_load_dummy_data_not_found(self):
        with patch("os.path.exists", return_value=False):
            assert _load_dummy_data() is None

    def test_load_dummy_data_exception(self):
        with patch("builtins.open", side_effect=Exception("Open Error")):
            assert _load_dummy_data() is None

    def test_load_dummy_data_success(self, tmp_path):
        dummy_file = tmp_path / "dummy.json"
        data = {"incidents": [{"description": "Test"}]}
        dummy_file.write_text(json.dumps(data), encoding="utf-8")

        with patch(
            "apps.reports.src.services.seeding.os.path.join",
            return_value=str(dummy_file),
        ):
            with patch(
                "apps.reports.src.services.seeding.os.path.exists", return_value=True
            ):
                loaded = _load_dummy_data()
                assert loaded == data

    def test_get_or_create_incident_exists(self, db_session):
        data = {
            "incident_type": "Breakdown",
            "equipment_line": "Line 1",
            "description": "Test Incident",
            "severity": "High",
            "technician_name": "Tech 1",
            "days_ago": 1,
        }
        # First creation
        inc, created = _get_or_create_incident(data)
        assert created is True
        db.session.commit()

        # Second call
        inc2, created2 = _get_or_create_incident(data)
        assert created2 is False
        assert inc2.id == inc.id

    def test_seed_reports_data_already_has_data(self):
        with (
            patch("apps.reports.src.models.Incident.query") as mock_query,
            patch("apps.reports.src.services.seeding.logger") as mock_logger,
        ):
            mock_query.first.return_value = MagicMock()
            seed_reports_data()
            mock_logger.info.assert_any_call(
                "Reports database already contains data. Skipping seeding."
            )

    def test_seed_reports_data_no_file(self):
        with (
            patch("apps.reports.src.models.Incident.query") as mock_query,
            patch(
                "apps.reports.src.services.seeding._load_dummy_data", return_value=None
            ),
            patch("apps.reports.src.services.seeding.logger") as mock_logger,
        ):
            mock_query.first.return_value = None
            seed_reports_data()
            mock_logger.warning.assert_any_call(
                "No incident dummy data found for Reports App."
            )

    def test_seed_reports_data_exception(self):
        with (
            patch("apps.reports.src.models.Incident.query") as mock_query,
            patch(
                "apps.reports.src.services.seeding._load_dummy_data",
                side_effect=Exception("Seed Boom"),
            ),
            patch(
                "apps.reports.src.services.seeding.db.session.rollback"
            ) as mock_rollback,
        ):
            mock_query.first.return_value = None
            seed_reports_data()
            mock_rollback.assert_called()

    def test_seed_reports_data_full_success(self, db_session):
        data = {
            "incidents": [
                {
                    "incident_type": "PM",
                    "equipment_line": "L1",
                    "description": "D1",
                    "severity": "Low",
                    "technician_name": "T1",
                }
            ]
        }
        with (
            patch(
                "apps.reports.src.services.seeding._load_dummy_data", return_value=data
            ),
            patch("apps.reports.src.services.seeding.logger") as mock_logger,
        ):
            # No mock for Incident.query here, use real DB
            seed_reports_data()
            # Verify one incident was added
            inc = Incident.query.filter_by(description="D1").first()
            assert inc is not None

            # Find any log call that starts with "Successfully seeded 1 incidents"
            found = False
            for call in mock_logger.info.call_args_list:
                if call.args and str(call.args[0]).startswith(
                    "Successfully seeded 1 incidents"
                ):
                    found = True
                    break
            assert found, (
                "Expected seeding info log not found. "
                f"Logs: {mock_logger.info.call_args_list}"
            )
