import os
from datetime import datetime, timezone

import pytest

from apps.planning.src.services.planning_db_utils import init_db  # noqa: E402
from src.app import create_app  # noqa: E402
from src.services.db_utils import db as _db  # noqa: E402


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("PLANNING_ENABLED", "true")
    monkeypatch.setenv("REPORTS_ENABLED", "true")
    planning_db_path = str(tmp_path / "planning_test.db")
    output_path = str(tmp_path / "output")
    os.makedirs(output_path, exist_ok=True)

    test_app = create_app(
        config_overrides={
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_BINDS": {"planning": f"sqlite:///{planning_db_path}"},
            "DATABASE_PATH": planning_db_path,
            "OUTPUT_FOLDER": output_path,
            "AUTO_SEED_DATABASE": False,
            "SERVER_NAME": "localhost.localdomain",
        }
    )

    with test_app.app_context():
        _db.create_all()
        try:
            init_db(planning_db_path, test_app.logger, debug_use_test_db=True)
        except Exception:
            pass
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
        u = User.query.filter_by(username="testuser").first()
        if not u:
            u = User(username="testuser", email="test@example.com")
            u.set_password("password")
            u.roles.append(r)
            _db.session.add(u)
        _db.session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "testuser"
        sess["last_active"] = datetime.now(timezone.utc).timestamp()
        sess["_fresh"] = True
    return client


@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        yield _db.session
