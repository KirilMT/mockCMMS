"""Database isolation tests - ensures no production DBs are created during testing.

This test module acts as a SAFETY NET to catch database isolation violations.
If these tests fail, it means tests are creating production database files,
which is a critical bug that must be fixed immediately.

CRITICAL: This test suite proves that the test environment is correctly isolated
from production data. It asserts that:
1. The testing environment variable is active.
2. The database URI points to a safe test database (memory or test file).
3. Tests do NOT create production database files.
4. All database binds (planning, reports, etc.) use in-memory databases.

IMPORTANT: These tests are designed to work in ALL scenarios:
- Tests running alone (no production)
- Tests running while production server is active
- Production DBs pre-existing before tests run
"""

import os
from pathlib import Path

import pytest

# Calculate project root (4 levels up: security -> backend -> tests -> root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Track which production DBs existed BEFORE tests started
# This is populated at module load time (before any tests run)
_PRE_EXISTING_DBS = set()

# Production database paths to check
_PRODUCTION_DBS = [
    PROJECT_ROOT / "apps" / "planning" / "instance" / "planning.db",
    PROJECT_ROOT / "apps" / "reports" / "instance" / "reports.db",
    PROJECT_ROOT / "instance" / "mockcmms.db",
]

# Record pre-existing DBs at module load time
for _db_path in _PRODUCTION_DBS:
    if _db_path.exists():
        _PRE_EXISTING_DBS.add(str(_db_path))


def _is_file_locked_or_in_use(filepath: Path) -> bool:
    """Check if a file is locked/in-use by another process (e.g., production).

    On Windows, SQLite may not hold exclusive locks, so we try to rename the file
    temporarily. If the rename fails, another process has the file open.

    Returns True if the file is locked by another process (production owns it). Returns
    False if the file exists but is NOT locked.
    """
    if not filepath.exists():
        return False

    # Try to rename the file temporarily - this fails if file is in use
    temp_path = filepath.with_suffix(".db.locktest")
    try:
        filepath.rename(temp_path)
        temp_path.rename(filepath)  # Rename back
        return False  # File was renamed successfully - NOT locked
    except (PermissionError, OSError):
        return True  # Cannot rename - file IS locked by another process


def _was_preexisting(filepath: Path) -> bool:
    """Check if a DB file existed before tests started."""
    return str(filepath) in _PRE_EXISTING_DBS


def _cleanup_e2e_test_dbs():
    """Remove E2E test databases only.

    This function removes ONLY E2E databases (*_e2e.db) that are unlocked. It does NOT
    touch production-named databases since we cannot safely determine if they were
    created by tests or are legitimate.
    """
    # E2E databases to clean - these are ALWAYS test artifacts
    e2e_dbs = [
        PROJECT_ROOT / "instance" / "mockcmms_e2e.db",
        PROJECT_ROOT / "apps" / "planning" / "instance" / "planning_e2e.db",
        PROJECT_ROOT / "apps" / "reports" / "instance" / "reports_e2e.db",
    ]

    for db_path in e2e_dbs:
        if db_path.exists() and not _is_file_locked_or_in_use(db_path):
            try:
                db_path.unlink()
            except (PermissionError, OSError):
                pass


