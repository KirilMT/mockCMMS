import os

import pytest

from src.app import create_app  # noqa: E402
from src.services.db_utils import db as _db  # noqa: E402


@pytest.fixture
def app():
    os.environ["REPORTS_ENABLED"] = "true"
    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_BINDS": {
                "reports": "sqlite:///:memory:",
                "planning": "sqlite:///:memory:",
            },
            "REPORTS_ENABLED": True,
            "WTF_CSRF_ENABLED": False,
            "AUTO_SEED_DATABASE": False,
            # No SERVER_NAME to avoid cookie domain mismatch issues in test_client
        }
    )
    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    from src.services.db_utils import Role, User

    with app.app_context():
        r = Role.query.filter_by(name="Admin").first()
        if not r:
            r = Role(name="Admin")
            _db.session.add(r)
        if not User.query.filter_by(username="testuser").first():
            u = User(username="testuser", email="test@example.com")
            u.set_password("password")
            u.roles.append(r)
            _db.session.add(u)
        _db.session.commit()

        # Robustly get the ID of the test user
        u = User.query.filter_by(username="testuser").first()
        user_id = u.id
        username = u.username

    from datetime import datetime, timezone

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username
        # Set last_active to prevent session timeout
        sess["last_active"] = datetime.now(timezone.utc).timestamp()
    return client


@pytest.fixture
def auth_headers(client, app):
    """Fixture that sets up auth session and returns empty headers dict.

    The auth is done via session, not headers, but this pattern allows tests to use the
    same client for authenticated requests.
    """
    from src.services.db_utils import Role, User

    with app.app_context():
        r = Role.query.filter_by(name="Admin").first()
        if not r:
            r = Role(name="Admin")
            _db.session.add(r)
        if not User.query.filter_by(username="testuser").first():
            u = User(username="testuser", email="test@example.com")
            u.set_password("password")
            u.roles.append(r)
            _db.session.add(u)
        _db.session.commit()

        u = User.query.filter_by(username="testuser").first()
        user_id = u.id
        username = u.username

    from datetime import datetime, timezone

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username
        sess["last_active"] = datetime.now(timezone.utc).timestamp()

    # Return empty headers dict - auth is via session
    return {}


@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        yield _db.session


@pytest.fixture(scope="function", autouse=True)
def cleanup_report_artifacts():
    """Clean up generated report files after each test."""
    yield
    # Path to reports directory
    reports_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "instance", "reports")
    )
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if (
                filename.endswith(".csv")
                or filename.endswith(".pdf")
                or filename.endswith(".md")
            ):
                try:
                    os.remove(os.path.join(reports_dir, filename))
                except OSError:
                    pass
