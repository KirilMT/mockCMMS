"""
Test configuration and fixtures for the Weekend Planning Project.
"""
import sys
import os

# Add project root to the Python path to resolve `src` imports correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest

# Import from main application (SQLAlchemy db instance)
from src.services.db_utils import db

# Import from workforceManager app
from apps.workforceManager.src.config import Config


class TestConfig(Config):
    """Test-specific configuration."""
    TESTING = True
    DEBUG_MODE = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing

    # Use in-memory database for tests
    @property
    def DATABASE_PATH(self):
        return ':memory:'


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    from flask import Flask

    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    # Initialize the db with the app
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def test_db(app):
    """Provide a clean database for each test."""
    with app.app_context():
        # Database is already initialized in app fixture
        yield
        # Could add cleanup here if needed


@pytest.fixture
def sample_technician_data():
    """Sample technician data for testing."""
    return {
        'name': 'Test Technician',
        'satellite_point_id': 1,
        'skills': {
            1: 3,  # technology_id: skill_level
            2: 4,
            3: 2
        }
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        'name': 'Test Task',
        'required_skills': [1, 2],  # technology_ids
        'quantity': 2,
        'duration': 120  # minutes
    }
