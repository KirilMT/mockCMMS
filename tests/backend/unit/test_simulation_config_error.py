import json
from unittest.mock import mock_open, patch

from src.services.simulation_service import DataSimulationService


def test_load_constants_os_error():
    """Test that _load_constants handles OSError (file not found/readable) correctly."""
    # Reset constants to force reload
    DataSimulationService._constants = None

    with patch("builtins.open", side_effect=OSError("Permission denied")):
        with patch("src.services.simulation_service.logger") as mock_logger:
            DataSimulationService._load_constants()

            # Verify fallback to empty dict
            assert DataSimulationService._constants == {}
            # Verify error logging
            mock_logger.error.assert_called_once()
            assert (
                "Error loading simulation config" in mock_logger.error.call_args[0][0]
            )


def test_load_constants_json_error():
    """Test that _load_constants handles JSONDecodeError correctly."""
    # Reset constants
    DataSimulationService._constants = None

    # Simulate a file existing but containing bad JSON
    with patch("builtins.open", mock_open(read_data="{invalid_json}")):
        with patch(
            "json.load", side_effect=json.JSONDecodeError("Expecting value", "doc", 0)
        ):
            with patch("src.services.simulation_service.logger") as mock_logger:
                DataSimulationService._load_constants()

                # Verify fallback
                assert DataSimulationService._constants == {}
                # Verify error logging
                mock_logger.error.assert_called_once()
