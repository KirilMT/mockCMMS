import sqlite3

import pytest

from apps.planning.src.services.planning_db_utils import LineConditionManager


@pytest.fixture
def db_connection():
    # Use in-memory database to follow project standards and avoid Windows file locking
    conn = sqlite3.connect(":memory:")
    # Use Row factory to match app behavior (access columns by name)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Create tables matching the schema in planning_db_utils.py
    cursor.execute(
        """
    CREATE TABLE line_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        color_code TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE task_line_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        condition_id INTEGER NOT NULL,
        FOREIGN KEY (condition_id) REFERENCES line_conditions(id),
        UNIQUE(task_id, condition_id)
    )
    """
    )

    conn.commit()
    yield conn
    conn.close()


def test_create_and_get_conditions(db_connection):
    manager = LineConditionManager(db_connection)

    # Test creating conditions
    cond1_id = manager.create_condition("Line Empty", "Line must be empty", "red")
    cond2_id = manager.create_condition("Power Off", "Power must be off", "blue")

    assert cond1_id is not None
    assert cond2_id is not None

    # Test getting all conditions
    conditions = manager.get_all_conditions()
    assert len(conditions) == 2

    names = [c["name"] for c in conditions]
    assert "Line Empty" in names
    assert "Power Off" in names


def test_assign_and_get_task_conditions(db_connection):
    manager = LineConditionManager(db_connection)

    # Create conditions
    c1 = manager.create_condition("C1", "D1", "red")
    c2 = manager.create_condition("C2", "D2", "blue")

    task_id = 101  # Use integer task ID

    # Test assigning conditions
    manager.assign_condition_to_task(task_id, c1)
    manager.assign_condition_to_task(task_id, c2)

    # Test getting task conditions
    task_conditions = manager.get_conditions_for_task(task_id)
    assert len(task_conditions) == 2

    condition_ids = [c["id"] for c in task_conditions]
    assert c1 in condition_ids
    assert c2 in condition_ids


def test_clear_task_conditions(db_connection):
    manager = LineConditionManager(db_connection)

    c1 = manager.create_condition("C1", "D1", "red")
    task_id = 101

    manager.assign_condition_to_task(task_id, c1)

    # Verify added
    assert len(manager.get_conditions_for_task(task_id)) == 1

    # Remove all
    manager.remove_conditions_from_task(task_id)

    # Verify removed
    assert len(manager.get_conditions_for_task(task_id)) == 0
