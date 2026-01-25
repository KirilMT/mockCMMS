"""Test configuration and fixtures for mockCMMS core application.

This module provides comprehensive pytest fixtures for testing the main mockCMMS
application, including Flask app setup, test client, database session management, and
sample data fixtures.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set TESTING globally to ensure apps/planning/src/config.py
# picks up the correct DB (memory)
os.environ["TESTING"] = "1"

from src.app import create_app  # noqa: E402
from src.services.db_utils import (  # noqa: E402
    Asset,
    MaintenanceOrder,
    Role,
    Skill,
    SparePart,
    Team,
    User,
    db,
)


@pytest.fixture(scope="function")
def app():
    """Create and configure a Flask app instance for testing.

    Uses an in-memory SQLite database that is created fresh for each test
    and destroyed after the test completes.

    Properly manages database connections to prevent ResourceWarning about
    unclosed database connections during garbage collection.

    Yields:
        Flask: Configured Flask application in testing mode.
    """
    config_overrides = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_BINDS": {
            "planning": "sqlite:///:memory:"  # In-memory for planning models
        },
        "AUTO_SEED_DATABASE": False,  # Prevent seeding in tests
        "SERVER_NAME": "localhost.localdomain",  # Required for url_for to work
        # Ensure connections are properly recycled
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        },
    }

    test_app = create_app(config_overrides)

    with test_app.app_context():
        # db.create_all() is now called within create_app
        yield test_app

        # Proper cleanup sequence to prevent ResourceWarnings:
        # 1. Remove all scoped sessions (returns connections to pool)
        db.session.remove()

        # 2. Drop all tables (cleanup)
        db.drop_all()

        # 3. Dispose of all engines (including binds)
        # to ensure SQLite connections are closed
        for engine in db.engines.values():
            if hasattr(engine, "pool"):
                engine.pool.dispose()
            engine.dispose()

        # 4. Dispose of the main engine
        if hasattr(db.engine, "pool"):
            db.engine.pool.dispose()
        db.engine.dispose()


@pytest.fixture(scope="function")
def client(app):
    """Provide a test client for making HTTP requests.

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client for the application
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Provide a test CLI runner for Click commands.

    Args:
        app: Flask application fixture

    Returns:
        FlaskCliRunner: CLI test runner
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a database session with automatic rollback.

    This fixture ensures that any database changes made during a test
    are rolled back after the test completes, maintaining test isolation.

    Args:
        app: Flask application fixture

    Yields:
        Session: SQLAlchemy database session
    """
    with app.app_context():
        # Start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()

        # Bind session to the connection
        session = db.create_scoped_session(options={"bind": connection})
        db.session = session

        yield session

        # Rollback transaction and close connection
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture(scope="function")
def sample_role(app):
    """Create a sample role for testing.

    Args:
        app: Flask application fixture

    Returns:
        Role: A test role with name 'Technician'
    """
    with app.app_context():
        role = Role(name="Technician", description="Maintenance technician role")
        db.session.add(role)
        db.session.commit()
        return role


@pytest.fixture(scope="function")
def sample_user(app, sample_role):
    """Create a sample user for testing.

    Args:
        app: Flask application fixture
        sample_role: Role fixture

    Returns:
        User: A test user with credentials (username: testuser, password: testpass123)
    """
    with app.app_context():
        user = User(
            username="testuser",
            email="testuser@example.com",
            is_active=True,
            availability_status="Available",
        )
        user.set_password("testpass123")
        user.roles.append(sample_role)
        db.session.add(user)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(user)
        return user


@pytest.fixture(scope="function")
def sample_admin_user(app):
    """Create a sample admin user for testing.

    Args:
        app: Flask application fixture

    Returns:
        User: A test admin user (username: admin, password: admin123)
    """
    with app.app_context():
        admin_role = Role(name="Admin", description="Administrator role")
        db.session.add(admin_role)

        admin = User(username="admin", email="admin@example.com", is_active=True)
        admin.set_password("admin123")
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.commit()

        db.session.refresh(admin)
        return admin


@pytest.fixture(scope="function")
def sample_team(app):
    """Create a sample team for testing.

    Args:
        app: Flask application fixture

    Returns:
        Team: A test team with shift information
    """
    with app.app_context():
        team = Team(name="Alpha Team", shift_type="Early", rotation_pattern="Pattern 1")
        db.session.add(team)
        db.session.commit()

        db.session.refresh(team)
        return team


@pytest.fixture(scope="function")
def sample_skill(app):
    """Create a sample skill for testing.

    Args:
        app: Flask application fixture

    Returns:
        Skill: A test skill (e.g., 'Welding')
    """
    with app.app_context():
        skill = Skill(name="Welding")
        db.session.add(skill)
        db.session.commit()

        db.session.refresh(skill)
        return skill


@pytest.fixture(scope="function")
def sample_asset(app):
    """Create a sample asset for testing.

    Args:
        app: Flask application fixture

    Returns:
        Asset: A test asset with typical attributes
    """
    with app.app_context():
        asset = Asset(
            asset_code="TEST-001",
            name="Test Robot Arm",
            description="Robotic welding arm for testing",
            asset_type="robot",
            cost_center="assembly",
            status="Operational",
        )
        db.session.add(asset)
        db.session.commit()

        db.session.refresh(asset)
        return asset


@pytest.fixture(scope="function")
def sample_spare_part(app):
    """Create a sample spare part for testing.

    Args:
        app: Flask application fixture

    Returns:
        SparePart: A test spare part with inventory details
    """
    with app.app_context():
        spare_part = SparePart(
            description="Hydraulic Pump Model X500",
            manufacturer="ACME Corp",
            manufacturer_part_id="PUMP-X500",
            stock_quantity=10,
            location="Warehouse A, Shelf 3",
            min_quantity=2,
        )
        db.session.add(spare_part)
        db.session.commit()

        db.session.refresh(spare_part)
        return spare_part


@pytest.fixture(scope="function")
def sample_mo(app, sample_asset, sample_user):
    """Create a sample maintenance order for testing.

    Args:
        app: Flask application fixture
        sample_asset: Asset fixture
        sample_user: User fixture

    Returns:
        MaintenanceOrder: A test maintenance order
    """
    with app.app_context():
        mo = MaintenanceOrder(
            asset_id=sample_asset.id,
            description="Routine maintenance check",
            order_type="PM",
            status="Open",
            priority="Medium",
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            estimated_completion_time=120,  # 2 hours
            labour_count=1,
            created_by=sample_user.id,
        )
        db.session.add(mo)
        db.session.commit()

        db.session.refresh(mo)
        return mo


@pytest.fixture(scope="function")
def auth_client(client, logged_in_user):
    """Provide an authenticated test client.

    This fixture creates a test client that is already logged in with
    the sample_user credentials, allowing tests to bypass authentication.

    Args:
        client: Test client fixture
        logged_in_user: User fixture (already logged in)

    Returns:
        FlaskClient: Authenticated test client
    """
    return client


@pytest.fixture(scope="function")
def multiple_assets(app):
    """Create multiple assets for testing list operations.

    Args:
        app: Flask application fixture

    Returns:
        list: List of 3 Asset objects
    """
    with app.app_context():
        assets = [
            Asset(
                asset_code="ROBOT-001",
                name="Welding Robot 1",
                asset_type="robot",
                cost_center="assembly",
                status="Operational",
            ),
            Asset(
                asset_code="ROBOT-002",
                name="Welding Robot 2",
                asset_type="robot",
                cost_center="assembly",
                status="Down",
            ),
            Asset(
                asset_code="PRESS-001",
                name="Hydraulic Press",
                asset_type="tooling",
                cost_center="biw",
                status="Operational",
            ),
        ]
        for asset in assets:
            db.session.add(asset)
        db.session.commit()

        for asset in assets:
            db.session.refresh(asset)
        return assets


@pytest.fixture(scope="function")
def multiple_mos(app, multiple_assets, sample_user):
    """Create multiple maintenance orders for testing list operations.

    Args:
        app: Flask application fixture
        multiple_assets: Multiple assets fixture
        sample_user: User fixture

    Returns:
        list: List of MaintenanceOrder objects
    """
    with app.app_context():
        mos = [
            MaintenanceOrder(
                asset_id=multiple_assets[0].id,
                description="Daily inspection",
                order_type="PM",
                status="Open",
                priority="Low",
                created_by=sample_user.id,
            ),
            MaintenanceOrder(
                asset_id=multiple_assets[1].id,
                description="Emergency repair",
                order_type="reactive",
                status="In Progress",
                priority="Critical",
                created_by=sample_user.id,
            ),
            MaintenanceOrder(
                asset_id=multiple_assets[2].id,
                description="Scheduled replacement",
                order_type="corrective",
                status="Completed",
                priority="Medium",
                created_by=sample_user.id,
            ),
        ]
        for mo in mos:
            db.session.add(mo)
        db.session.commit()

        for mo in mos:
            db.session.refresh(mo)
        return mos


@pytest.fixture(scope="function")
def logged_in_user(client, sample_user):
    """Create a logged-in user session for testing authenticated endpoints.

    Args:
        client: Flask test client
        sample_user: User fixture

    Returns:
        User: The logged-in user
    """
    with client.session_transaction() as sess:
        sess["user_id"] = sample_user.id
        sess["username"] = sample_user.username
    return sample_user


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Clean up test database files after entire test session completes.

    IMPORTANT: Only clean up TEST database files, never production data.
    The mockcmms.db and planning.db are production databases and must
    NEVER be deleted by tests.

    Also runs explicit garbage collection to ensure all SQLite connections
    are properly closed before pytest checks for resource leaks.
    """
    yield

    # Force garbage collection to clean up any remaining SQLite connections
    import gc

    gc.collect()

    # Define test database files to clean up (E2E and test DBs only)
    instance_dir = os.path.join(project_root, "instance")
    planning_instance_dir = os.path.join(project_root, "apps", "planning", "instance")
    reports_instance_dir = os.path.join(project_root, "apps", "reports", "instance")

    # Test DB files to clean (E2E and test DBs only)
    test_db_files = [
        os.path.join(instance_dir, "mockcmms_test.db"),
        os.path.join(instance_dir, "mockcmms_test.db-journal"),
        os.path.join(instance_dir, "mockcmms_e2e.db"),
        os.path.join(instance_dir, "mockcmms_e2e.db-journal"),
        # Explicitly target apps/planning/instance/planning_test.db
        os.path.join(planning_instance_dir, "planning_test.db"),
        os.path.join(planning_instance_dir, "planning_test.db-journal"),
        os.path.join(planning_instance_dir, "planning_e2e.db"),
        os.path.join(planning_instance_dir, "planning_e2e.db-journal"),
        os.path.join(planning_instance_dir, "testsDB.db"),
        os.path.join(planning_instance_dir, "testsDB.db-journal"),
    ]

    import time

    def force_delete_file(filepath):
        if not os.path.exists(filepath):
            return

        # Try up to 5 times
        for i in range(5):
            try:
                os.remove(filepath)
                return
            except (PermissionError, OSError):
                # Force GC and wait
                gc.collect()
                time.sleep(0.2 * (i + 1))

        # Final attempt warning
        if os.path.exists(filepath):
            print(f"WARNING: Failed to delete test artifact: {filepath}")

    # Clean up Files
    for db_file in test_db_files:
        force_delete_file(db_file)

    # Remove instance directories ONLY if they're empty
    # This ensures we never delete directories with production DBs
    # We do a recursive check to handle any subdirs (like apps/reports/instance/reports)
    for dir_path in [instance_dir, planning_instance_dir, reports_instance_dir]:
        if os.path.exists(dir_path):
            try:
                # Walk bottom-up to remove empty leaf directories
                for root, dirs, files in os.walk(dir_path, topdown=False):
                    for name in dirs:
                        full_path = os.path.join(root, name)
                        try:
                            if not os.listdir(full_path):
                                os.rmdir(full_path)
                        except (OSError, PermissionError):
                            pass

                # Finally try to remove the root dir itself if empty
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except (OSError, PermissionError):
                pass


