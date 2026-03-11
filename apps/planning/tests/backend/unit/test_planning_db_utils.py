"""Consolidated tests for planning_db_utils.py."""

import sqlite3
from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.planning.src.services.planning_db_utils import (
    TaskManager,
    TechnicianGroupManager,
    TechnologyManager,
    add_line,
    clear_technician_skills,
    delete_line,
    delete_satellite_point,
    delete_technician,
    delete_technician_skill,
    ensure_skill_update_log_table,
    get_all_lines,
    get_all_satellite_points,
    get_all_technician_skills_by_name,
    get_all_technicians,
    get_db_connection,
    get_lines_for_satellite_point,
    get_or_create_satellite_point,
    get_technician_by_id,
    get_technician_lines_via_satellite_point,
    get_technician_skills_by_id,
    init_db,
    log_technician_skill_update,
    populate_dummy_data,
    update_line,
    update_satellite_point,
    update_technician_skill,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture for a temporary sqlite database."""
    return str(tmp_path / "test_planning.db")


@pytest.fixture
def db_conn(temp_db):
    """Fixture for a database connection."""
    conn = get_db_connection(temp_db)
    yield conn
    conn.close()


class TestDbUtils:
    """Consolidated database utility tests."""

    def test_init_and_connection(self, temp_db):
        init_db(temp_db, logger=None)
        conn = get_db_connection(temp_db)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_satellite_point_crud(self, db_conn, temp_db):
        init_db(temp_db, logger=None)
        sp_id = get_or_create_satellite_point(db_conn, "Consolidated Point")
        assert sp_id is not None

        success, msg = update_satellite_point(db_conn, sp_id, "New Name")
        assert success is True
        points = get_all_satellite_points(db_conn)
        assert any(p["name"] == "New Name" for p in points)

        # Test deletion protection
        add_line(db_conn, "Attached Line", sp_id)
        success, msg = delete_satellite_point(db_conn, sp_id)
        assert success is False

        delete_line(db_conn, db_conn.execute("SELECT id FROM lines").fetchone()[0])
        success, msg = delete_satellite_point(db_conn, sp_id)
        assert success is True

    def test_line_management(self, db_conn, temp_db):
        init_db(temp_db, logger=None)
        sp_id = get_or_create_satellite_point(db_conn, "SP")
        line_id = add_line(db_conn, "Line 1", sp_id)

        update_line(db_conn, line_id, "Line 1 Updated", sp_id)
        lines = get_all_lines(db_conn)
        assert any(line["name"] == "Line 1 Updated" for line in lines)

        # Technician association
        db_conn.execute(
            "INSERT INTO technicians (name, satellite_point_id) VALUES (?, ?)",
            ("Tech 1", sp_id),
        )
        tech_id = db_conn.execute(
            "SELECT id FROM technicians WHERE name='Tech 1'"
        ).fetchone()[0]
        tech_lines = get_technician_lines_via_satellite_point(db_conn, tech_id)
        assert "Line 1 Updated" in tech_lines

    def test_skill_management(self, db_conn, temp_db):
        init_db(temp_db, logger=None)
        db_conn.execute("INSERT INTO technicians (name) VALUES (?)", ("Tech Skill",))
        tech_id = db_conn.execute("SELECT id FROM technicians").fetchone()[0]
        db_conn.execute("INSERT INTO technologies (name) VALUES (?)", ("Tech A",))
        tech_a_id = db_conn.execute("SELECT id FROM technologies").fetchone()[0]

        update_technician_skill(db_conn, tech_id, tech_a_id, 3)
        skills = get_technician_skills_by_id(db_conn, tech_id)
        assert skills[tech_a_id] == 3

        all_skills = get_all_technician_skills_by_name(db_conn)
        assert all_skills["Tech Skill"][tech_a_id] == 3

    def test_logging(self, db_conn):
        ensure_skill_update_log_table(db_conn)
        log_technician_skill_update(db_conn, 1, 1, "task_1", 1, 2, "Log message")
        row = db_conn.execute("SELECT * FROM technician_skill_update_log").fetchone()
        assert row["message"] == "Log message"

    def test_managers(self, db_conn, temp_db):
        init_db(temp_db, logger=None)
        tech_mgr = TechnologyManager(db_conn)
        group_id = tech_mgr.get_or_create_group("Group 1")
        assert group_id is not None

        task_mgr = TaskManager(db_conn)
        assert task_mgr.get_or_create("Task 1") is not None

        group_mgr = TechnicianGroupManager(db_conn)
        assert group_mgr.get_or_create_group("Team 1") is not None

    def test_dummy_data_full(self, db_conn, temp_db):
        init_db(temp_db, logger=None)
        logger = MagicMock()

        # Mock data with parent technologies to cover both passes
        dummy_json = {
            "satellite_points": ["SP1"],
            "technology_groups": ["Group1"],
            "technologies": [
                {"name": "Tech1", "group": "Group1"},
                {"name": "Tech2", "group": "Group1", "parent": "Tech1"},
            ],
            "technicians": [
                {
                    "name": "T1",
                    "satellite_point": "SP1",
                    "skills": [{"name": "Tech1", "level": 2}],
                }
            ],
            "tasks": [{"name": "Task1", "required_skills": ["Tech1"]}],
        }

        with (
            patch("builtins.open", mock_open(read_data="{}")),
            patch("json.load", return_value=dummy_json),
        ):
            populate_dummy_data(db_conn, logger)

        assert db_conn.execute("SELECT COUNT(*) FROM technologies").fetchone()[0] == 2

    def test_init_db_restore(self, temp_db):
        """Test init_db branch where technicians are backed up."""
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE technicians (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO technicians VALUES (1, 'Old Tech')")
        conn.commit()
        conn.close()

        # init_db should backup and restore
        init_db(temp_db, logger=MagicMock())
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT name FROM technicians").fetchone()
        assert row["name"] == "Old Tech"
        conn.close()

    def test_additional_db_utils(self, db_conn, temp_db):
        """Test additional utility functions for coverage."""
        init_db(temp_db, logger=None)
        sp_id = get_or_create_satellite_point(db_conn, "SP1")
        line_id = add_line(db_conn, "Line 1", sp_id)

        # get_lines_for_satellite_point
        lines = get_lines_for_satellite_point(db_conn, sp_id)
        assert any(line["id"] == line_id for line in lines)

        # Technology groups
        tech_mgr = TechnologyManager(db_conn)
        groups = tech_mgr.get_all_groups()
        assert isinstance(groups, list)

        # Skills clearing/deletion
        db_conn.execute("INSERT INTO technicians (name) VALUES (?)", ("Tech X",))
        tid = db_conn.execute(
            "SELECT id FROM technicians WHERE name='Tech X'"
        ).fetchone()[0]
        db_conn.execute("INSERT INTO technologies (name) VALUES (?)", ("Tech X1",))
        tech_id = db_conn.execute("SELECT id FROM technologies").fetchone()[0]

        update_technician_skill(db_conn, tid, tech_id, 4)
        delete_technician_skill(db_conn, tid, tech_id)
        assert len(get_technician_skills_by_id(db_conn, tid)) == 0

        update_technician_skill(db_conn, tid, tech_id, 2)
        clear_technician_skills(db_conn, tid)
        assert len(get_technician_skills_by_id(db_conn, tid)) == 0

        # Task required skills
        task_mgr = TaskManager(db_conn)
        task_id = task_mgr.get_or_create("Repair X")
        task_mgr.add_required_skill(task_id, tech_id)
        skills = task_mgr.get_required_skills(task_id)
        assert any(s["technology_id"] == tech_id for s in skills)

        task_mgr.remove_required_skill(task_id, tech_id)
        assert len(task_mgr.get_required_skills(task_id)) == 0

        task_mgr.add_required_skill(task_id, tech_id)
        task_mgr.remove_all_required_skills(task_id)
        assert len(task_mgr.get_required_skills(task_id)) == 0

        # Technician management
        db_conn.execute(
            "INSERT INTO technicians (name, satellite_point_id) VALUES (?, ?)",
            ("Tech Y", sp_id),
        )
        all_techs = get_all_technicians(db_conn)
        assert any(t["name"] == "Tech Y" for t in all_techs)

        tech_y_id = [t["id"] for t in all_techs if t["name"] == "Tech Y"][0]
        tech_y = get_technician_by_id(db_conn, tech_y_id)
        assert tech_y["name"] == "Tech Y"

        success, msg = delete_technician(db_conn, tech_y_id)
        assert success is True
        assert get_technician_by_id(db_conn, tech_y_id) is None