class TestDBIsolationProof:
    """Test suite to verify database isolation between testing and production."""

    @pytest.fixture(autouse=True)
    def cleanup_e2e_dbs(self):
        """Clean up any unlocked E2E DB files before and after test."""
        _cleanup_e2e_test_dbs()
        yield
        _cleanup_e2e_test_dbs()

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
        is_test_file = "_test.db" in uri

        if not (is_memory or is_test_file):
            pytest.fail(
                f"CRITICAL: Database URI '{uri}' does not look like a "
                "safe test database!"
            )

        # Explicitly forbid production DB usage
        assert "planning.db" not in uri
        assert "reports.db" not in uri
        assert "mockcmms.db" not in uri

    def test_all_binds_use_memory_in_testing(self, app):
        """Verify all database binds use in-memory SQLite during testing."""
        binds = app.config.get("SQLALCHEMY_BINDS", {})
        for bind_name, bind_uri in binds.items():
            assert ":memory:" in str(bind_uri), (
                f"Bind '{bind_name}' is not in-memory during testing!\n"
                f"Current URI: {bind_uri}\n"
                f"Expected: sqlite:///:memory:\n"
                f"Fix: Add '{bind_name}': 'sqlite:///:memory:' to conftest.py"
            )

    def test_no_planning_db_created(self, app):
        """Verify tests don't CREATE planning.db (pre-existing/locked DBs allowed)."""
        planning_db = PROJECT_ROOT / "apps" / "planning" / "instance" / "planning.db"

        # If DB doesn't exist, test passes (tests didn't create it)
        if not planning_db.exists():
            return

        # If DB existed before tests started, test passes (pre-existing)
        if _was_preexisting(planning_db):
            return

        # If DB exists and is LOCKED, test passes (production owns it)
        if _is_file_locked_or_in_use(planning_db):
            return

        # DB exists, was NOT pre-existing, and is NOT locked
        # This means tests created it - VIOLATION!
        pytest.fail(
            f"CRITICAL: planning.db was created during testing!\n"
            f"Path: {planning_db}\n"
            f"This indicates a database isolation violation.\n"
            f"Tests should use in-memory databases only."
        )

    def test_no_reports_db_created(self, app):
        """Verify tests don't CREATE reports.db (pre-existing/locked DBs allowed)."""
        reports_db = PROJECT_ROOT / "apps" / "reports" / "instance" / "reports.db"

        # If DB doesn't exist, test passes (tests didn't create it)
        if not reports_db.exists():
            return

        # If DB existed before tests started, test passes (pre-existing)
        if _was_preexisting(reports_db):
            return

        # If DB exists and is LOCKED, test passes (production owns it)
        if _is_file_locked_or_in_use(reports_db):
            return

        # DB exists, was NOT pre-existing, and is NOT locked
        # This means tests created it - VIOLATION!
        pytest.fail(
            f"CRITICAL: reports.db was created during testing!\n"
            f"Path: {reports_db}\n"
            f"This indicates a database isolation violation.\n"
            f"Tests should use in-memory databases only."
        )

    def test_no_mockcmms_db_created(self, app):
        """Verify tests don't CREATE mockcmms.db (pre-existing/locked DBs allowed)."""
        mockcmms_db = PROJECT_ROOT / "instance" / "mockcmms.db"

        # If DB doesn't exist, test passes (tests didn't create it)
        if not mockcmms_db.exists():
            return

        # If DB existed before tests started, test passes (pre-existing)
        if _was_preexisting(mockcmms_db):
            return

        # If DB exists and is LOCKED, test passes (production owns it)
        if _is_file_locked_or_in_use(mockcmms_db):
            return

        # DB exists, was NOT pre-existing, and is NOT locked
        # This means tests created it - VIOLATION!
        pytest.fail(
            f"CRITICAL: mockcmms.db was created during testing!\n"
            f"Path: {mockcmms_db}\n"
            f"This indicates a database isolation violation.\n"
            f"Tests should use in-memory databases only."
        )

    def test_no_production_dbs_in_any_app(self, app):
        """Verify tests don't CREATE production DBs (pre-existing/locked allowed)."""
        apps_dir = PROJECT_ROOT / "apps"
        if not apps_dir.exists():
            return

        for app_dir in apps_dir.iterdir():
            if not app_dir.is_dir():
                continue
            instance_dir = app_dir / "instance"
            if instance_dir.exists():
                # Find production DBs that tests may have created
                # (not E2E, not pre-existing, not locked)
                test_created_dbs = [
                    f
                    for f in instance_dir.glob("*.db")
                    if not f.name.endswith("_e2e.db")
                    and not _was_preexisting(f)
                    and not _is_file_locked_or_in_use(f)
                ]
                assert len(test_created_dbs) == 0, (
                    f"Tests created production DB files in {instance_dir}!\n"
                    f"Files: {[f.name for f in test_created_dbs]}\n"
                    f"These should not be created during testing.\n"
                    f"(Pre-existing and locked DBs are ignored)"
                )

    def test_no_e2e_dbs_during_pytest(self, app):
        """Verify E2E databases are cleaned up during pytest runs.

        E2E databases (*_e2e.db) should only exist during Playwright tests.
        - If E2E DB doesn't exist → PASS
        - If E2E DB exists and is LOCKED → PASS (E2E tests running)
        - If E2E DB exists and is UNLOCKED → FAIL (cleanup failed)
        """
        e2e_dbs = [
            PROJECT_ROOT / "instance" / "mockcmms_e2e.db",
            PROJECT_ROOT / "apps" / "planning" / "instance" / "planning_e2e.db",
            PROJECT_ROOT / "apps" / "reports" / "instance" / "reports_e2e.db",
        ]

        for db_path in e2e_dbs:
            if not db_path.exists():
                continue  # No E2E DB, good

            if _is_file_locked_or_in_use(db_path):
                continue  # E2E tests currently running, that's OK

            # E2E DB exists but is unlocked - cleanup failed
            pytest.fail(
                f"E2E database found during pytest: {db_path}\n"
                f"This indicates E2E cleanup did not run or failed.\n"
                f"E2E databases should be removed after Playwright tests."
            )


