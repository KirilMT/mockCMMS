"""Unit tests for the Planning Engine."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.planning.src.services.planning_engine import PlanningEngine


@pytest.fixture
def engine():
    """Fixture to provide a PlanningEngine instance with a mocked logger."""
    return PlanningEngine(logger=MagicMock())


@pytest.fixture
def mock_schedule():
    """Fixture for a mocked Schedule object."""
    schedule = MagicMock()
    schedule.id = 1
    schedule.name = "Test Schedule"
    schedule.start_date = datetime(2025, 1, 1, 6, 0)
    schedule.end_date = datetime(2025, 1, 1, 18, 0)
    schedule.tasks = []
    return schedule


@pytest.fixture(autouse=True)
def mock_all_models():
    """Mock database models in the planning_engine namespace."""
    with (
        patch("apps.planning.src.services.planning_engine.Team") as m_team,
        patch("apps.planning.src.services.planning_engine.User") as m_user,
        patch("apps.planning.src.services.planning_engine.MaintenanceOrder") as m_mo,
        patch("apps.planning.src.services.planning_engine.PlanningTask") as m_pt,
        patch("apps.planning.src.services.planning_engine.Schedule") as m_sch,
    ):
        m_team.query.all.return_value = []
        m_team.query.filter.return_value.all.return_value = []
        m_user.query.filter.return_value.all.return_value = []
        m_pt.query.filter.return_value.all.return_value = []
        m_sch.query.filter.return_value.all.return_value = []

        yield {
            "Team": m_team,
            "User": m_user,
            "MaintenanceOrder": m_mo,
            "PlanningTask": m_pt,
            "Schedule": m_sch,
        }


class TestPlanningEngine:
    """Tests for the PlanningEngine core logic."""

    def test_engine_init(self, engine):
        """Test engine initialization."""
        assert engine is not None

    def test_parse_time_str(self, engine):
        """Test parsing of time strings."""
        assert engine._parse_time_str("06:00").hour == 6

    def test_get_working_teams(self, engine, mock_all_models):
        """Test team rotation logic."""
        # This uses local import src.services.db_utils.Team
        with patch("apps.planning.src.services.planning_engine.Team") as m_db_team:
            team_a = MagicMock()
            team_a.name = "Team A"
            m_db_team.query.filter.return_value.all.return_value = [team_a]

            date_odd = datetime(2025, 1, 1)  # Wednesday
            teams = engine._get_working_teams(date_odd)
            assert any(t.name == "Team A" for t in teams)

    @patch("src.services.shift_utils.get_shift_teams")
    @patch("apps.planning.src.services.planning_engine.check_spare_parts_availability")
    def test_generate_plan_complex(
        self, mock_parts, mock_get_shifts, engine, mock_schedule, mock_all_models
    ):
        """Test full planning cycle with tasks and technicians."""
        mock_parts.return_value = (True, [])

        team_a = MagicMock()
        team_a.name = "Team A"

        tech = MagicMock()
        tech.id = 101
        tech.username = "Tech1"
        tech.team = team_a
        tech.skills = []

        # Mock shift teams for the date
        mock_get_shifts.return_value = (team_a, None)

        # Setup mock task and MO
        task = MagicMock()
        task.id = 1

        mo = MagicMock()
        mo.id = 501
        mo.description = "Repair Pump"
        mo.order_type = "REP"
        mo.priority = "High"
        mo.labour_count = 1
        mo.estimated_completion_time = 30
        mo.required_skills = []

        # Patch engine methods
        with (
            patch.object(engine, "_get_available_technicians", return_value=[tech]),
            patch.object(engine, "_get_plannable_tasks", return_value=[(task, mo)]),
            patch("apps.planning.src.services.planning_engine.datetime") as mock_dt,
        ):
            fixed_now = datetime(2025, 1, 1, 6, 0)
            mock_dt.now.return_value = fixed_now
            mock_dt.utcnow.return_value = fixed_now

            result = engine.generate_plan(mock_schedule, planning_mode="shift_break")

            assert result is not None
            assert len(result.assigned_tasks) == 1
            assert result.assigned_tasks[0].planning_task_id == 1

    def test_initialize_workloads(self, engine):
        """Test workload initialization."""
        techs = [MagicMock(id=1, username="T1", team=None)]
        workloads = engine._initialize_workloads(techs, 720)
        assert 1 in workloads
        assert workloads[1].total_available_minutes == 720

    def test_prioritize_tasks(self, engine):
        """Test task prioritization."""
        mo_pm = MagicMock(order_type="PM", priority="Medium", id=1)
        mo_rep = MagicMock(order_type="REP", priority="High", id=2)
        tasks = [(MagicMock(), mo_pm), (MagicMock(), mo_rep)]
        sorted_tasks = engine._prioritize_tasks(tasks, "shift_break")
        assert sorted_tasks[0][1].order_type == "REP"
