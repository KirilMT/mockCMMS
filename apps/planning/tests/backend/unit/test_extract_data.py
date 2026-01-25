"""Consolidated tests for extract_data.py."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from apps.planning.src.services.extract_data import (
    _extract_data_from_excel,
    extract_data,
    find_and_filter_data,
    get_current_day,
    get_current_shift,
    get_current_week,
)


@pytest.fixture
def mock_excel_df():
    """Create a standard mock Excel dataframe."""
    row0 = [""] * 8
    row0[2] = "Saturday CW-16"

    row1 = [
        "Scheduler Group /  Task",  # 0
        "Lines",  # 1
        "early",  # 2
        "Mitarbeiter pro Aufgabe",  # 3
        "Planned Worktime in Min",  # 4
        "Prio",  # 5
        "&",  # 6
        "Ticket oder MO ID",  # 7
    ]

    data = (
        [row0, row1]
        + [["ignore"] * 8] * 7
        + [
            ["Task 1", "Line 1", 1, "1", 60, "R", "PM", "12345"],
            ["Task 2", "Line 2", 2, "2", 120, "H", "Rep", "67890"],
        ]
    )
    return pd.DataFrame(data)


@pytest.fixture(autouse=True)
def mock_config():
    """Mock Config to avoid file system dependencies."""
    with patch("apps.planning.src.services.config.Config") as mock:
        mock_instance = mock.return_value
        mock_instance.get_ticket_url.return_value = "http://ticket/1234"
        mock_instance.get_maintenance_grid_url.return_value = "http://grid/1234"
        yield mock


class TestExtractData:
    """Tests for extraction logic."""

    @patch("pandas.read_excel")
    @patch("apps.planning.src.services.extract_data.get_current_week")
    @patch("apps.planning.src.services.extract_data.get_current_day")
    @patch("apps.planning.src.services.extract_data.get_current_shift")
    def test_extract_from_excel_success(
        self, mock_shift, mock_day, mock_week, mock_read, mock_excel_df
    ):
        mock_week.return_value = ("Summary KW16", None)
        mock_day.return_value = "Saturday"
        mock_shift.return_value = "early"
        mock_read.return_value = mock_excel_df

        mock_file = MagicMock()
        mock_file.filename = "test.xlsx"

        with (
            patch(
                "apps.planning.src.services.extract_data.get_current_week_number",
                return_value="16",
            ),
            patch(
                "apps.planning.src.services.extract_data.get_current_week",
                return_value=("Summary KW16", None),
            ),
        ):
            data, errors = _extract_data_from_excel(mock_file)

        assert len(data) == 2
        assert data[0]["scheduler_group_task"] == "Task 1"
        assert not errors

    def test_find_and_filter_data_mismatch(self):
        """Test error when shift column not found."""
        df = pd.DataFrame([["Wrong Header"], ["early"]])
        with pytest.raises(ValueError, match="No columns found"):
            find_and_filter_data(df, "Saturday", "late")

    @patch("apps.planning.src.services.extract_data._extract_data_from_excel")
    def test_extract_data_dispatcher(self, mock_excel):
        mock_excel.return_value = (["data"], [])
        with patch("apps.planning.src.services.extract_data.FlaskConfig") as mock_conf:
            mock_conf.DATA_SOURCE = "excel"
            result, errors = extract_data("file_obj")
            assert result == ["data"]
            assert errors == []
            mock_excel.assert_called_once_with("file_obj")

    @patch("requests.get")
    def test_fetch_from_api_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "task": "API Task"}]
        mock_get.return_value = mock_response

        from apps.planning.src.services.extract_data import _fetch_data_from_api

        data, errors = _fetch_data_from_api()
        assert data[0]["task"] == "API Task"
        assert not errors

    @patch("requests.get")
    def test_fetch_from_api_failure(self, mock_get):
        import requests  # type: ignore

        mock_get.side_effect = requests.exceptions.RequestException("API Down")

        from apps.planning.src.services.extract_data import _fetch_data_from_api

        data, errors = _fetch_data_from_api()
        assert not data
        assert "API Down" in errors[0]

    def test_dispatcher_api(self):
        with (
            patch("apps.planning.src.services.extract_data.FlaskConfig") as mock_conf,
            patch(
                "apps.planning.src.services.extract_data._fetch_data_from_api"
            ) as mock_api,
        ):
            mock_conf.DATA_SOURCE = "api"
            mock_api.return_value = (["api_data"], [])
            result, errors = extract_data()
            assert result == ["api_data"]

    def test_dispatcher_no_source(self):
        with patch("apps.planning.src.services.extract_data.FlaskConfig") as mock_conf:
            mock_conf.DATA_SOURCE = "none"
            result, errors = extract_data()
            assert not result
            assert "No data source" in errors[0]

    @patch("apps.planning.src.services.extract_data.FlaskConfig")
    def test_now_fixed_datetime(self, mock_conf):
        from apps.planning.src.services.extract_data import _now

        # Patch the config method that _now calls
        mock_conf.get_fixed_datetime.return_value = "fixed"
        assert _now() == "fixed"

    def test_context_helpers(self):
        """Test that context helpers return expected types."""
        assert isinstance(get_current_day(), str)
        assert get_current_shift() in ["early", "late", "night"]
        week_str, _ = get_current_week()
        assert "KW" in week_str or "CW" in week_str
