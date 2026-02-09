import pytest

from src.app import create_app
from src.services.db_utils import Role, User, db


@pytest.fixture(scope="function")
def app():
    """Create and configure a Flask app instance for testing."""
    config_overrides = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_BINDS": {
            "planning": "sqlite:///:memory:",
            "reports": "sqlite:///:memory:",
        },
        "AUTO_SEED_DATABASE": False,
        # SERVER_NAME removed to test if default behavior works better
        # "SERVER_NAME": "localhost",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        },
        "DB_INITIALIZED": True,
    }

    test_app = create_app(config_overrides)

    with test_app.app_context():
        yield test_app
        db.session.remove()
        db.drop_all()
        for engine in db.engines.values():
            if hasattr(engine, "pool"):
                engine.pool.dispose()
            engine.dispose()
        if hasattr(db.engine, "pool"):
            db.engine.pool.dispose()
        db.engine.dispose()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def sample_role(app):
    """Create a sample role."""
    with app.app_context():
        role = Role.query.filter_by(name="Admin").first()
        if not role:
            role = Role(name="Admin")
            db.session.add(role)
            db.session.commit()
        return role


@pytest.fixture(scope="function")
def sample_user(app, sample_role):
    """Create a sample user."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        if not user:
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
            db.session.refresh(user)
        return user
