import logging
from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.reporting.src.services.db_seeding import seed_reporting_data


class TestReportingSeeding:
    """Test seeding functionality for reporting."""

    @pytest.fixture(autouse=True)
    def setup_app_context(self, app):
        with app.app_context():
            yield

    @pytest.fixture
    def mock_db_session(self):
        with patch("src.services.db_utils.db.session") as mock_session:
            yield mock_session

    @pytest.fixture
    def mock_report_query(self):
        with patch("apps.reporting.src.models.Report.query") as mock_query:
            yield mock_query

    def test_seed_reporting_data_already_has_data(
        self, mock_report_query, mock_db_session
    ):
        """Test seeding skips if Report table has data."""
        mock_report_query.first.return_value = MagicMock()  # Data exists
        mock_logger = MagicMock()

        # Call function
        seed_reporting_data(mock_logger)

        # Verify no add or commit
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
        mock_logger.log.assert_any_call(
            logging.INFO,
            "[SEED][REPORTING] Checking if Reporting database needs to be populated.",
        )
        mock_logger.log.assert_any_call(
            logging.INFO,
            "[SEED][REPORTING] Reporting database already contains data. "
            "Skipping main population.",
        )

    def test_seed_reporting_data_logs_prefixed_warning_when_file_missing(
        self, mock_report_query, mock_db_session
    ):
        """Missing reporting seed file should produce a prefixed warning."""
        mock_report_query.first.return_value = None
        mock_logger = MagicMock()

        with patch(
            "apps.reporting.src.services.db_seeding.os.path.exists", return_value=False
        ):
            seed_reporting_data(mock_logger)

        assert any(
            call.args[0] == logging.WARNING
            and "[SEED][REPORTING] Reporting dummy data not found:" in call.args[1]
            for call in mock_logger.log.call_args_list
        )

    def test_seed_reporting_data_no_file(self, mock_report_query, mock_db_session):
        """Test seeding handles missing file gracefully."""
        mock_report_query.first.return_value = None  # Empty table

        with patch(
            "apps.reporting.src.services.db_seeding.os.path.exists", return_value=False
        ):
            seed_reporting_data()

        mock_db_session.add.assert_not_called()

    def test_seed_reporting_data_success(self, mock_report_query, mock_db_session):
        """Test successful seeding."""
        mock_report_query.first.return_value = None  # Empty table

        dummy_data = {
            "reporting": [
                {
                    "title": "Shift Report - Seeded",
                    "report_type": "shift_report",
                    "format": "html",
                    "parameters": {"date": "2026-02-08", "shift": "Early"},
                    "data": {"key": "value"},
                }
            ]
        }

        with patch(
            "apps.reporting.src.services.db_seeding.os.path.exists", return_value=True
        ):
            with patch(
                "apps.reporting.src.services.db_seeding.json.load",
                return_value=dummy_data,
            ):
                with patch("builtins.open", mock_open(read_data="{}")):
                    seed_reporting_data()

        # Verify add called
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    def test_seed_reporting_data_exception_handling(
        self, mock_report_query, mock_db_session
    ):
        """Test seeding handles exceptions with rollback."""
        mock_report_query.first.return_value = None  # Empty table
        mock_db_session.commit.side_effect = Exception("DB error")

        with patch(
            "apps.reporting.src.services.db_seeding.os.path.exists", return_value=True
        ):
            with patch(
                "apps.reporting.src.services.db_seeding.json.load",
                return_value={
                    "reporting": [
                        {"title": "T", "report_type": "t", "parameters": {}, "data": {}}
                    ]
                },
            ):
                with patch("builtins.open", mock_open()):
                    seed_reporting_data()

        # Verify rollback was called
        mock_db_session.rollback.assert_called()

    def test_seed_reporting_query_exception(self, mock_report_query, mock_db_session):
        """Test seeding handles query exception."""
        mock_report_query.first.side_effect = Exception("Query failed")

        seed_reporting_data()

        mock_db_session.add.assert_not_called()


class TestReportingLoadDummyData:
    """Test _load_dummy_data function."""

    def test_load_dummy_data_file_not_found(self):
        """Test _load_dummy_data returns None when file not found."""
        from apps.reporting.src.services.db_seeding import _load_dummy_data

        with patch(
            "apps.reporting.src.services.db_seeding.os.path.exists", return_value=False
        ):
            result = _load_dummy_data()
            assert result is None

    def test_load_dummy_data_success(self):
        """Test _load_dummy_data returns data when file exists."""
        from apps.reporting.src.services.db_seeding import _load_dummy_data

        test_data = {"reporting": [{"title": "Test"}]}
        with patch(
            "apps.reporting.src.services.db_seeding.os.path.exists", return_value=True
        ):
            with patch("builtins.open", mock_open(read_data="{}")):
                with patch(
                    "apps.reporting.src.services.db_seeding.json.load",
                    return_value=test_data,
                ):
                    result = _load_dummy_data()
                    assert result == test_data

    def test_load_dummy_data_exception(self):
        """Test _load_dummy_data returns None on exception."""
        from apps.reporting.src.services.db_seeding import _load_dummy_data

        with patch(
            "apps.reporting.src.services.db_seeding.os.path.exists", return_value=True
        ):
            with patch("builtins.open", side_effect=Exception("File error")):
                result = _load_dummy_data()
                assert result is None
