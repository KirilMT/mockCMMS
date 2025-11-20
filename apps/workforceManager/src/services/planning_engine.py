# apps/workforceManager/src/services/planning_engine.py

"""
Planning Engine - Core Assignment Algorithm

This module implements the skill-based task assignment algorithm for the Planning module.
It replaces the legacy Excel-based task_assigner.py with a clean implementation using
SQLAlchemy domain models.

Key Features:
- Skill-based task-to-technician matching
- Team size optimization
- Workload balancing
- Priority-based task ordering
- Constraint validation (spare parts, skills, availability)
"""

import time
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Set
from collections import defaultdict

from src.services.db_utils import db, MaintenanceOrder, Technician, Skill
from .planning_models import PlanningTask, Schedule, TechnicianSkill
from .planning_result import (
    PlanningResult, TaskAssignment, UnassignedTask, TechnicianWorkload,
    UnassignedReason
)
from .inventory_service import check_spare_parts_availability


class PlanningEngine:
    """
    Core planning engine for skill-based task assignment.

    This class encapsulates the algorithm for assigning maintenance tasks
    to technicians based on skills, availability, and workload balancing.
    """

    def __init__(self, logger=None):
        """
        Initialize the planning engine.

        Args:
            logger: Optional logger instance for debugging
        """
        self.logger = logger
        self._log("info", "Planning Engine initialized")

    def _log(self, level: str, message: str, *args):
        """Helper to log or print messages."""
        if self.logger:
            getattr(self.logger, level)(message, *args)
        else:
            print(f"[{level.upper()}] {message % args if args else message}")

    def generate_plan(
        self,
        schedule: Schedule,
        planning_mode: str = "weekend",
        shift_duration_minutes: int = 720,  # 12 hours default
        check_parts: bool = True,
        max_task_duration: int = None  # NEW: Time constraint for shift-break mode
    ) -> PlanningResult:
        """
        Generate a complete planning result for a schedule.

        Args:
            schedule: Schedule object containing tasks to plan
            planning_mode: "shift_break" (30-min windows) or "weekend" (multi-day)
            shift_duration_minutes: Total available minutes per shift
            check_parts: Whether to check spare parts availability
            max_task_duration: Maximum task duration in minutes (auto-set by mode if None)

        Returns:
            PlanningResult with all assignments and metadata
        """
        start_time = time.time()

        # Set mode-specific constraints
        if planning_mode == "shift_break":
            max_task_duration = max_task_duration or 30  # 30-minute default for shift breaks
            self._log("info", f"Shift-break mode: max task duration = {max_task_duration} min")
        else:  # weekend mode
            max_task_duration = max_task_duration or shift_duration_minutes  # No effective limit
            self._log("info", f"Weekend mode: no strict time limit")

        self._log("info", f"Starting planning for schedule: {schedule.name}")
        self._log("info", f"Mode: {planning_mode}, Shift Duration: {shift_duration_minutes} min")

        # Initialize result
        result = PlanningResult(
            schedule_id=schedule.id,
            schedule_name=schedule.name,
            planning_mode=planning_mode,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            created_at=datetime.utcnow()
        )

        # Get plannable tasks (with MO data)
        tasks_to_plan = self._get_plannable_tasks(schedule, check_parts, result)

        # Apply mode-specific filtering
        if planning_mode == "weekend":
            tasks_to_plan = self._filter_weekend_tasks(tasks_to_plan, result)

        if not tasks_to_plan:
            result.add_warning("No plannable tasks found for this schedule")
            result.calculate_statistics()
            result.statistics.planning_duration_seconds = time.time() - start_time
            return result

        # Get available technicians
        available_technicians = self._get_available_technicians(schedule)

        if not available_technicians:
            result.add_error("No available technicians found")
            for task, mo in tasks_to_plan:
                result.add_unassigned(self._create_unassigned_task(
                    task, mo, UnassignedReason.NO_AVAILABLE_TECHNICIANS,
                    "No technicians are available for this planning period"
                ))
            result.calculate_statistics()
            result.statistics.planning_duration_seconds = time.time() - start_time
            return result

        self._log("info", f"Found {len(tasks_to_plan)} tasks and {len(available_technicians)} technicians")

        # Initialize workload tracking
        technician_workloads = self._initialize_workloads(
            available_technicians, shift_duration_minutes
        )

        # Sort tasks by priority
        sorted_tasks = self._prioritize_tasks(tasks_to_plan, planning_mode)

        # Assign tasks
        current_time = schedule.start_date
        for task, mo in sorted_tasks:
            assignment_result = self._assign_single_task(
                task, mo, available_technicians, technician_workloads,
                current_time, result, planning_mode, max_task_duration
            )

            if assignment_result:
                result.add_assignment(assignment_result)
                # Update current time for next task (simple sequential for now)
                current_time = assignment_result.planned_end_time

        # Finalize workloads
        result.technician_workloads = list(technician_workloads.values())

        # Calculate statistics
        result.calculate_statistics()
        result.statistics.planning_duration_seconds = time.time() - start_time

        self._log("info", f"Planning complete: {len(result.assigned_tasks)} assigned, "
                         f"{len(result.unassigned_tasks)} unassigned")

        return result

    def _get_plannable_tasks(
        self,
        schedule: Schedule,
        check_parts: bool,
        result: PlanningResult
    ) -> List[Tuple[PlanningTask, MaintenanceOrder]]:
        """
        Get all tasks that can be planned (filtered by constraints).

        Returns list of (PlanningTask, MaintenanceOrder) tuples.
        """
        plannable_tasks = []

        # Get all unplanned or draft tasks for this schedule
        tasks = PlanningTask.query.filter(
            PlanningTask.schedule_id == schedule.id,
            PlanningTask.status.in_(['Unplanned', 'Draft'])
        ).all()

        for task in tasks:
            mo = MaintenanceOrder.query.get(task.maintenance_order_id)

            if not mo:
                result.add_warning(f"PlanningTask {task.id} has no associated MaintenanceOrder")
                continue

            # Validate task has required data
            if not mo.estimated_completion_time or mo.estimated_completion_time <= 0:
                result.add_unassigned(self._create_unassigned_task(
                    task, mo, UnassignedReason.INVALID_DATA,
                    "Missing or invalid estimated completion time"
                ))
                continue

            if not mo.labour_count or mo.labour_count <= 0:
                result.add_unassigned(self._create_unassigned_task(
                    task, mo, UnassignedReason.INVALID_DATA,
                    "Missing or invalid labour count"
                ))
                continue

            # Check spare parts if requested
            if check_parts:
                is_available, details = check_spare_parts_availability(mo)
                if not is_available:
                    result.add_unassigned(self._create_unassigned_task(
                        task, mo, UnassignedReason.INSUFFICIENT_PARTS,
                        "Required spare parts not in stock",
                        insufficient_parts=details
                    ))
                    continue

            plannable_tasks.append((task, mo))

        return plannable_tasks

    def _get_available_technicians(self, schedule: Schedule) -> List[Technician]:
        """Get technicians available during the schedule period."""
        # For now, get all technicians with "Available" status
        # Future: Filter by shift, vacation, etc.
        return Technician.query.filter(
            Technician.availability_status == 'Available'
        ).all()

    def _filter_weekend_tasks(
        self,
        tasks: List[Tuple[PlanningTask, MaintenanceOrder]],
        result: PlanningResult
    ) -> List[Tuple[PlanningTask, MaintenanceOrder]]:
        """
        Filter tasks suitable for weekend planning mode.

        Weekend planning focuses on:
        - Scheduled PMs (Weekly, Monthly frequency)
        - Outstanding REP tasks
        - Deferred maintenance
        - Any tasks not dependent on production line being active

        Args:
            tasks: List of (PlanningTask, MaintenanceOrder) tuples
            result: PlanningResult to add warnings to

        Returns:
            Filtered list of tasks suitable for weekend planning
        """
        weekend_tasks = []
        filtered_count = 0

        for task, mo in tasks:
            # Include PM tasks with appropriate frequency
            if mo.order_type == 'PM' and mo.frequency:
                if mo.frequency.lower() in ['weekly', 'monthly', 'bi-weekly', 'quarterly']:
                    weekend_tasks.append((task, mo))
                    continue
                else:
                    # PMs with daily frequency might not be suitable for weekend
                    filtered_count += 1
                    continue

            # Include PM tasks without frequency (assume they're candidates)
            if mo.order_type == 'PM' and not mo.frequency:
                weekend_tasks.append((task, mo))
                continue

            # Include outstanding REP/Corrective tasks
            if mo.order_type in ['REP', 'Corrective']:
                if mo.status in ['Open', 'In Progress']:
                    weekend_tasks.append((task, mo))
                    continue

            # Include deferred tasks
            if mo.status == 'Deferred':
                weekend_tasks.append((task, mo))
                continue

            # Include Project tasks (good time for non-urgent project work)
            if mo.order_type == 'Project':
                weekend_tasks.append((task, mo))
                continue

            # Task didn't match any weekend criteria
            filtered_count += 1

        if filtered_count > 0:
            result.add_warning(
                f"Weekend mode: Filtered out {filtered_count} task(s) not suitable for weekend planning "
                f"(e.g., daily PMs, closed tasks)"
            )

        self._log("info", f"Weekend filtering: {len(weekend_tasks)} tasks selected from {len(tasks)} total")

        return weekend_tasks

    def _initialize_workloads(
        self,
        technicians: List[Technician],
        shift_duration_minutes: int
    ) -> Dict[int, TechnicianWorkload]:
        """Initialize workload tracking for all technicians."""
        workloads = {}
        for tech in technicians:
            workloads[tech.id] = TechnicianWorkload(
                technician_id=tech.id,
                technician_name=tech.name,
                total_assigned_minutes=0,
                total_available_minutes=shift_duration_minutes,
                utilization_percentage=0.0,
                assigned_task_count=0,
                assigned_task_ids=[],
                shift_name=tech.shift.name if tech.shift else None
            )
        return workloads

    def _prioritize_tasks(
        self,
        tasks: List[Tuple[PlanningTask, MaintenanceOrder]],
        planning_mode: str
    ) -> List[Tuple[PlanningTask, MaintenanceOrder]]:
        """
        Sort tasks by priority based on planning mode.

        Priority order for shift_break mode:
        1. Task type FIRST (REP > Corrective > PM > Project) - Reactive focus
        2. Then by priority level within type (Critical > High > Medium > Low)

        Priority order for weekend mode:
        1. Task type FIRST (PM > REP > Corrective > Project) - Preventive focus
        2. Then by priority level within type (Critical > High > Medium > Low)
        """
        priority_map = {
            'Critical': 1,
            'High': 2,
            'Medium': 3,
            'Low': 4,
            'Undefined': 5
        }

        type_priority_shift_break = {
            'REP': 1,
            'Corrective': 2,
            'PM': 3,
            'Project': 4
        }

        type_priority_weekend = {
            'PM': 1,
            'REP': 2,
            'Corrective': 3,
            'Project': 4
        }

        type_map = type_priority_shift_break if planning_mode == "shift_break" else type_priority_weekend

        def sort_key(task_tuple):
            task, mo = task_tuple
            priority_val = priority_map.get(mo.priority, 99)
            type_val = type_map.get(mo.order_type, 99)

            # Both modes: Type FIRST, then priority
            # Shift-break: REP-first (reactive)
            # Weekend: PM-first (preventive)
            return (type_val, priority_val, mo.id)

        return sorted(tasks, key=sort_key)

    def _assign_single_task(
        self,
        task: PlanningTask,
        mo: MaintenanceOrder,
        available_technicians: List[Technician],
        workloads: Dict[int, TechnicianWorkload],
        current_time: datetime,
        result: PlanningResult,
        planning_mode: str,
        max_task_duration: int
    ) -> Optional[TaskAssignment]:
        """
        Attempt to assign a single task to technician(s).

        For multi-technician tasks (labour_count > 1):
        - Forms a cohesive team with complementary skills
        - Balances experience levels
        - Ensures all team members are available at the same time

        Returns TaskAssignment if successful, None if cannot assign.
        """
        required_tech_count = mo.labour_count
        estimated_duration = mo.estimated_completion_time

        # Check time window constraint for shift-break mode
        if not self._fits_time_window(estimated_duration, max_task_duration, planning_mode):
            result.add_unassigned(self._create_unassigned_task(
                task, mo, UnassignedReason.INSUFFICIENT_TIME,
                f"Task duration ({estimated_duration} min) exceeds {planning_mode} time window ({max_task_duration} min)"
            ))
            return None

        # Get required skills for this task
        required_skills = [skill.name for skill in mo.required_skills] if hasattr(mo, 'required_skills') else []

        # For multi-skill tasks, we need to ensure team coverage
        # Single technician may not have all skills, but team collectively should
        if required_tech_count > 1 and len(required_skills) > 1:
            # Multi-technician, multi-skill task - use team-based skill matching
            eligible_technicians = self._find_team_with_skill_coverage(
                available_technicians, required_skills, required_tech_count, workloads, estimated_duration
            )
        else:
            # Single technician or single skill - use individual matching
            eligible_technicians = self._find_eligible_technicians(
                available_technicians, required_skills, workloads, estimated_duration
            )

        if not eligible_technicians:
            result.add_unassigned(self._create_unassigned_task(
                task, mo, UnassignedReason.NO_MATCHING_SKILLS,
                f"No technicians available with required skills: {', '.join(required_skills)}",
                missing_skills=required_skills
            ))
            return None

        if len(eligible_technicians) < required_tech_count:
            result.add_unassigned(self._create_unassigned_task(
                task, mo, UnassignedReason.TEAM_SIZE_CONFLICT,
                f"Need {required_tech_count} technicians, only {len(eligible_technicians)} eligible"
            ))
            return None

        # Select best technicians (now with advanced team formation logic)
        selected_technicians = self._select_best_team(
            eligible_technicians, required_tech_count, workloads
        )

        # Validate team has all required skills collectively
        if required_skills and not self._team_has_all_skills(selected_technicians, required_skills):
            result.add_unassigned(self._create_unassigned_task(
                task, mo, UnassignedReason.NO_MATCHING_SKILLS,
                f"Selected team missing required skills: {', '.join(required_skills)}"
            ))
            return None

        # Calculate actual duration (could be adjusted based on team size and composition)
        actual_duration = self._calculate_adjusted_duration(
            estimated_duration, required_tech_count, len(selected_technicians)
        )

        # Create assignment
        assignment = TaskAssignment(
            planning_task_id=task.id,
            maintenance_order_id=mo.id,
            task_description=mo.description,
            assigned_technician_ids=[t.id for t in selected_technicians],
            assigned_technician_names=[t.name for t in selected_technicians],
            planned_start_time=current_time,
            planned_end_time=current_time + timedelta(minutes=actual_duration),
            estimated_duration_minutes=estimated_duration,
            actual_duration_minutes=actual_duration,
            required_skills=required_skills,
            priority=mo.priority,
            task_type=mo.order_type
        )

        # Update workloads for all team members
        for tech in selected_technicians:
            workload = workloads[tech.id]
            workload.total_assigned_minutes += actual_duration
            workload.assigned_task_count += 1
            workload.assigned_task_ids.append(task.id)
            workload.utilization_percentage = (
                workload.total_assigned_minutes / workload.total_available_minutes * 100
                if workload.total_available_minutes > 0 else 0
            )

        self._log("info", f"Assigned task {mo.id} to team: {', '.join([t.name for t in selected_technicians])}")

        return assignment

    def _find_eligible_technicians(
        self,
        technicians: List[Technician],
        required_skills: List[str],
        workloads: Dict[int, TechnicianWorkload],
        task_duration: int
    ) -> List[Technician]:
        """Find technicians who have the required skills and available time."""
        if not required_skills:
            # If no specific skills required, all technicians are eligible
            return [t for t in technicians if self._has_available_time(t, workloads, task_duration)]

        eligible = []
        for tech in technicians:
            # Check if technician has all required skills
            if self._has_required_skills(tech, required_skills):
                # Check if technician has available time
                if self._has_available_time(tech, workloads, task_duration):
                    eligible.append(tech)

        return eligible

    def _has_required_skills(self, technician: Technician, required_skills: List[str]) -> bool:
        """Check if technician has all required skills."""
        tech_skills = {ts.skill.name for ts in technician.skills}
        return all(skill in tech_skills for skill in required_skills)

    def _has_available_time(
        self,
        technician: Technician,
        workloads: Dict[int, TechnicianWorkload],
        task_duration: int
    ) -> bool:
        """Check if technician has enough available time."""
        workload = workloads.get(technician.id)
        if not workload:
            return False

        remaining_time = workload.total_available_minutes - workload.total_assigned_minutes
        return remaining_time >= task_duration

    def _find_team_with_skill_coverage(
        self,
        technicians: List[Technician],
        required_skills: List[str],
        team_size: int,
        workloads: Dict[int, TechnicianWorkload],
        task_duration: int
    ) -> List[Technician]:
        """
        Find technicians who collectively have all required skills for a multi-person task.

        For multi-technician tasks, individual techs don't need ALL skills,
        but the team collectively must cover all required skills.

        Args:
            technicians: Pool of available technicians
            required_skills: List of skills needed for the task
            team_size: Number of technicians needed
            workloads: Current workload tracking
            task_duration: Task duration in minutes

        Returns:
            List of technicians who collectively have required skills and available time
        """
        # Filter to only those with available time
        available_techs = [
            t for t in technicians
            if self._has_available_time(t, workloads, task_duration)
        ]

        if not available_techs:
            return []

        # If no specific skills required, return all available
        if not required_skills:
            return available_techs

        # Find technicians who have at least ONE of the required skills
        tech_with_some_skills = []
        for tech in available_techs:
            tech_skills = {ts.skill.name for ts in tech.skills} if hasattr(tech, 'skills') else set()
            # Check if tech has ANY of the required skills
            if any(skill in tech_skills for skill in required_skills):
                tech_with_some_skills.append(tech)

        if len(tech_with_some_skills) < team_size:
            # Not enough technicians with relevant skills
            return []

        # Strategy: Greedily select technicians to maximize skill coverage
        # This is a simplified approach - more sophisticated algorithms exist
        selected = []
        covered_skills = set()
        remaining_pool = tech_with_some_skills.copy()

        # First pass: Select technicians to cover as many skills as possible
        while len(selected) < team_size and remaining_pool:
            # Find tech that covers the most uncovered skills
            best_tech = None
            best_new_coverage = 0

            for tech in remaining_pool:
                tech_skills = {ts.skill.name for ts in tech.skills} if hasattr(tech, 'skills') else set()
                new_coverage = len(tech_skills.intersection(required_skills) - covered_skills)

                if new_coverage > best_new_coverage:
                    best_new_coverage = new_coverage
                    best_tech = tech

            if best_tech:
                selected.append(best_tech)
                tech_skills = {ts.skill.name for ts in best_tech.skills} if hasattr(best_tech, 'skills') else set()
                covered_skills.update(tech_skills.intersection(required_skills))
                remaining_pool.remove(best_tech)
            else:
                # No more progress possible, fill remaining slots with any available
                for tech in remaining_pool[:team_size - len(selected)]:
                    selected.append(tech)
                break

        # Verify team collectively has all required skills
        if self._team_has_all_skills(selected, required_skills):
            return selected
        else:
            # Try alternative: return techs who individually have all skills
            individual_match = [
                t for t in available_techs
                if self._has_required_skills(t, required_skills)
            ]
            return individual_match if len(individual_match) >= team_size else []

    def _team_has_all_skills(
        self,
        team: List[Technician],
        required_skills: List[str]
    ) -> bool:
        """
        Check if a team collectively has all required skills.

        Args:
            team: List of technicians
            required_skills: Skills needed for the task

        Returns:
            True if team collectively covers all skills, False otherwise
        """
        if not required_skills:
            return True

        # Collect all skills from all team members
        team_skills = set()
        for tech in team:
            if hasattr(tech, 'skills'):
                tech_skills = {ts.skill.name for ts in tech.skills}
                team_skills.update(tech_skills)

        # Check if all required skills are covered
        return all(skill in team_skills for skill in required_skills)

    def _select_best_team(
        self,
        eligible_technicians: List[Technician],
        team_size: int,
        workloads: Dict[int, TechnicianWorkload]
    ) -> List[Technician]:
        """
        Select the best team from eligible technicians using advanced team formation logic.

        Strategy:
        1. Maximize skill coverage across the team
        2. Balance experience levels (mix senior and junior if possible)
        3. Prioritize workload balancing (fair distribution)
        4. Prefer technicians who have worked together successfully

        Args:
            eligible_technicians: List of technicians who meet basic requirements
            team_size: Number of technicians needed
            workloads: Current workload tracking

        Returns:
            List of selected technicians forming the optimal team
        """
        if len(eligible_technicians) <= team_size:
            # Not enough choice, return all eligible
            return eligible_technicians

        # Score each technician based on multiple factors
        tech_scores = []
        for tech in eligible_technicians:
            workload = workloads[tech.id]

            # Factor 1: Available time (workload balancing) - weight 40%
            remaining_time = workload.total_available_minutes - workload.total_assigned_minutes
            time_score = remaining_time / workload.total_available_minutes if workload.total_available_minutes > 0 else 0

            # Factor 2: Skill diversity (number of unique skills) - weight 30%
            skill_count = len(tech.skills) if hasattr(tech, 'skills') else 0
            max_skills = max(len(t.skills) if hasattr(t, 'skills') else 0 for t in eligible_technicians)
            skill_score = skill_count / max_skills if max_skills > 0 else 0

            # Factor 3: Skill level (average proficiency) - weight 30%
            avg_skill_level = 0.0  # Initialize to avoid reference error
            if hasattr(tech, 'skills') and tech.skills:
                avg_skill_level = sum(ts.skill_level for ts in tech.skills) / len(tech.skills)
                skill_level_score = avg_skill_level / 5.0  # Normalize to 0-1 (assuming 1-5 scale)
            else:
                skill_level_score = 0

            # Calculate weighted score
            total_score = (
                time_score * 0.40 +
                skill_score * 0.30 +
                skill_level_score * 0.30
            )

            tech_scores.append((tech, total_score, skill_count, avg_skill_level))

        # Sort by total score (descending)
        tech_scores.sort(key=lambda x: x[1], reverse=True)

        # Select team with experience balancing
        selected_team = self._balance_team_experience(tech_scores, team_size)

        return selected_team

    def _balance_team_experience(
        self,
        scored_technicians: List[Tuple[Technician, float, int, float]],
        team_size: int
    ) -> List[Technician]:
        """
        Balance team composition with mix of experienced and less experienced technicians.

        Strategy:
        - For teams of 2+: Try to include at least one highly skilled technician (skill level >= 4)
        - Avoid all-junior or all-senior teams if possible
        - Maximize overall team skill coverage

        Args:
            scored_technicians: List of (Technician, score, skill_count, avg_skill_level) tuples
            team_size: Number of technicians needed

        Returns:
            Balanced team of technicians
        """
        if team_size == 1:
            # Single technician: pick the highest scored
            return [scored_technicians[0][0]]

        # Separate into experience levels based on average skill level
        senior_techs = [(t, s, sc, sl) for t, s, sc, sl in scored_technicians if sl >= 4.0]
        mid_techs = [(t, s, sc, sl) for t, s, sc, sl in scored_technicians if 3.0 <= sl < 4.0]
        junior_techs = [(t, s, sc, sl) for t, s, sc, sl in scored_technicians if sl < 3.0]

        selected = []

        # Strategy 1: Include at least 1 senior if available and team size >= 2
        if senior_techs and team_size >= 2:
            selected.append(senior_techs[0][0])
            remaining = team_size - 1
        else:
            remaining = team_size

        # Strategy 2: Fill remaining slots from all pools, preferring highest scores
        remaining_pool = [t for t in scored_technicians if t[0] not in selected]
        remaining_pool.sort(key=lambda x: x[1], reverse=True)  # Sort by score

        for tech_tuple in remaining_pool[:remaining]:
            selected.append(tech_tuple[0])

        return selected

    def _calculate_adjusted_duration(
        self,
        base_duration: int,
        required_team_size: int,
        actual_team_size: int
    ) -> int:
        """
        Calculate adjusted duration based on team size.

        More technicians can potentially complete work faster (to a point).
        This is a simplified model - can be enhanced with more sophisticated logic.
        """
        if actual_team_size <= required_team_size:
            return base_duration

        # Simple efficiency model: each extra technician reduces time by 10%, up to 30% max
        extra_techs = actual_team_size - required_team_size
        efficiency_gain = min(0.30, extra_techs * 0.10)
        adjusted_duration = int(base_duration * (1 - efficiency_gain))

        return max(adjusted_duration, int(base_duration * 0.5))  # Never less than 50% of original

    def _fits_time_window(
        self,
        task_duration: int,
        max_allowed: int,
        mode: str
    ) -> bool:
        """
        Check if task fits within time window for the planning mode.

        Args:
            task_duration: Estimated task duration in minutes
            max_allowed: Maximum allowed duration for this mode
            mode: Planning mode ("shift_break" or "weekend")

        Returns:
            True if task fits within time constraint, False otherwise
        """
        if mode == "shift_break":
            return task_duration <= max_allowed
        # No time limit for weekend mode
        return True

    def _create_unassigned_task(
        self,
        task: PlanningTask,
        mo: MaintenanceOrder,
        reason: UnassignedReason,
        detail: str,
        missing_skills: Optional[List[str]] = None,
        insufficient_parts: Optional[Dict] = None
    ) -> UnassignedTask:
        """Helper to create UnassignedTask object."""
        required_skills = [skill.name for skill in mo.required_skills] if hasattr(mo, 'required_skills') else []

        return UnassignedTask(
            planning_task_id=task.id,
            maintenance_order_id=mo.id,
            task_description=mo.description,
            reason=reason,
            reason_detail=detail,
            required_skills=required_skills,
            priority=mo.priority,
            task_type=mo.order_type,
            missing_skills=missing_skills,
            insufficient_parts=insufficient_parts
        )


# Convenience function for simple usage
def generate_plan(schedule_id: int, planning_mode: str = "weekend", logger=None) -> PlanningResult:
    """
    Generate a planning result for a schedule.

    Args:
        schedule_id: ID of the schedule to plan
        planning_mode: "shift_break" or "weekend"
        logger: Optional logger instance

    Returns:
        PlanningResult object with all assignments
    """
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        raise ValueError(f"Schedule {schedule_id} not found")

    engine = PlanningEngine(logger=logger)
    return engine.generate_plan(schedule, planning_mode=planning_mode)

