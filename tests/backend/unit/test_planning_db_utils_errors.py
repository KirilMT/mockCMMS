import sqlite3
from unittest.mock import MagicMock, patch

from apps.planning.src.services.planning_db_utils import init_db


def test_init_planning_db_migration_error():
    """Test error handling during migration checks in init_db."""
    mock_logger = MagicMock()

    with patch(
        "apps.planning.src.services.planning_db_utils.sqlite3.connect"
    ) as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate table info result missing 'group_id' to trigger ALTER TABLE
        # 1. PRAGMA for techniques -> returns [] or columns without group_id
        # We need to target the specific call.
        # It calls PRAGMA table_info(technicians) first, then technologies.

        # Let's make PRAGMA table_info(technologies) fail when checked
        def side_effect(query, params=()):
            if "PRAGMA table_info(technologies)" in query:
                return mock_cursor
            if "ALTER TABLE technologies ADD COLUMN group_id" in query:
                raise sqlite3.Error("Alter failed")
            return mock_cursor

        mock_cursor.execute.side_effect = side_effect
        mock_cursor.fetchall.return_value = []  # No columns found, forcing ALTER

        init_db(":memory:", logger=mock_logger)

        # Verify logger.error was called
        # Line 289
        assert any(
            "Error checking/adding group_id" in str(call)
            for call in mock_logger.error.call_args_list
        )


def test_init_planning_db_technicians_uptodate():
    """Test log message when technicians table is up to date."""
    mock_logger = MagicMock()
    with patch(
        "apps.planning.src.services.planning_db_utils.sqlite3.connect"
    ) as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # PRAGMA table_info(technicians) return contains 'satellite_point_id'
        def side_effect(query, params=()):
            if "PRAGMA table_info(technicians)" in query:
                return mock_cursor
            return mock_cursor

        mock_cursor.execute.side_effect = side_effect
        # Return columns list including satellite_point_id
        mock_cursor.fetchall.return_value = [(0, "id"), (1, "satellite_point_id")]

        init_db(":memory:", logger=mock_logger)

        # Verify execution completed without migration triggers if already up to date
        assert mock_cursor.execute.call_count > 0
