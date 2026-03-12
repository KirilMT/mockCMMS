"""Tests for planning app seeding log standardization."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

from apps.planning.src.services.db_seeding import seed_planning_data
from apps.planning.src.services.planning_models import Schedule
from src.services.db_utils import db


class TestPlanningSeeding:
    """Verify planning seeding behavior and log conventions."""

    def test_seed_planning_data_uses_prefixed_messages_when_skipping(self, app):
        """Planning app seeding logs should include the standard prefix."""
        mock_logger = MagicMock()

        with app.app_context():
            existing_schedule = Schedule(
                name="Existing Schedule",
                start_date=datetime(2026, 3, 12, 8, 0, 0),
                end_date=datetime(2026, 3, 12, 16, 0, 0),
            )
            db.session.add(existing_schedule)
            db.session.commit()

            seed_planning_data(mock_logger)

        mock_logger.log.assert_any_call(
            logging.INFO,
            "[SEED][PLANNING] Checking if Planning database needs to be populated.",
        )
        mock_logger.log.assert_any_call(
            logging.INFO,
            "[SEED][PLANNING] Planning database already contains data. "
            "Skipping main population.",
        )

    def test_seed_planning_data_logs_warning_when_dummy_data_missing(self, app):
        """Planning seeding warns with prefixed logs when dummy data is missing."""
        mock_logger = MagicMock()

        with app.app_context():
            Schedule.query.delete()
            db.session.commit()

            with (
                patch("apps.planning.src.services.db_seeding.init_db"),
                patch(
                    "apps.planning.src.services.db_seeding.get_db_connection"
                ) as mock_conn,
                patch(
                    "apps.planning.src.services.db_seeding.populate_planning_dummy_data"
                ),
                patch(
                    "apps.planning.src.services.db_seeding._load_dummy_data",
                    return_value=None,
                ),
            ):
                mock_conn.return_value.close = MagicMock()
                seed_planning_data(mock_logger)

        mock_logger.log.assert_any_call(
            logging.WARNING,
            "[SEED][PLANNING] No dummy data found for Planning App.",
        )

    def test_seed_planning_data_rolls_back_and_logs_error_on_commit_failure(self, app):
        """Planning seeding should rollback and log a prefixed commit failure."""
        mock_logger = MagicMock()
        schedules_data = {
            "schedules": [
                {
                    "name": "Commit Failure Schedule",
                    "start_date": "2026-03-12T08:00:00",
                    "end_date": "2026-03-12T16:00:00",
                    "maintenance_orders": [],
                }
            ]
        }

        with app.app_context():
            Schedule.query.delete()
            db.session.commit()

            with (
                patch("apps.planning.src.services.db_seeding.init_db"),
                patch(
                    "apps.planning.src.services.db_seeding.get_db_connection"
                ) as mock_conn,
                patch(
                    "apps.planning.src.services.db_seeding.populate_planning_dummy_data"
                ),
                patch(
                    "apps.planning.src.services.db_seeding._load_dummy_data",
                    return_value=schedules_data,
                ),
                patch(
                    "apps.planning.src.services.db_seeding.db.session.commit",
                    side_effect=Exception("commit failed"),
                ),
                patch(
                    "apps.planning.src.services.db_seeding.db.session.rollback"
                ) as mock_rollback,
            ):
                mock_conn.return_value.close = MagicMock()
                seed_planning_data(mock_logger)

        mock_rollback.assert_called_once()
        assert any(
            call.args[0] == logging.ERROR
            and "[SEED][PLANNING] Error seeding Planning App data: commit failed"
            in call.args[1]
            for call in mock_logger.log.call_args_list
        )