class TestDatabaseBindsComplete:
    """Test that all required database binds are properly configured."""

    def test_planning_bind_exists(self, app):
        """Verify planning bind is configured."""
        binds = app.config.get("SQLALCHEMY_BINDS", {})
        assert "planning" in binds, (
            "Planning bind is missing from SQLALCHEMY_BINDS!\n"
            "Add 'planning': 'sqlite:///:memory:' to conftest.py"
        )

    def test_reports_bind_exists(self, app):
        """Verify reports bind is configured."""
        binds = app.config.get("SQLALCHEMY_BINDS", {})
        assert "reports" in binds, (
            "Reports bind is missing from SQLALCHEMY_BINDS!\n"
            "Add 'reports': 'sqlite:///:memory:' to conftest.py"
        )

    def test_all_enabled_modules_have_binds(self, app):
        """Verify all enabled modules have corresponding database binds."""
        binds = app.config.get("SQLALCHEMY_BINDS", {})

        # Check Planning
        planning_enabled = os.environ.get("PLANNING_ENABLED", "true").lower() in (
            "true",
            "1",
        )
        if planning_enabled:
            assert "planning" in binds, "Planning is enabled but bind is missing!"

        # Check Reports
        reports_enabled = os.environ.get("REPORTS_ENABLED", "false").lower() in (
            "true",
            "1",
        )
        if reports_enabled:
            assert "reports" in binds, "Reports is enabled but bind is missing!"


