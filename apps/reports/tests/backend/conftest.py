import os
import sys

import pytest

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
)

from src.app import create_app  # noqa: E402
from src.services.db_utils import db as _db  # noqa: E402


@pytest.fixture
def app():
    os.environ["REPORTS_ENABLED"] = "true"
    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "REPORTS_ENABLED": True,
            "WTF_CSRF_ENABLED": False,
            "AUTO_SEED_DATABASE": False,
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
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    return client


@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        yield _db.session
