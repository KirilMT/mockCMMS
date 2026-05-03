"""History-related tests for LockClient."""

from __future__ import annotations

from ._helpers import FakeResponse, load_lock_client_module, make_create_client

mod = load_lock_client_module()


def test_history_all_files(monkeypatch):
    """Test fetching lock history for all files."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    history_data = [
        {"file_path": "src/app.py", "developer_id": "user1", "action": "acquired"},
        {"file_path": "src/app.py", "developer_id": "user1", "action": "released"},
    ]
    response = FakeResponse(status=200, data=history_data)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    history = lc.history()
    assert isinstance(history, list)


def test_history_specific_file(monkeypatch):
    """Test fetching lock history for a specific file."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    history_data = [
        {"file_path": "src/app.py", "developer_id": "user1", "action": "acquired"}
    ]
    response = FakeResponse(status=200, data=history_data)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    history = lc.history(file_path="src/app.py", limit=10)
    assert isinstance(history, list)


def test_history_exception(monkeypatch):
    """Test history returns empty list when API raises exception."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    class ExplodingClient:
        def __init__(self, resp):
            self._resp = resp

        def table(self, *a, **k):
            raise RuntimeError("DB error")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: (lambda url, key: ExplodingClient(None))
    )

    lc = mod.LockClient(developer_id="test_user")
    history = lc.history()
    assert history == []


# RESTORED: test_history_fallback_exception
def test_history_fallback_exception(monkeypatch):
    """Test history partial exception."""
    monkeypatch.setattr(mod, "SUPABASE_SERVICE_ROLE_KEY", "admin_key")
    monkeypatch.setattr(mod, "_supabase_create_client", lambda url, key: None)

    class FakeQuery:
        def select(self, *args):
            return self

        def eq(self, *args):
            return self

        def is_(self, *args):
            return self

        def ilike(self, *args):
            return self

        def order(self, *args, **kwargs):
            return self

        def limit(self, *args):
            return self

        def execute(self):
            return None

    class FakeClient:
        def table(self, *args):
            return FakeQuery()

    client = getattr(mod, "LockClient")()
    client._client = FakeClient()
    monkeypatch.setattr(client, "_parse_response", lambda res: (False, [], None))

    # Pass an object that throws when string methods are called
    class Exploder:
        def replace(self, *args, **kwargs):
            raise Exception("boom")

    res = client.history(limit=5, file_path=Exploder())
    assert res == []