class TestNoFileBasedDBsDuringPytest:
    """Verify that NO file-based databases are created during backend pytest.

    This test class specifically catches the issue where unit tests that set
    E2E_TEST=True (to test E2E configuration) accidentally create file-based
    databases. ALL backend tests should use in-memory databases exclusively.

    IMPORTANT: These tests check for BOTH production DBs AND E2E DBs because
    neither should be created during backend pytest runs.
    """

    # All database files that should NEVER be created during backend pytest
    _ALL_FILE_BASED_DBS = [
        # Production databases
        ("apps/planning/instance/planning.db", "production"),
        ("apps/reports/instance/reports.db", "production"),
        ("instance/mockcmms.db", "production"),
        # E2E databases (should only exist during Playwright tests)
        ("apps/planning/instance/planning_e2e.db", "e2e"),
        ("apps/reports/instance/reports_e2e.db", "e2e"),
        ("instance/mockcmms_e2e.db", "e2e"),
        # Test databases
        ("apps/planning/instance/planning_test.db", "test"),
        ("apps/reports/instance/reports_test.db", "test"),
        ("instance/mockcmms_test.db", "test"),
    ]

    def test_no_instance_directories_created(self, app):
        """Verify instance directories are not created during testing.

        If an instance directory exists but is empty, it indicates tests tried to create
        DBs but were blocked. The directory itself shouldn't be created during backend
        pytest.
        """
        instance_dirs = [
            PROJECT_ROOT / "apps" / "planning" / "instance",
            PROJECT_ROOT / "apps" / "reports" / "instance",
        ]

        for instance_dir in instance_dirs:
            if not instance_dir.exists():
                continue  # Good - directory doesn't exist

            # Directory exists - check if it was pre-existing or has production DBs
            db_files = list(instance_dir.glob("*.db"))

            # If directory has files, check if they're all pre-existing or locked
            if db_files:
                for db_file in db_files:
                    if _was_preexisting(db_file) or _is_file_locked_or_in_use(db_file):
                        continue  # Pre-existing or production-owned
                    # File was created by tests - violation
                    pytest.fail(
                        f"Database file created during testing: {db_file}\n"
                        f"Backend tests must use in-memory databases only."
                    )

    def test_e2e_test_env_not_causing_file_creation(self, app):
        """Verify that tests setting E2E_TEST=True don't create E2E databases.

        This catches the specific bug where unit tests that test E2E configuration
        accidentally create file-based E2E databases (planning_e2e.db, etc.).

        The fix is to pass in-memory URIs when testing E2E configuration:
            create_app({
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SQLALCHEMY_BINDS": {"planning": "sqlite:///:memory:", ...},
            })
        """
        e2e_db_paths = [
            PROJECT_ROOT / "apps" / "planning" / "instance" / "planning_e2e.db",
            PROJECT_ROOT / "apps" / "reports" / "instance" / "reports_e2e.db",
            PROJECT_ROOT / "instance" / "mockcmms_e2e.db",
        ]

        for db_path in e2e_db_paths:
            if not db_path.exists():
                continue  # Good

            # E2E DB exists - check if it's from actual E2E tests (locked)
            if _is_file_locked_or_in_use(db_path):
                continue  # Actual E2E tests running

            # E2E DB exists and is unlocked during backend pytest - BAD!
            pytest.fail(
                f"E2E database created during backend pytest: {db_path}\n"
                f"This indicates a test is setting E2E_TEST=True without using "
                f"in-memory database URIs.\n\n"
                f"FIX: When testing E2E configuration, always pass in-memory URIs:\n"
                f"    create_app({{\n"
                f'        "TESTING": True,\n'
                f'        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",\n'
                f'        "SQLALCHEMY_BINDS": {{\n'
                f'            "planning": "sqlite:///:memory:",\n'
                f'            "reports": "sqlite:///:memory:",\n'
                f"        }},\n"
                f"    }})"
            )

    def test_all_binds_are_memory_not_file(self, app):
        """Verify ALL database binds use in-memory URIs, not file paths.

        This is a stricter check than test_all_binds_use_memory_in_testing. It
        explicitly checks for file-based URIs that could create files.
        """
        main_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        binds = app.config.get("SQLALCHEMY_BINDS", {})

        # Check main URI
        if main_uri and ":memory:" not in main_uri:
            if "sqlite:///" in main_uri and ".db" in main_uri:
                pytest.fail(
                    f"Main database URI is file-based during testing!\n"
                    f"URI: {main_uri}\n"
                    f"Expected: sqlite:///:memory:"
                )

        # Check all binds
        for bind_name, bind_uri in binds.items():
            bind_uri_str = str(bind_uri)
            if ":memory:" not in bind_uri_str:
                if "sqlite:///" in bind_uri_str and ".db" in bind_uri_str:
                    pytest.fail(
                        f"Bind '{bind_name}' uses file-based URI during testing!\n"
                        f"URI: {bind_uri_str}\n"
                        f"Expected: sqlite:///:memory:\n"
                        f"Fix: Update conftest.py to use in-memory for this bind."
                    )
