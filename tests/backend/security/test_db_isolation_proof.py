import os

import pytest


class TestDBIsolationProof:
    """
    CRITICAL: This test suite proves that the test environment is correctly isolated
    from production data. It asserts that:
    1. The testing environment variable is active.
    2. The database URI points to a safe test database (memory or test file).
    3. No production database file (planning.db) is being created or used.
    """

    def test_environment_is_testing(self, app):
        """Verify that the app is running in testing mode."""
        assert app.config["TESTING"] is True
        assert os.environ.get("TESTING") == "1"

    def test_database_uri_is_test_db(self, app):
        """Verify that SQLALCHEMY_DATABASE_URI points to a safe test database."""
        uri = app.config["SQLALCHEMY_DATABASE_URI"]

        # In-memory SQLite is the safest possible isolation
        is_memory = ":memory:" in uri
        # File-based test DB is also acceptable if explicitly configured
        is_test_file = "planning_test.db" in uri

        if not (is_memory or is_test_file):
            pytest.fail(
                f"CRITICAL: Database URI '{uri}' does not look like a "
                "safe test database!"
            )

        # Explicitly forbid production DB usage
        assert "planning.db" not in uri
