import os
import json
import pytest
from unittest.mock import patch, mock_open
from apps.planning.src.services.config_manager import load_shift_config

def test_load_shift_config_default_when_no_files():
    # Test that default values are returned if no config files exist
    with patch('os.path.exists', return_value=False):
        config = load_shift_config()
        assert config['shift_durations']['shift_break'] == 30
        assert config['shift_durations']['weekend'] == 720

def test_load_shift_config_from_actual_file():
    # Test that values are loaded from config.json
    mock_config = {
        "shift_durations": {
            "shift_break": 45,
            "weekend": 600
        }
    }

    # We mock os.path.exists. It is called twice: for config.json and config.example.json
    # We want first call (config.json) to return True
    def side_effect(path):
        if 'config.json' in path and 'example' not in path:
            return True
        return False

    with patch('os.path.exists', side_effect=side_effect):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
            config = load_shift_config()
            assert config['shift_durations']['shift_break'] == 45
            assert config['shift_durations']['weekend'] == 600

def test_load_shift_config_fallback_to_example():
    # Test that values are loaded from config.example.json when config.json missing
    mock_config = {
        "shift_durations": {
            "shift_break": 40,
            "weekend": 700
        }
    }

    def side_effect(path):
        if 'config.json' in path and 'example' not in path:
            return False
        if 'config.example.json' in path:
            return True
        return False

    with patch('os.path.exists', side_effect=side_effect):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
            config = load_shift_config()
            assert config['shift_durations']['shift_break'] == 40
            assert config['shift_durations']['weekend'] == 700

def test_load_shift_config_partial_merge():
    # Test that partial config is merged with defaults
    mock_config = {
        "shift_durations": {
            "shift_break": 50
        }
    }

    with patch('os.path.exists', return_value=True): # config.json exists
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
            config = load_shift_config()
            assert config['shift_durations']['shift_break'] == 50
            assert config['shift_durations']['weekend'] == 720