@pytest.fixture(autouse=True)
def ensure_clean_models():
    """Ensure database models are not Mocks before each test.

    This fixture detects if key SQLAlchemy models have been replaced by Mocks (test
    pollution) and reloads the modules to restore the real classes.
    """
    import sys
    import unittest.mock

    # We use a try-import because if the module isn't loaded yet, it can't be polluted
    if "src.services.db_utils" not in sys.modules:
        return

    import src.services.db_utils as db_utils_module

    # Check key models for pollution from unittest.mock
    affected_models = ["SparePart", "MaintenanceOrder", "Asset", "User"]
    reload_needed = False

    for model_name in affected_models:
        current_attr = getattr(db_utils_module, model_name, None)
        if current_attr and (
            isinstance(current_attr, unittest.mock.Mock)
            or isinstance(current_attr, unittest.mock.MagicMock)
            or hasattr(current_attr, "assert_called")
        ):
            reload_needed = True
            break

    if reload_needed:
        try:
            db_instance = db_utils_module.db
            real_models = {}

            if hasattr(db_instance.Model, "registry"):
                for mapper in db_instance.Model.registry.mappers:
                    model = mapper.class_
                    real_models[model.__name__] = model
            elif hasattr(db_instance.Model, "_decl_class_registry"):
                real_models = db_instance.Model._decl_class_registry

            for model_name in affected_models:
                current_attr = getattr(db_utils_module, model_name, None)
                if current_attr and (
                    isinstance(current_attr, unittest.mock.Mock)
                    or isinstance(current_attr, unittest.mock.MagicMock)
                    or hasattr(current_attr, "assert_called")
                ):
                    if model_name in real_models:
                        setattr(db_utils_module, model_name, real_models[model_name])
        except Exception:
            pass
    yield
