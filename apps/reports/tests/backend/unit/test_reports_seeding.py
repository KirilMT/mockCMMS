from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.reports.src.services.seeding import seed_reports_data


class TestReportsSeeding:
    """Test seeding functionality for reports."""

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
        with patch("apps.reports.src.models.Report.query") as mock_query:
            yield mock_query

    def test_seed_reports_data_already_has_data(
        self, mock_report_query, mock_db_session
    ):
        """Test seeding skips if Report table has data."""
        mock_report_query.first.return_value = MagicMock()  # Data exists

        # Call function
        seed_reports_data()

        # Verify no add or commit
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    def test_seed_reports_data_no_file(self, mock_report_query, mock_db_session):
        """Test seeding handles missing file gracefully."""
        mock_report_query.first.return_value = None  # Empty table

        with patch(
            "apps.reports.src.services.seeding.os.path.exists", return_value=False
        ):
            seed_reports_data()

        mock_db_session.add.assert_not_called()

    def test_seed_reports_data_success(self, mock_report_query, mock_db_session):
        """Test successful seeding."""
        mock_report_query.first.return_value = None  # Empty table

        dummy_data = {
            "reports": [
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
            "apps.reports.src.services.seeding.os.path.exists", return_value=True
        ):
            with patch(
                "apps.reports.src.services.seeding.json.load", return_value=dummy_data
            ):
                with patch("builtins.open", mock_open(read_data="{}")):
                    seed_reports_data()

        # Verify add called
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    def test_seed_reports_data_exception_handling(
        self, mock_report_query, mock_db_session
    ):
        """Test seeding handles exceptions with rollback."""
        mock_report_query.first.return_value = None  # Empty table
        mock_db_session.commit.side_effect = Exception("DB error")

        with patch(
            "apps.reports.src.services.seeding.os.path.exists", return_value=True
        ):
            with patch(
                "apps.reports.src.services.seeding.json.load",
                return_value={
                    "reports": [
                        {"title": "T", "report_type": "t", "parameters": {}, "data": {}}
                    ]
                },
            ):
                with patch("builtins.open", mock_open()):
                    seed_reports_data()

        # Verify rollback was called
        mock_db_session.rollback.assert_called()

    def test_seed_reports_query_exception(self, mock_report_query, mock_db_session):
        """Test seeding handles query exception."""
        mock_report_query.first.side_effect = Exception("Query failed")

        seed_reports_data()

        mock_db_session.add.assert_not_called()


class TestLoadDummyData:
    """Test _load_dummy_data function."""

    def test_load_dummy_data_file_not_found(self):
        """Test _load_dummy_data returns None when file not found."""
        from apps.reports.src.services.seeding import _load_dummy_data

        with patch(
            "apps.reports.src.services.seeding.os.path.exists", return_value=False
        ):
            result = _load_dummy_data()
            assert result is None

    def test_load_dummy_data_success(self):
        """Test _load_dummy_data returns data when file exists."""
        from apps.reports.src.services.seeding import _load_dummy_data

        test_data = {"reports": [{"title": "Test"}]}
        with patch(
            "apps.reports.src.services.seeding.os.path.exists", return_value=True
        ):
            with patch("builtins.open", mock_open(read_data="{}")):
                with patch(
                    "apps.reports.src.services.seeding.json.load",
                    return_value=test_data,
                ):
                    result = _load_dummy_data()
                    assert result == test_data

    def test_load_dummy_data_exception(self):
        """Test _load_dummy_data returns None on exception."""
        from apps.reports.src.services.seeding import _load_dummy_data

        with patch(
            "apps.reports.src.services.seeding.os.path.exists", return_value=True
        ):
            with patch("builtins.open", side_effect=Exception("File error")):
                result = _load_dummy_data()
                assert result is None
