"""Unit tests for the Planning Engine."""

import json
from datetime import datetime, time
from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.planning.src.services.planning_engine import PlanningEngine, generate_plan
from apps.planning.src.services.planning_models import PlanningTask, Schedule
from apps.planning.src.services.planning_result import PlanningResult
from src.services.db_utils import MaintenanceOrder, User


@pytest.fixture
def mock_all_models():
    """Mock database models in the planning_engine namespace."""
    with (
        patch("apps.planning.src.services.planning_engine.Team") as m_team,
        patch("apps.planning.src.services.planning_engine.User") as m_user,
        patch("apps.planning.src.services.planning_engine.MaintenanceOrder") as m_mo,
        patch("apps.planning.src.services.planning_engine.PlanningTask") as m_pt,
        patch("apps.planning.src.services.planning_engine.Schedule") as m_sch,
        patch("apps.planning.src.services.planning_engine.db") as m_db,
    ):
        m_team.query.all.return_value = []
        m_team.query.filter.return_value.all.return_value = []
        m_user.query.filter.return_value.all.return_value = []
        m_pt.query.filter.return_value.all.return_value = []
        m_sch.query.filter.return_value.all.return_value = []
        m_user.team_id.isnot.return_value = MagicMock()

        yield {
            "Team": m_team,
            "User": m_user,
            "MaintenanceOrder": m_mo,
            "PlanningTask": m_pt,
            "Schedule": m_sch,
            "db": m_db,
        }


@pytest.fixture
def engine(mock_all_models):
    """Fixture to provide a PlanningEngine instance with a mocked logger."""
    return PlanningEngine(logger=MagicMock())


@pytest.fixture
def mock_schedule():
    """Fixture for a mocked Schedule object."""
    schedule = MagicMock(spec=Schedule)
    schedule.id = 1
    schedule.name = "Test Schedule"
    schedule.start_date = datetime(2025, 1, 1, 6, 0)
    schedule.end_date = datetime(2025, 1, 1, 18, 0)
    schedule.tasks = []
    return schedule


