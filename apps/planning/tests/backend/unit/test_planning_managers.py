"""Tests for TechnicianGroupManager, LineConditionManager, and populate_dummy_data with
line conditions.

Covers uncovered lines in planning_db_utils.py:
- TechnicianGroupManager full CRUD (lines 998-1055)
- LineConditionManager full CRUD (lines 1058-1151)
- populate_dummy_data with line conditions (lines 163-165)
"""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.planning.src.services.planning_db_utils import (
    LineConditionManager,
    TaskManager,
    TechnicianGroupManager,
    get_db_connection,
    init_db,
    populate_dummy_data,
    update_line,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture for a temporary sqlite database."""
    return str(tmp_path / "test_managers.db")


@pytest.fixture
def db_conn(temp_db):
    """Fixture for a database connection with initialized schema."""
    init_db(temp_db, logger=None)
    conn = get_db_connection(temp_db)
    yield conn
    conn.close()


class TestTechnicianGroupManagerCrud:
    """Tests for TechnicianGroupManager CRUD operations."""

    def test_get_or_create_new_group(self, db_conn):
        """Test creating a new technician group."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("Alpha Team")
        assert gid is not None
        assert isinstance(gid, int)

    def test_get_or_create_existing_group(self, db_conn):
        """Test getting an existing group returns same ID."""
        mgr = TechnicianGroupManager(db_conn)
        gid1 = mgr.get_or_create_group("Beta Team")
        gid2 = mgr.get_or_create_group("Beta Team")
        assert gid1 == gid2

    def test_get_all_groups(self, db_conn):
        """Test listing all technician groups."""
        mgr = TechnicianGroupManager(db_conn)
        mgr.get_or_create_group("Group A")
        mgr.get_or_create_group("Group B")
        groups = mgr.get_all_groups()
        assert len(groups) >= 2
        assert all("id" in g and "name" in g for g in groups)

    def test_update_group(self, db_conn):
        """Test updating a group name."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("OldName")
        result = mgr.update_group(gid, "NewName")
        assert result is True
        groups = mgr.get_all_groups()
        assert any(g["name"] == "NewName" for g in groups)

    def test_update_nonexistent_group(self, db_conn):
        """Test updating a group that doesn't exist."""
        mgr = TechnicianGroupManager(db_conn)
        result = mgr.update_group(9999, "Ghost")
        assert result is False

    def test_delete_group(self, db_conn):
        """Test deleting a technician group."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("ToDelete")
        result = mgr.delete_group(gid)
        assert result is True
        groups = mgr.get_all_groups()
        assert not any(g["id"] == gid for g in groups)

    def test_delete_nonexistent_group(self, db_conn):
        """Test deleting a group that doesn't exist."""
        mgr = TechnicianGroupManager(db_conn)
        result = mgr.delete_group(9999)
        assert result is False

    def test_add_member(self, db_conn):
        """Test adding a member to a group."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("Team X")
        # Create a technician first
        db_conn.execute("INSERT INTO technicians (name) VALUES (?)", ("TechMember",))
        db_conn.commit()
        tid = db_conn.execute(
            "SELECT id FROM technicians WHERE name='TechMember'"
        ).fetchone()[0]

        result = mgr.add_member(gid, tid)
        assert result is not None

    def test_remove_member(self, db_conn):
        """Test removing a member from a group."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("Team Y")
        db_conn.execute("INSERT INTO technicians (name) VALUES (?)", ("TechRemove",))
        db_conn.commit()
        tid = db_conn.execute(
            "SELECT id FROM technicians WHERE name='TechRemove'"
        ).fetchone()[0]

        mgr.add_member(gid, tid)
        result = mgr.remove_member(gid, tid)
        assert result is True

    def test_remove_nonexistent_member(self, db_conn):
        """Test removing a member that isn't in the group."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("Team Z")
        result = mgr.remove_member(gid, 9999)
        assert result is False

    def test_get_group_members(self, db_conn):
        """Test getting members of a group."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("Members Team")
        db_conn.execute("INSERT INTO technicians (name) VALUES (?)", ("M1",))
        db_conn.execute("INSERT INTO technicians (name) VALUES (?)", ("M2",))
        db_conn.commit()
        t1 = db_conn.execute("SELECT id FROM technicians WHERE name='M1'").fetchone()[0]
        t2 = db_conn.execute("SELECT id FROM technicians WHERE name='M2'").fetchone()[0]
        mgr.add_member(gid, t1)
        mgr.add_member(gid, t2)

        members = mgr.get_group_members(gid)
        assert len(members) == 2
        assert all("id" in m and "name" in m for m in members)

    def test_delete_group_with_members(self, db_conn):
        """Test deleting a group cleans up member associations."""
        mgr = TechnicianGroupManager(db_conn)
        gid = mgr.get_or_create_group("GroupWithMembers")
        db_conn.execute("INSERT INTO technicians (name) VALUES (?)", ("Cleaner",))
        db_conn.commit()
        tid = db_conn.execute(
            "SELECT id FROM technicians WHERE name='Cleaner'"
        ).fetchone()[0]
        mgr.add_member(gid, tid)
        result = mgr.delete_group(gid)
        assert result is True
        # Verify member association is also removed
        row = db_conn.execute(
            "SELECT COUNT(*) FROM technician_group_members WHERE group_id = ?", (gid,)
        ).fetchone()[0]
        assert row == 0


class TestLineConditionManagerCrud:
    """Tests for LineConditionManager CRUD operations."""

    def test_create_condition(self, db_conn):
        """Test creating a new line condition."""
        mgr = LineConditionManager(db_conn)
        cid = mgr.create_condition("Power Off", "Turn off power", "red")
        assert cid is not None
        assert isinstance(cid, int)

    def test_create_duplicate_condition(self, db_conn):
        """Test creating a duplicate returns existing ID."""
        mgr = LineConditionManager(db_conn)
        cid1 = mgr.create_condition("Line Empty", "Empty the line", "yellow")
        cid2 = mgr.create_condition("Line Empty", "Different desc", "green")
        assert cid1 == cid2

    def test_get_all_conditions(self, db_conn):
        """Test listing all conditions."""
        mgr = LineConditionManager(db_conn)
        mgr.create_condition("Cond A", "Desc A", "red")
        mgr.create_condition("Cond B", "Desc B", "blue")
        conditions = mgr.get_all_conditions()
        assert len(conditions) >= 2
        assert all("id" in c and "name" in c for c in conditions)

    def test_update_condition(self, db_conn):
        """Test updating a condition."""
        mgr = LineConditionManager(db_conn)
        cid = mgr.create_condition("OldCond", "Old desc", "red")
        result = mgr.update_condition(cid, "NewCond", "New desc", "green")
        assert result is True

    def test_update_condition_duplicate_name(self, db_conn):
        """Test updating condition to a duplicate name returns False."""
        mgr = LineConditionManager(db_conn)
        mgr.create_condition("CondX", "Desc", "red")
        cid2 = mgr.create_condition("CondY", "Desc", "blue")
        result = mgr.update_condition(cid2, "CondX", "Desc", "green")
        assert result is False

    def test_delete_condition(self, db_conn):
        """Test deleting a condition."""
        mgr = LineConditionManager(db_conn)
        cid = mgr.create_condition("ToDeleteCond", "Desc", "red")
        result = mgr.delete_condition(cid)
        assert result is True

    def test_delete_nonexistent_condition(self, db_conn):
        """Test deleting a condition that doesn't exist."""
        mgr = LineConditionManager(db_conn)
        result = mgr.delete_condition(9999)
        assert result is False

    def test_assign_condition_to_task(self, db_conn):
        """Test assigning a condition to a task."""
        mgr = LineConditionManager(db_conn)
        cid = mgr.create_condition("AssignTest", "Desc", "yellow")
        task_mgr = TaskManager(db_conn)
        tid = task_mgr.get_or_create("Test Task")
        result = mgr.assign_condition_to_task(tid, cid)
        assert result is True

    def test_assign_duplicate_condition_to_task(self, db_conn):
        """Test assigning same condition twice is idempotent."""
        mgr = LineConditionManager(db_conn)
        cid = mgr.create_condition("DupAssign", "Desc", "green")
        task_mgr = TaskManager(db_conn)
        tid = task_mgr.get_or_create("Dup Task")
        mgr.assign_condition_to_task(tid, cid)
        result = mgr.assign_condition_to_task(tid, cid)
        assert result is True

    def test_get_conditions_for_task(self, db_conn):
        """Test getting conditions for a task."""
        mgr = LineConditionManager(db_conn)
        cid1 = mgr.create_condition("TaskCond1", "D1", "red")
        cid2 = mgr.create_condition("TaskCond2", "D2", "blue")
        task_mgr = TaskManager(db_conn)
        tid = task_mgr.get_or_create("Multi Cond Task")
        mgr.assign_condition_to_task(tid, cid1)
        mgr.assign_condition_to_task(tid, cid2)
        conditions = mgr.get_conditions_for_task(tid)
        assert len(conditions) == 2

    def test_remove_conditions_from_task(self, db_conn):
        """Test removing all conditions from a task."""
        mgr = LineConditionManager(db_conn)
        cid = mgr.create_condition("RemoveCond", "Desc", "red")
        task_mgr = TaskManager(db_conn)
        tid = task_mgr.get_or_create("Remove Task")
        mgr.assign_condition_to_task(tid, cid)
        mgr.remove_conditions_from_task(tid)
        conditions = mgr.get_conditions_for_task(tid)
        assert len(conditions) == 0

    def test_get_conditions_for_task_empty(self, db_conn):
        """Test getting conditions for a task with none assigned."""
        mgr = LineConditionManager(db_conn)
        task_mgr = TaskManager(db_conn)
        tid = task_mgr.get_or_create("Empty Cond Task")
        conditions = mgr.get_conditions_for_task(tid)
        assert conditions == []


class TestPopulateDummyDataWithConditions:
    """Test populate_dummy_data with line conditions data."""

    def test_populate_with_line_conditions(self, db_conn, temp_db):
        """Test populating dummy data including task line conditions."""
        init_db(temp_db, logger=None)
        logger = MagicMock()

        dummy_json = {
            "satellite_points": ["SP1"],
            "lines": [{"name": "Line1", "satellite_point": "SP1"}],
            "technology_groups": ["Group1"],
            "technologies": [{"name": "Tech1", "group": "Group1"}],
            "technicians": [
                {
                    "name": "T1",
                    "satellite_point": "SP1",
                    "skills": [{"name": "Tech1", "level": 3}],
                }
            ],
            "tasks": [
                {
                    "name": "Task1",
                    "required_skills": ["Tech1"],
                    "line_conditions": ["Line Empty", "Power Off"],
                }
            ],
        }

        with (
            patch("builtins.open", mock_open(read_data="{}")),
            patch("json.load", return_value=dummy_json),
        ):
            populate_dummy_data(db_conn, logger)

        # Verify tasks were created
        task_count = db_conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        assert task_count >= 1

        # Verify line conditions were created
        cond_count = db_conn.execute("SELECT COUNT(*) FROM line_conditions").fetchone()[
            0
        ]
        assert cond_count >= 2

        # Verify task-condition associations
        task_id = db_conn.execute("SELECT id FROM tasks WHERE name='Task1'").fetchone()[
            0
        ]
        assoc_count = db_conn.execute(
            "SELECT COUNT(*) FROM task_line_conditions WHERE task_id = ?", (task_id,)
        ).fetchone()[0]
        assert assoc_count == 2


class TestUpdateLineInvalidSatellitePoint:
    """Test update_line with invalid satellite point (line 675)."""

    def test_update_line_invalid_sp(self, db_conn, temp_db):
        """Test update_line returns error for invalid satellite point ID."""
        init_db(temp_db, logger=None)
        # Create a valid satellite point and line
        cursor = db_conn.cursor()
        cursor.execute("INSERT INTO satellite_points (name) VALUES (?)", ("ValidSP",))
        sp_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO lines (name, satellite_point_id) VALUES (?, ?)",
            ("TestLine", sp_id),
        )
        line_id = cursor.lastrowid
        db_conn.commit()

        # Try to update with invalid satellite point
        success, msg = update_line(db_conn, line_id, "NewName", 9999)
        assert success is False
        assert "Invalid satellite point ID" in msg
