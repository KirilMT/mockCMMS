"""Tests for dashboard.py and data_processing.py (LEGACY modules)."""

from unittest.mock import MagicMock


class TestDataProcessing:
    """Tests for data_processing.py functions."""

    def test_normalize_string_basic(self):
        """Test normalize_string removes extra whitespace."""
        from apps.planning.src.services.data_processing import normalize_string

        result = normalize_string("  Hello   World  ")
        assert result == "hello world"

    def test_normalize_string_empty(self):
        """Test normalize_string handles empty input."""
        from apps.planning.src.services.data_processing import normalize_string

        assert normalize_string("") == ""
        assert normalize_string(None) == ""

    def test_normalize_string_german_chars(self):
        """Test normalize_string replaces German umlauts."""
        from apps.planning.src.services.data_processing import normalize_string

        result = normalize_string("Über Öl Äpfel ß")
        assert "u" in result
        assert "o" in result
        assert "a" in result

    def test_calculate_work_time(self):
        """Test calculate_work_time returns correct values."""
        from apps.planning.src.services.data_processing import calculate_work_time

        assert calculate_work_time("Monday") == 434
        assert calculate_work_time("Saturday") == 651
        assert calculate_work_time("Tuesday") == 434  # Default

    def test_is_valid_number(self):
        """Test is_valid_number validation."""
        from apps.planning.src.services.data_processing import is_valid_number

        assert is_valid_number(5) is True
        assert is_valid_number("10") is True
        assert is_valid_number(None) is False
        assert is_valid_number("") is False
        assert is_valid_number(-1) is False
        assert is_valid_number("3.5") is False  # Not integer

    def test_sanitize_data_basic(self, app):
        """Test sanitize_data processes rows correctly."""
        from apps.planning.src.services.data_processing import sanitize_data

        data = [
            {
                "id": "1",
                "scheduler_group_task": "Task A",
                "task_type": "PM",
                "priority": "A",
            }
        ]
        result = sanitize_data(data)
        assert len(result) == 1
        assert result[0]["task_type"] == "PM"

    def test_sanitize_data_missing_fields(self, app):
        """Test sanitize_data handles missing required fields."""
        from apps.planning.src.services.data_processing import sanitize_data

        data = [{"id": "1"}]  # Missing all required fields
        result = sanitize_data(data)
        assert len(result) == 1
        assert result[0]["priority"] == "C"  # Default
        assert result[0]["task_type"] == "REP"  # Default

    def test_validate_assignments_flat_input_valid(self):
        """Test validate_assignments_flat_input with valid data."""
        from apps.planning.src.services.data_processing import (
            validate_assignments_flat_input,
        )

        assignments = [
            {
                "technician": "Tech1",
                "task_name": "Task A",
                "start": 0,
                "duration": 30,
                "instance_id": "1_1",
            }
        ]
        result = validate_assignments_flat_input(assignments)
        assert len(result) == 1

    def test_validate_assignments_flat_input_invalid(self):
        """Test validate_assignments_flat_input rejects invalid data."""
        from apps.planning.src.services.data_processing import (
            validate_assignments_flat_input,
        )

        # Missing required field
        assignments = [{"technician": "Tech1"}]
        result = validate_assignments_flat_input(assignments)
        assert len(result) == 0

    def test_calculate_available_time(self):
        """Test calculate_available_time computes remaining time."""
        from apps.planning.src.services.data_processing import calculate_available_time

        techs = ["Tech1", "Tech2"]
        assignments = [{"technician": "Tech1", "duration": 60}]
        result = calculate_available_time(assignments, techs, 480)
        assert result["Tech1"] == 420
        assert result["Tech2"] == 480


class TestDashboard:
    """Tests for dashboard.py functions."""

    def test_prepare_dashboard_data_empty(self):
        """Test prepare_dashboard_data with empty inputs."""
        from apps.planning.src.services.dashboard import prepare_dashboard_data

        pm, rep, id_map = prepare_dashboard_data([], [], {}, {})
        assert pm == []
        assert rep == []
        assert id_map == {}

    def test_prepare_dashboard_data_with_tasks(self):
        """Test prepare_dashboard_data categorizes PM and REP tasks."""
        from apps.planning.src.services.dashboard import prepare_dashboard_data

        tasks = [
            {"id": "1", "task_type": "PM", "quantity": 1},
            {"id": "2", "task_type": "REP", "quantity": 1},
        ]
        pm, rep, id_map = prepare_dashboard_data(tasks, [], {}, {})
        assert len(pm) == 1
        assert len(rep) == 1
        assert pm[0]["display_id"] == 1
        assert rep[0]["display_id"] == 2

    def test_prepare_dashboard_data_color_generation(self):
        """Test prepare_dashboard_data generates color hex values."""
        from apps.planning.src.services.dashboard import prepare_dashboard_data

        tasks = [{"id": "1", "task_type": "PM", "quantity": 1}]
        pm, _, _ = prepare_dashboard_data(tasks, [], {}, {})
        assert pm[0]["color_hex"].startswith("#")
        assert len(pm[0]["color_hex"]) == 7

    def test_prepare_dashboard_data_with_assignments(self):
        """Test prepare_dashboard_data with assignments."""
        from apps.planning.src.services.dashboard import prepare_dashboard_data

        tasks = [{"id": "1", "task_type": "PM", "quantity": 2}]
        assignments = [
            {"instance_id": "1_1", "technician": "TechA"},
            {"instance_id": "1_2", "technician": "TechB"},
        ]
        pm, _, _ = prepare_dashboard_data(tasks, assignments, {}, {})
        assert len(pm) == 1
        assert "group_counter" in pm[0]

    def test_log_helper(self):
        """Test _log helper function."""
        from apps.planning.src.services.dashboard import _log

        mock_logger = MagicMock()
        _log(mock_logger, "info", "Test message")
        mock_logger.info.assert_called_once()

        _log(mock_logger, "error", "Error message")
        mock_logger.error.assert_called_once()

        # No logger - should print instead (no error)
        _log(None, "debug", "Debug message")