class TestPlanningEngine:
    """Consolidated tests for the PlanningEngine core logic and coverage."""

    def test_engine_init(self, engine):
        """Test engine initialization."""
        assert engine is not None

    # =========================================================================
    # UTILS & CONFIG
    # =========================================================================

    def test_parse_time_str(self, engine):
        """Test parsing of time strings."""
        assert engine._parse_time_str("06:00").hour == 6
        assert engine._parse_time_str("invalid") == time(0, 0)

    def test_load_config_coverage(self, engine):
        """Test _load_config edge cases."""
        # Missing files
        with patch("os.path.exists", return_value=False):
            assert engine._load_config() == {}
            engine.logger.error.assert_called()

        # Exception handling
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid json")),
            patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)),
        ):
            assert engine._load_config() == {}
            assert engine.logger.error.call_count >= 1

    # =========================================================================
    # TEAM & SELECTION LOGIC
    # =========================================================================

    def test_get_working_teams(self, engine, mock_all_models):
        """Test team rotation logic."""
        team_a = MagicMock()
        team_a.name = "Team A"
        mock_all_models["Team"].query.filter.return_value.all.return_value = [team_a]

        date = datetime(2025, 1, 1)
        teams = engine._get_working_teams(date)
        assert any(t.name == "Team A" for t in teams)

    def test_team_selection_greedy(self, engine):
        """Test greedy algorithm for team selection based on skills."""
        req_skills = ["SkillA", "SkillB"]

        def create_tech(id, *skills):
            t = MagicMock(spec=User, id=id, username=f"T{id}")
            t.skills = []
            for s in skills:
                us = MagicMock()
                us.skill.name = s
                us.skill_level = 3
                t.skills.append(us)
            return t

        t1 = create_tech(1, "SkillA")
        t2 = create_tech(2, "SkillB")
        t3 = create_tech(3, "SkillA", "SkillB")

        with patch.object(engine, "_has_available_time", return_value=True):
            # T3 covers all
            res = engine._find_team_with_skill_coverage(
                [t1, t2, t3], req_skills, 1, {}, 60
            )
            assert t3 in res
            assert len(res) == 1

            # T1 + T2 cover all
            res = engine._find_team_with_skill_coverage([t1, t2], req_skills, 2, {}, 60)
            assert len(res) == 2
            assert t1 in res and t2 in res

    def test_select_best_team_scoring(self, engine):
        """Test scoring and top-N selection in _select_best_team."""

        def create_mock_skill(level):
            s = MagicMock()
            s.skill_level = level
            return s

        t1 = MagicMock(spec=User, id=1)
        t1.skills = [create_mock_skill(3)]
        t2 = MagicMock(spec=User, id=2)
        t2.skills = [create_mock_skill(3)]

        # Workloads: Use real numbers to avoid MagicMock comparison errors
        w1 = MagicMock()
        w1.total_available_minutes = 100
        w1.total_assigned_minutes = 90
        w2 = MagicMock()
        w2.total_available_minutes = 100
        w2.total_assigned_minutes = 10
        workloads = {1: w1, 2: w2}

        with patch.object(
            engine,
            "_balance_team_experience",
            side_effect=lambda s, n: [x[0] for x in s[:n]],
        ):
            best = engine._select_best_team([t1, t2], 1, workloads)
            # Time score weight is 0.4. T2 should rank higher if skills equal.
            assert best == [t2]

    def test_calculate_adjusted_duration(self, engine):
        """Test duration adjustment for extra technicians."""
        base = 100
        assert engine._calculate_adjusted_duration(base, 1, 1) == 100
        assert engine._calculate_adjusted_duration(base, 1, 2) == 90
        assert engine._calculate_adjusted_duration(base, 1, 4) == 70  # Max 30% gain

    # =========================================================================
    # PLANNING EXECUTION & FILTERING
    # =========================================================================

    def test_plannable_tasks_validation(self, engine, mock_all_models):
        """Test _get_plannable_tasks validation (missing MO, parts, etc)."""
        result = MagicMock(spec=PlanningResult)
        task1 = MagicMock(
            spec=PlanningTask, id=1, maintenance_order_id=101
        )  # Invalid MO
        task2 = MagicMock(spec=PlanningTask, id=2, maintenance_order_id=102)  # Valid MO
        mock_all_models["PlanningTask"].query.filter.return_value.all.return_value = [
            task1,
            task2,
        ]

        mo2 = MagicMock(
            spec=MaintenanceOrder, estimated_completion_time=60, labour_count=1
        )

        def mock_get(model, id):
            return mo2 if id == 102 else None

        mock_all_models["db"].session.get.side_effect = mock_get

        with patch(
            "apps.planning.src.services.planning_engine.check_spare_parts_availability",
            return_value=(True, None),
        ):
            # All 3 positional arguments are required
            plannable = engine._get_plannable_tasks(MagicMock(), True, result)
            assert len(plannable) == 1
            assert plannable[0][0] == task2
            result.add_warning.assert_called()

    def test_generate_plan_no_tasks(self, engine, mock_schedule):
        """Test generate_plan with no plannable tasks found."""
        with patch.object(engine, "_get_plannable_tasks", return_value=[]):
            result = engine.generate_plan(mock_schedule, planning_mode="weekend")
            assert "No plannable tasks found for this schedule" in result.warnings

    def test_no_technicians_available(self, engine, mock_all_models, mock_schedule):
        """Test generate_plan when no technicians exist."""
        mock_all_models["User"].query.filter.return_value.all.return_value = []
        with (
            patch.object(
                engine,
                "_get_plannable_tasks",
                return_value=[(MagicMock(), MagicMock())],
            ),
            patch.object(engine, "_filter_weekend_tasks", side_effect=lambda t, r: t),
        ):
            result = engine.generate_plan(mock_schedule)
            assert "No available technicians found" in result.errors

    @patch("src.services.shift_utils.get_shift_teams")
    @patch("apps.planning.src.services.planning_engine.check_spare_parts_availability")
    def test_generate_plan_complex(
        self, mock_parts, mock_get_shifts, engine, mock_schedule
    ):
        """Test full planning cycle success."""
        mock_parts.return_value = (True, [])
        team = MagicMock(name="Team A")
        tech = MagicMock(id=101, team=team, skills=[])
        tech.username = "Tech1"  # Fix join(tech.username) error
        mock_get_shifts.return_value = (team, None)

        task = MagicMock(id=1)
        mo = MagicMock(
            id=501,
            order_type="REP",
            priority="High",
            labour_count=1,
            estimated_completion_time=30,
            required_skills=[],
        )

        with (
            patch.object(engine, "_get_available_technicians", return_value=[tech]),
            patch.object(engine, "_get_plannable_tasks", return_value=[(task, mo)]),
            patch("apps.planning.src.services.planning_engine.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = datetime(2025, 1, 1, 6, 0)
            mock_dt.utcnow.return_value = datetime(2025, 1, 1, 6, 0)

            result = engine.generate_plan(mock_schedule, planning_mode="shift_break")
            assert len(result.assigned_tasks) == 1
            assert result.assigned_tasks[0].planning_task_id == 1

    def test_generate_plan_wrapper(self, mock_all_models):
        """Test convenience wrapper function."""
        mock_all_models["db"].session.get.return_value = MagicMock(id=1)
        with patch(
            "apps.planning.src.services.planning_engine.PlanningEngine.generate_plan",
            return_value="OK",
        ):
            assert generate_plan(1) == "OK"

        mock_all_models["db"].session.get.return_value = None
        with pytest.raises(ValueError):
            generate_plan(999)
