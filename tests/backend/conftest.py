"""Test configuration and fixtures for mockCMMS core application.

This module provides comprehensive pytest fixtures for testing the main mockCMMS
application, including Flask app setup, test client, database session management, and
sample data fixtures.
"""

import os
from datetime import datetime, timedelta, timezone

import pytest

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

        # 2. Close all checked-out connections
        if hasattr(db.engine, "pool"):
            db.engine.pool.dispose()

        # 3. Dispose of the engine (closes all connections)
        db.engine.dispose()

        # 4. Drop all tables (cleanup)
        db.drop_all()


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
        session = db.create_scoped_session(options={"bind": connection, "binds": {}})
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
def auth_client(client, sample_user, app):
    """Provide an authenticated test client.

    This fixture creates a test client that is already logged in with
    the sample_user credentials, allowing tests to bypass authentication.

    Args:
        client: Test client fixture
        sample_user: User fixture for authentication
        app: Flask application fixture

    Returns:
        FlaskClient: Authenticated test client
    """
    with app.app_context():
        # Simulate login by setting session
        with client.session_transaction() as session:
            session["user_id"] = sample_user.id
            session["username"] = sample_user.username

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
    The mockcmms.db is the production database and must NEVER be deleted by tests.

    Also runs explicit garbage collection to ensure all SQLite connections
    are properly closed before pytest checks for resource leaks.
    """
    yield

    # Force garbage collection to clean up any remaining SQLite connections
    # This prevents ResourceWarning about unclosed database connections
    import gc

    gc.collect()

    # Only clean up TEST database files - NEVER touch production mockcmms.db
    test_db = os.path.join("instance", "mockcmms_test.db")

    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except PermissionError:
            pass

    # Remove instance directory ONLY if it's empty
    # This ensures we never delete the directory if mockcmms.db exists
    if os.path.exists("instance"):
        try:
            # os.rmdir only succeeds if directory is empty - safe operation
            if not os.listdir("instance"):
                os.rmdir("instance")
        except (OSError, PermissionError):
            pass
