import json
import os
import sys
from datetime import datetime, time
from unittest.mock import MagicMock, mock_open, patch

import pytest

from apps.planning.src.services.planning_engine import PlanningEngine, generate_plan
from apps.planning.src.services.planning_models import PlanningTask, Schedule
from apps.planning.src.services.planning_result import PlanningResult, UnassignedReason
from src.services.db_utils import MaintenanceOrder, User

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))


class TestPlanningEngineCoverage:
    """Targeted tests to improve coverage for PlanningEngine."""

    @pytest.fixture
    def mock_models(self):
        """Mock all DB models used in PlanningEngine."""
        with (
            patch("apps.planning.src.services.planning_engine.User") as mock_user,
            patch("apps.planning.src.services.planning_engine.Team") as mock_team,
            patch(
                "apps.planning.src.services.planning_engine.MaintenanceOrder"
            ) as mock_mo,
            patch("apps.planning.src.services.planning_engine.PlanningTask") as mock_pt,
            patch("apps.planning.src.services.planning_engine.Schedule"),
            patch("apps.planning.src.services.planning_engine.db") as mock_db,
        ):
            # Setup User query chain
            mock_user.query.filter.return_value.all.return_value = []
            mock_user.team_id.isnot.return_value = MagicMock()

            # Setup defaults
            yield {
                "User": mock_user,
                "Team": mock_team,
                "MaintenanceOrder": mock_mo,
                "PlanningTask": mock_pt,
                "db": mock_db,
            }

    @pytest.fixture
    def engine(self, mock_models):
        return PlanningEngine(logger=MagicMock())

    def test_load_config_missing_files(self, engine):
        """Test _load_config when no files exist."""
        with patch("os.path.exists", return_value=False):
            config = engine._load_config()
            assert config == {}
            engine.logger.error.assert_called_with("No configuration file found!")

    def test_load_config_exception(self, engine):
        """Test _load_config handling exceptions."""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid json")),
            patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)),
        ):
            config = engine._load_config()
            assert config == {}
            # Verify error logging
            assert engine.logger.error.call_count == 1

    def test_parse_time_str_invalid(self, engine):
        """Test _parse_time_str with invalid input."""
        res = engine._parse_time_str("invalid")
        assert res == time(0, 0)

    def test_generate_plan_no_tasks(self, engine):
        """Test generate_plan with no plannable tasks."""
        schedule = MagicMock(spec=Schedule)
        schedule.id = 1
        schedule.name = "Test Schedule"
        schedule.start_date = datetime(2023, 1, 1)
        schedule.end_date = datetime(2023, 1, 2)

        with patch.object(engine, "_get_plannable_tasks", return_value=[]):
            result = engine.generate_plan(schedule, planning_mode="weekend")
            assert "No plannable tasks found for this schedule" in result.warnings
            assert len(result.assigned_tasks) == 0

    def test_generate_plan_weekend_filtering(self, engine):
        """Test weekend mode filtering branch."""
        schedule = MagicMock(spec=Schedule)
        schedule.id = 1
        schedule.name = "Test Schedule"
        schedule.start_date = datetime(2023, 1, 1)
        schedule.end_date = datetime(2023, 1, 2)

        tasks = [MagicMock(spec=PlanningTask)]

        with (
            patch.object(engine, "_get_plannable_tasks", return_value=tasks),
            patch.object(
                engine, "_filter_weekend_tasks", return_value=[]
            ) as mock_filter,
        ):
            result = engine.generate_plan(schedule, planning_mode="weekend")

            mock_filter.assert_called_once()
            assert "No plannable tasks found for this schedule" in result.warnings

    def test_assign_single_task_time_window_fail(self, engine):
        """Test assignment fails if task doesn't fit time window."""
        task = MagicMock(spec=PlanningTask)
        mo = MagicMock(spec=MaintenanceOrder)
        mo.estimated_completion_time = 120
        mo.labour_count = 1
        result = MagicMock(spec=PlanningResult)

        with patch.object(engine, "_fits_time_window", return_value=False):
            res = engine._assign_single_task(
                task, mo, [], {}, datetime.now(), result, "planning_mode", 60
            )
            assert res is None
            result.add_unassigned.assert_called_once()
            args = result.add_unassigned.call_args[0][0]
            assert args.reason == UnassignedReason.INSUFFICIENT_TIME

    def test_assign_single_task_shift_window_fail(self, engine):
        """Test assignment fails if task exceeds remaining shift time."""
        task = MagicMock(spec=PlanningTask)
        mo = MagicMock(spec=MaintenanceOrder)
        mo.estimated_completion_time = 60
        mo.labour_count = 1

        current_time = datetime(2023, 1, 1, 10, 0)
        shift_end = datetime(2023, 1, 1, 10, 30)  # Only 30 mins left

        with patch.object(engine, "_fits_time_window", return_value=True):
            res = engine._assign_single_task(
                task,
                mo,
                [],
                {},
                current_time,
                MagicMock(),
                "planning_mode",
                120,
                shift_end_time=shift_end,
            )
            assert res is None

    def test_assign_single_task_skills_failure(self, engine):
        """Test assignment fails if team lacks required skills."""
        task = MagicMock(spec=PlanningTask)
        task.id = 1
        mo = MagicMock(spec=MaintenanceOrder)
        mo.id = 101
        mo.estimated_completion_time = 60
        mo.labour_count = 2  # Multi-tech
        mo.required_skills = [MagicMock(name="SkillA"), MagicMock(name="SkillB")]
        mo.description = "Test Task"
        mo.priority = "High"
        mo.order_type = "PM"

        techs = [MagicMock(spec=User), MagicMock(spec=User)]

        with (
            patch.object(engine, "_fits_time_window", return_value=True),
            patch.object(engine, "_find_team_with_skill_coverage", return_value=techs),
            patch.object(engine, "_select_best_team", return_value=techs),
            patch.object(engine, "_team_has_all_skills", return_value=False),
        ):
            res = engine._assign_single_task(
                task, mo, techs, {}, datetime.now(), MagicMock(), "planning_mode", 120
            )
            assert res is None

    def test_plannable_tasks_validation(self, engine, mock_models):
        """Test _get_plannable_tasks validation logic (missing MO, invalid time,
        parts)."""
        schedule = MagicMock(spec=Schedule)
        schedule.id = 1
        result = MagicMock(spec=PlanningResult)

        # Create tasks
        task1 = MagicMock(
            spec=PlanningTask, id=1, maintenance_order_id=101
        )  # Missing MO
        task2 = MagicMock(
            spec=PlanningTask, id=2, maintenance_order_id=102
        )  # Invalid Time
        task3 = MagicMock(
            spec=PlanningTask, id=3, maintenance_order_id=103
        )  # Invalid Labour
        task4 = MagicMock(
            spec=PlanningTask, id=4, maintenance_order_id=104
        )  # Check Parts Fail
        task5 = MagicMock(spec=PlanningTask, id=5, maintenance_order_id=105)  # Valid

        mock_models["PlanningTask"].query.filter.return_value.all.return_value = [
            task1,
            task2,
            task3,
            task4,
            task5,
        ]

        # Mock MaintenanceOrder.query.get
        mo2 = MagicMock(spec=MaintenanceOrder, estimated_completion_time=0)
        mo3 = MagicMock(
            spec=MaintenanceOrder, estimated_completion_time=60, labour_count=0
        )
        mo4 = MagicMock(
            spec=MaintenanceOrder, estimated_completion_time=60, labour_count=1
        )
        mo5 = MagicMock(
            spec=MaintenanceOrder, estimated_completion_time=60, labour_count=1
        )

        def get_mo(model, id):
            mapping = {102: mo2, 103: mo3, 104: mo4, 105: mo5}
            return mapping.get(id)

        mock_models["db"].session.get.side_effect = get_mo

        with patch(
            "apps.planning.src.services.planning_engine.check_spare_parts_availability"
        ) as mock_parts:
            mock_parts.side_effect = lambda mo: (
                (False, "Missing Part") if mo == mo4 else (True, None)
            )

            plannable = engine._get_plannable_tasks(
                schedule, check_parts=True, result=result
            )

            # 5 tasks total:
            # 1: Missing MO -> Warning
            # 2: Invalid Time -> Unassigned INVALID_DATA
            # 3: Invalid Labour -> Unassigned INVALID_DATA
            # 4: Parts Fail -> Unassigned INSUFFICIENT_PARTS
            # 5: Valid -> Returned

            assert len(plannable) == 1
            assert plannable[0][0] == task5

            # Verify calls to result
            assert result.add_warning.call_count >= 1
            assert result.add_unassigned.call_count >= 3

    def test_no_technicians_available(self, engine, mock_models):
        """Test generate_plan when no technicians are found."""
        schedule = MagicMock(spec=Schedule)
        schedule.start_date = datetime.now()
        schedule.end_date = datetime.now()

        # Ensure User query returns empty list
        mock_models["User"].query.filter.return_value.all.return_value = []

        # Mock tasks existing so we enter the check block
        with (
            patch.object(
                engine,
                "_get_plannable_tasks",
                return_value=[(MagicMock(), MagicMock())],
            ),
            patch.object(engine, "_filter_weekend_tasks", side_effect=lambda t, r: t),
            patch("time.time", return_value=0),
        ):
            result = engine.generate_plan(schedule)

            assert "No available technicians found" in result.errors
            assert len(result.unassigned_tasks) == 1
            assert (
                result.unassigned_tasks[0].reason
                == UnassignedReason.NO_AVAILABLE_TECHNICIANS
            )

    def test_team_selection_logic(self, engine):
        """Test greedy algorithm for team selection."""
        # Setup: 2 required skills (A, B)
        # Tech1: A
        # Tech2: B
        # Tech3: A, B

        req_skills = ["SkillA", "SkillB"]

        # Helper to create tech with skills
        def create_tech(id, *skill_names):
            t = MagicMock(spec=User, id=id, username=f"T{id}")
            t.skills = []
            for s in skill_names:
                us = MagicMock()
                us.skill.name = s
                # Mock skill_level for scoring (default 3)
                us.skill_level = 3
                t.skills.append(us)
            return t

        t1 = create_tech(1, "SkillA")
        t2 = create_tech(2, "SkillB")
        t3 = create_tech(3, "SkillA", "SkillB")

        # Case 1: Greedy selection prefers T3 (covers 2) then anyone else (if needed)
        # However, _find_team_with_skill_coverage filters by availability
        # using _has_available_time
        # We must mock _has_available_time to return True

        with patch.object(engine, "_has_available_time", return_value=True):
            # Pass all techs
            available = [t1, t2, t3]

            # Request team of size 1. T3 covers all.
            res = engine._find_team_with_skill_coverage(
                available, req_skills, 1, {}, 60
            )
            assert t3 in res
            assert len(res) == 1

            # Request team of size 2. T3 + T1 or T2.
            res = engine._find_team_with_skill_coverage(
                available, req_skills, 2, {}, 60
            )
            assert t3 in res
            assert len(res) == 2

            # Request team of size 2 but only T1 and T2 available.
            # T1 covers A, T2 covers B. Together cover {A, B}.
            res = engine._find_team_with_skill_coverage([t1, t2], req_skills, 2, {}, 60)
            assert len(res) == 2
            assert t1 in res
            assert t2 in res

    def test_select_best_team_scoring(self, engine):
        """Test scoring logic in _select_best_team."""
        # Techs:
        # T1: High workload (bad time score), High skills
        # T2: Low workload (good time score), Low skills

        t1 = MagicMock(spec=User, id=1)
        t1.skills = [MagicMock(), MagicMock(), MagicMock()]  # 3 skills
        for s in t1.skills:
            s.skill_level = 5

        t2 = MagicMock(spec=User, id=2)
        t2.skills = [MagicMock()]  # 1 skill
        for s in t2.skills:
            s.skill_level = 1

        # Workloads
        wl1 = MagicMock(
            total_available_minutes=100, total_assigned_minutes=90
        )  # 10% remaining
        wl2 = MagicMock(
            total_available_minutes=100, total_assigned_minutes=10
        )  # 90% remaining

        workloads = {1: wl1, 2: wl2}

        # Test selection
        # T2 has high time score (0.9), low skill (1/3=0.33), low level (0.2).
        # Total ~ 0.36 + 0.1 + 0.06 = 0.52
        # T1 has low time score (0.1), high skill (1.0), high level (1.0).
        # Total ~ 0.04 + 0.3 + 0.3 = 0.64
        # T1 should win? Let's see weights: Time 40%, SkillCount 30%, SkillLevel 30%
        # T1: 0.1*0.4=0.04. 1.0*0.3=0.3. 1.0*0.3=0.3. Sum=0.64.
        # T2: 0.9*0.4=0.36. 0.33*0.3=0.1. 0.2*0.3=0.06. Sum=0.52.
        # So T1 should form the team if size=1.

        # Mock _balance_team_experience to return top N
        with patch.object(
            engine,
            "_balance_team_experience",
            side_effect=lambda scores, n: [x[0] for x in scores[:n]],
        ):
            eligible = [t1, t2]
            best = engine._select_best_team(eligible, 1, workloads)
            assert best == [t1]

            # Adjust T1 workload to be REALLY full (0 remaining) -> TimeScore 0
            # Sum=0.6. Still wins.

            # Adjust T2 skill to be better.

    def test_balance_team_experience(self, engine):
        """Test _balance_team_experience logic."""
        # Setup Scored Techs: (Tech, Score, SkillCount, AvgLevel)
        t_senior = MagicMock(spec=User, id=1, username="Senior")
        t_mid = MagicMock(spec=User, id=2, username="Mid")
        t_junior = MagicMock(spec=User, id=3, username="Junior")

        # (Tech, Score, Count, Level)
        # Senior: Level 5
        # Mid: Level 3
        # Junior: Level 1
        scored = [
            (t_senior, 0.9, 5, 5.0),
            (t_mid, 0.8, 3, 3.0),
            (t_junior, 0.7, 1, 1.0),
        ]

        # Case 1: Team size 1 -> Pick highest score (Senior)
        res = engine._balance_team_experience(scored, 1)
        assert res == [t_senior]

        # Case 2: Team size 2 -> Senior + Next best (Mid)
        res = engine._balance_team_experience(scored, 2)
        assert t_senior in res
        assert t_mid in res
        assert len(res) == 2

        # Case 3: Team size 2, NO SENIORS
        scored_no_senior = [(t_mid, 0.8, 3, 3.0), (t_junior, 0.7, 1, 1.0)]
        res = engine._balance_team_experience(scored_no_senior, 2)
        assert t_mid in res
        assert t_junior in res

    def test_calculate_adjusted_duration(self, engine):
        """Test duration adjustment logic."""
        base = 100
        # Required 1, Actual 1 -> Base
        assert engine._calculate_adjusted_duration(base, 1, 1) == 100

        # Required 1, Actual 2 -> 1 extra -> 10% gain -> 90
        assert engine._calculate_adjusted_duration(base, 1, 2) == 90

        # Required 1, Actual 4 -> 3 extra -> 30% max gain -> 70
        assert engine._calculate_adjusted_duration(base, 1, 4) == 70

        # Required 1, Actual 10 -> 9 extra -> 30% max -> 70
        assert engine._calculate_adjusted_duration(base, 1, 10) == 70

    # Removed unused test_generate_plan_convenience_function

    def test_generate_plan_wrapper(self):
        """Test wrapper function separately to avoid mock definition issues."""
        with (
            patch(
                "apps.planning.src.services.planning_engine.Schedule"
            ) as MockSchedule,
            patch(
                "apps.planning.src.services.planning_engine.PlanningEngine"
            ) as MockEngine,
            patch("apps.planning.src.services.planning_engine.db") as MockDb,
        ):
            # Case Success
            MockDb.session.get.return_value = MagicMock(id=1)
            mock_inst = MockEngine.return_value
            mock_inst.generate_plan.return_value = "Result"

            res = generate_plan(1, "weekend")
            assert res == "Result"
            MockDb.session.get.assert_called_with(MockSchedule, 1)
            mock_inst.generate_plan.assert_called()

            # Case Failure (No Schedule)
            MockDb.session.get.return_value = None
            with pytest.raises(ValueError):
                generate_plan(999)
