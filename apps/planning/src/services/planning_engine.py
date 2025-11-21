# apps/planning/src/services/planning_engine.py

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
import json
import os
from datetime import datetime, timedelta, time as dt_time
from typing import List, Tuple, Optional, Dict, Set
from collections import defaultdict
from dataclasses import dataclass

from src.services.db_utils import db, MaintenanceOrder, User, Skill, Team, UserSkill
from .planning_models import PlanningTask, Schedule
from .planning_result import (
    PlanningResult, TaskAssignment, UnassignedTask, TechnicianWorkload,
    UnassignedReason
)
from .inventory_service import check_spare_parts_availability


@dataclass
class ShiftDefinition:
    """Defines a specific shift instance."""
    name: str
    day_name: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    is_overnight: bool = False
    base_name: str = ""  # e.g., "early", "late"


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

    def _load_config(self) -> dict:
        """Load configuration from config.json or config.example.json."""
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config'))
        config_path = os.path.join(base_path, 'config.json')
        example_path = os.path.join(base_path, 'config.example.json')

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            elif os.path.exists(example_path):
                self._log("warning", "config.json not found, using config.example.json")
                with open(example_path, 'r') as f:
                    return json.load(f)
            else:
                self._log("error", "No configuration file found!")
                return {}
        except Exception as e:
            self._log("error", f"Failed to load config: {str(e)}")
            return {}

    def _parse_time_str(self, time_str: str) -> dt_time:
        """Parse HH:MM string to time object."""
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return dt_time(0, 0)

    def _get_weekend_shifts(self, start_date: datetime, end_date: datetime) -> List[ShiftDefinition]:
        """
        Generate specific shift instances for the given date range based on Shift Patterns.
        
        Args:
            start_date: The start date of the schedule
            end_date: The end date of the schedule
            
        Returns:
            List of ShiftDefinition objects ordered by time
        """
        config = self._load_config()
        
        # 1. Get Resource Pattern (default to maintenance)
        windows_config = config.get('planning_windows', {})
        window_def = windows_config.get('weekend_maintenance', {})
        pattern_name = window_def.get('resource_pattern', 'maintenance')
        
        patterns_config = config.get('shift_patterns', {})
        pattern_def = patterns_config.get(pattern_name, {})
        shifts_def = pattern_def.get('shifts', [])
        
        if not shifts_def:
            self._log("warning", f"No shifts defined for pattern '{pattern_name}'")
            return []

        generated_shifts = []
        
        # 2. Generate Shifts for the range
        curr_date = start_date.date()
        end_date_limit = end_date.date()
        
        while curr_date <= end_date_limit + timedelta(days=1): # +1 buffer for overnight
            for shift_data in shifts_def:
                s_start = self._parse_time_str(shift_data['start_time'])
                s_end = self._parse_time_str(shift_data['end_time'])
                
                # Construct absolute shift times for this day
                shift_start_dt = datetime.combine(curr_date, s_start)
                shift_end_dt = datetime.combine(curr_date, s_end)
                
                # Handle overnight shifts (e.g. 18:00 - 06:00)
                if shift_end_dt <= shift_start_dt:
                    shift_end_dt += timedelta(days=1)
                
                # 3. Intersect with Schedule Range
                inter_start = max(start_date, shift_start_dt)
                inter_end = min(end_date, shift_end_dt)
                
                if inter_start < inter_end:
                    # Valid overlap
                    duration = int((inter_end - inter_start).total_seconds() / 60)
                    
                    # Determine if overnight (crosses midnight)
                    is_overnight = inter_start.date() != inter_end.date()
                    
                    shift_name = f"{shift_start_dt.strftime('%A')} - {shift_data['name'].capitalize()}"
                    
                    generated_shifts.append(ShiftDefinition(
                        name=shift_name,
                        day_name=shift_start_dt.strftime('%A').lower(),
                        start_time=inter_start,
                        end_time=inter_end,
                        duration_minutes=duration,
                        is_overnight=is_overnight,
                        base_name=shift_data['name'].lower()
                    ))
            
            curr_date += timedelta(days=1)
            
        return sorted(generated_shifts, key=lambda s: s.start_time)

    def _get_working_teams(self, date: datetime) -> List:
        """
        Determine which shift teams are working for the given date based on 2-week rotation.
        
        Week 1 (Odd ISO Week Number): Team A (Early) and Team B (Late)
        Week 2 (Even ISO Week Number): Team C (Early) and Team D (Late)
        
        Args:
            date: The date to check
            
        Returns:
            List of Team objects that are active for this week
        """
        from src.services.db_utils import Team
        
        week_number = date.isocalendar()[1]
        is_odd_week = (week_number % 2) != 0
        
        if is_odd_week:
            # Pattern 1: Team A (Early) and Team B (Late)
            active_teams = Team.query.filter(Team.rotation_pattern == "Pattern 1").all()
        else:
            # Pattern 2: Team C (Early) and Team D (Late)
            active_teams = Team.query.filter(Team.rotation_pattern == "Pattern 2").all()
        
        self._log("info", f"Week {week_number} ({'Odd' if is_odd_week else 'Even'}): Active teams: {[t.name for t in active_teams]}")
        return active_teams

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
            shift_duration_minutes: Total available minutes per shift (used for utilization calc)
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
        self._log("info", f"Mode: {planning_mode}")

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
        self._log("info", f"Found {len(tasks_to_plan)} plannable tasks before mode filtering")

        # Apply mode-specific filtering
        if planning_mode == "weekend":
            self._log("info", f"Applying weekend mode filtering...")
            tasks_to_plan = self._filter_weekend_tasks(tasks_to_plan, result)
            self._log("info", f"After weekend filtering: {len(tasks_to_plan)} tasks remain")

        if not tasks_to_plan:
            result.add_warning("No plannable tasks found for this schedule")
            self._log("warning", f"Zero tasks to plan after filtering (mode={planning_mode})")
            result.calculate_statistics()
            result.statistics.planning_duration_seconds = time.time() - start_time
            return result

        # Get available technicians (Global pool)
        # We now use User model where team_id is not None
        all_technicians = self._get_available_technicians(schedule)

        if not all_technicians:
            result.add_error("No available technicians found")
            for task, mo in tasks_to_plan:
                result.add_unassigned(self._create_unassigned_task(
                    task, mo, UnassignedReason.NO_AVAILABLE_TECHNICIANS,
                    "No technicians are available for this planning period"
                ))
            result.calculate_statistics()
            result.statistics.planning_duration_seconds = time.time() - start_time
            return result

        self._log("info", f"Found {len(tasks_to_plan)} tasks and {len(all_technicians)} technicians")

        # Initialize workload tracking (Global across all shifts)
        # We use a default shift duration for utilization calc, but actual availability is per shift
        technician_workloads = self._initialize_workloads(
            all_technicians, shift_duration_minutes * 3 # Approx 3 days
        )

        # Sort tasks by priority
        sorted_tasks = self._prioritize_tasks(tasks_to_plan, planning_mode)
        unassigned_tasks = list(sorted_tasks) # Copy to track remaining

        # Define Shifts
        shifts = []
        if planning_mode == "weekend":
            shifts = self._get_weekend_shifts(schedule.start_date, schedule.end_date)
            self._log("info", f"Generated {len(shifts)} weekend shifts")
        else:
            # Create a single dummy shift for shift_break or other modes
            shifts = [ShiftDefinition(
                name="Standard",
                day_name="Day 1",
                start_time=schedule.start_date,
                end_time=schedule.end_date,
                duration_minutes=int((schedule.end_date - schedule.start_date).total_seconds() / 60)
            )]

        # Fetch all teams once
        all_teams = Team.query.all()
        from src.services.shift_utils import get_shift_teams

        # Iterate through shifts and assign tasks
        for shift in shifts:
            self._log("info", f"Planning for shift: {shift.name} ({shift.start_time} - {shift.end_time})")
            
            # Filter technicians by Shift Team (Rotation Logic)
            allowed_team_names = []
            
            # Determine query date (handle overnight shifts)
            query_date = shift.start_time
            if shift.start_time.hour < 6:
                query_date = shift.start_time - timedelta(days=1)
            
            # Get the teams working on this date
            early_team, late_team = get_shift_teams(query_date, all_teams)
            
            if planning_mode == "weekend":
                # For weekend mode, use the shift's base_name to determine Early/Late
                shift_type = shift.base_name.lower() # "early" or "late"
                
                allowed_teams = []
                if 'early' in shift_type and early_team:
                    allowed_teams.append(early_team)
                elif 'late' in shift_type and late_team:
                    allowed_teams.append(late_team)
                
                allowed_team_names = [t.name for t in allowed_teams]
            else:
                # For shift_break mode, determine Early/Late based on time of day
                # Early shift: 06:00-18:00, Late shift: 18:00-06:00
                shift_hour = shift.start_time.hour
                
                if 6 <= shift_hour < 18:
                    # Morning/Day shift - use Early team
                    allowed_team_names = [early_team.name] if early_team else []
                else:
                    # Evening/Night shift - use Late team
                    allowed_team_names = [late_team.name] if late_team else []
            
            self._log("info", f"Shift: {shift.name} -> Working Teams: {allowed_team_names}")

            # 3. Filter technicians
            shift_technicians = []
            for tech in all_technicians:
                # Strict enforcement: Tech MUST have a shift team assigned
                if not tech.team:
                    continue
                
                # Check if tech belongs to one of the allowed teams
                if tech.team.name in allowed_team_names:
                    shift_technicians.append(tech)
            
            self._log("info", f"Available technicians for {shift.name}: {len(shift_technicians)} ({', '.join([t.username for t in shift_technicians])})")

            if not shift_technicians:
                self._log("warning", f"No technicians found for shift {shift.name} (Required: {allowed_team_names})") 
            
            # Track which technicians are busy during this shift (boolean)
            # Each technician can only work on ONE task per shift (parallel execution)
            shift_tech_busy = {
                t.id: False for t in shift_technicians
            }

            current_time = shift.start_time
            
            # Try to assign remaining tasks
            tasks_assigned_in_shift = []
            
            for i, (task, mo) in enumerate(unassigned_tasks):
                # Skip if already assigned (shouldn't happen if we manage list correctly, but safety check)
                if task.id in [t.planning_task_id for t in result.assigned_tasks]:
                    continue

                # Attempt assignment
                assignment_result = self._assign_single_task(
                    task, mo, shift_technicians, technician_workloads,
                    current_time, result, planning_mode, max_task_duration,
                    shift_end_time=shift.end_time,
                    shift_tech_busy=shift_tech_busy
                )

                if assignment_result:
                    result.add_assignment(assignment_result)
                    tasks_assigned_in_shift.append((task, mo))
                    
                    # Update current time? 
                    # In a real Gantt, tasks are parallel. 
                    # Here we are simplifying: we just check if tech has time in the shift.
                    # The 'planned_start_time' might need to be smarter (finding first gap).
                    # For now, we set start time to shift start + offset? 
                    # Or just shift start if we assume parallel execution?
                    # The original code did: current_time = assignment_result.planned_end_time
                    # which implies sequential execution.
                    # Let's keep sequential for simplicity of 'current_time' but per-tech availability matters.
                    
                    # Actually, if we have multiple techs, they can work in parallel.
                    # But 'current_time' variable suggests a global cursor.
                    # Let's assume tasks start as early as possible.
                    # We need to find the earliest start time for the selected team.
                    pass

            # Remove assigned tasks from the master list
            for item in tasks_assigned_in_shift:
                if item in unassigned_tasks:
                    unassigned_tasks.remove(item)

        # Handle remaining unassigned tasks
        for task, mo in unassigned_tasks:
             result.add_unassigned(self._create_unassigned_task(
                task, mo, UnassignedReason.INSUFFICIENT_TIME,
                "Could not fit into any available shift"
            ))

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

    def _get_available_technicians(self, schedule: Schedule) -> List[User]:
        """Get technicians available during the schedule period."""
        # In the new schema, technicians are Users with a team_id
        # We also check availability_status
        return User.query.filter(
            User.team_id.isnot(None),
            User.availability_status == 'Available'
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
        filter_reasons = {}  # Track why tasks were filtered

        self._log("info", f"Weekend filtering: Processing {len(tasks)} tasks")

        for task, mo in tasks:
            # Include PM tasks with appropriate frequency
            if mo.order_type == 'PM' and mo.frequency:
                if mo.frequency.lower() in ['daily', 'weekly', 'monthly', 'bi-weekly', 'quarterly']:
                    weekend_tasks.append((task, mo))
                    self._log("debug", f"MO-{mo.id}: Included (PM with frequency={mo.frequency})")
                    continue
                else:
                    # PMs with unknown/unsupported frequency
                    filtered_count += 1
                    reason = f"PM with unsupported frequency ({mo.frequency})"
                    filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
                    self._log("debug", f"MO-{mo.id}: Filtered out (PM with frequency={mo.frequency})")
                    continue

            # Include PM tasks without frequency (assume they're candidates)
            if mo.order_type == 'PM' and not mo.frequency:
                weekend_tasks.append((task, mo))
                self._log("debug", f"MO-{mo.id}: Included (PM without frequency)")
                continue

            # Include outstanding REP/Corrective tasks
            if mo.order_type in ['REP', 'Corrective']:
                if mo.status in ['Open', 'In Progress']:
                    weekend_tasks.append((task, mo))
                    self._log("debug", f"MO-{mo.id}: Included (REP/Corrective, status={mo.status})")
                    continue
                else:
                    filtered_count += 1
                    reason = f"REP/Corrective with status {mo.status}"
                    filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
                    self._log("debug", f"MO-{mo.id}: Filtered out (REP/Corrective, status={mo.status})")
                    continue

            # Include deferred tasks
            if mo.status == 'Deferred':
                weekend_tasks.append((task, mo))
                self._log("debug", f"MO-{mo.id}: Included (Deferred)")
                continue

            # Include Project tasks (good time for non-urgent project work)
            if mo.order_type == 'Project':
                weekend_tasks.append((task, mo))
                self._log("debug", f"MO-{mo.id}: Included (Project)")
                continue

            # Task didn't match any weekend criteria
            filtered_count += 1
            reason = f"Type={mo.order_type}, Status={mo.status}, Freq={mo.frequency or 'None'}"
            filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
            self._log("debug", f"MO-{mo.id}: Filtered out (no weekend criteria match: {reason})")

        if filtered_count > 0:
            reason_summary = ", ".join([f"{count} {reason}" for reason, count in filter_reasons.items()])
            result.add_warning(
                f"Weekend mode: Filtered out {filtered_count} task(s): {reason_summary}"
            )

        self._log("info", f"Weekend filtering: {len(weekend_tasks)} tasks selected from {len(tasks)} total")

        return weekend_tasks

    def _initialize_workloads(
        self,
        technicians: List[User],
        shift_duration_minutes: int
    ) -> Dict[int, TechnicianWorkload]:
        """Initialize workload tracking for all technicians."""
        workloads = {}
        for tech in technicians:
            workloads[tech.id] = TechnicianWorkload(
                technician_id=tech.id,
                technician_name=tech.username,
                total_assigned_minutes=0,
                total_available_minutes=shift_duration_minutes,
                utilization_percentage=0.0,
                assigned_task_count=0,
                assigned_task_ids=[],
                shift_name=tech.team.name if tech.team else None
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
        available_technicians: List[User],
        workloads: Dict[int, TechnicianWorkload],
        current_time: datetime,
        result: PlanningResult,
        planning_mode: str,
        max_task_duration: int,
        shift_end_time: datetime = None,
        shift_tech_busy: Dict[int, bool] = None
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

        # Check time window constraint
        if not self._fits_time_window(estimated_duration, max_task_duration, planning_mode):
            result.add_unassigned(self._create_unassigned_task(
                task, mo, UnassignedReason.INSUFFICIENT_TIME,
                f"Task duration ({estimated_duration} min) exceeds time window ({max_task_duration} min)"
            ))
            return None

        # Check if task fits in shift window (parallel execution - all tasks start at shift.start_time)
        if shift_end_time:
            shift_duration_minutes = (shift_end_time - current_time).total_seconds() / 60
            if estimated_duration > shift_duration_minutes:
                # Task doesn't fit in the shift window at all
                return None

        # Get required skills for this task
        required_skills = [skill.name for skill in mo.required_skills] if hasattr(mo, 'required_skills') else []

        # For multi-skill tasks, we need to ensure team coverage
        # Single technician may not have all skills, but team collectively should
        if required_tech_count > 1 and len(required_skills) > 1:
            # Multi-technician, multi-skill task - use team-based skill matching
            eligible_technicians = self._find_team_with_skill_coverage(
                available_technicians, required_skills, required_tech_count, workloads, estimated_duration, shift_tech_busy
            )
        else:
            # Single technician or single skill - use individual matching
            eligible_technicians = self._find_eligible_technicians(
                available_technicians, required_skills, workloads, estimated_duration, shift_tech_busy
            )

        if not eligible_technicians:
            # Don't add unassigned error here if we are just trying a shift
            # The caller loop handles unassigned tasks at the end
            return None

        if len(eligible_technicians) < required_tech_count:
            return None

        # Select best technicians (now with advanced team formation logic)
        selected_technicians = self._select_best_team(
            eligible_technicians, required_tech_count, workloads
        )

        # Validate team has all required skills collectively
        if required_skills and not self._team_has_all_skills(selected_technicians, required_skills):
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
            assigned_technician_names=[t.username for t in selected_technicians],
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
            # Update global workload (for statistics and reporting)
            workload = workloads[tech.id]
            workload.total_assigned_minutes += actual_duration
            workload.assigned_task_count += 1
            workload.assigned_task_ids.append(task.id)
            workload.utilization_percentage = (
                workload.total_assigned_minutes / workload.total_available_minutes * 100
                if workload.total_available_minutes > 0 else 0
            )
            
            # Mark technician as busy for this shift (parallel execution)
            if shift_tech_busy is not None and tech.id in shift_tech_busy:
                shift_tech_busy[tech.id] = True

        self._log("info", f"Assigned task {mo.id} to team: {', '.join([t.username for t in selected_technicians])}")

        return assignment

    def _find_eligible_technicians(
        self,
        technicians: List[User],
        required_skills: List[str],
        workloads: Dict[int, TechnicianWorkload],
        task_duration: int,
        shift_tech_busy: Dict[int, bool] = None
    ) -> List[User]:
        """Find technicians who have the required skills and available time."""
        if not required_skills:
            # If no specific skills required, all technicians are eligible
            return [t for t in technicians if self._has_available_time(t, workloads, task_duration, shift_tech_busy)]

        eligible = []
        for tech in technicians:
            # Check if technician has all required skills
            if self._has_required_skills(tech, required_skills):
                # Check if technician has available time
                if self._has_available_time(tech, workloads, task_duration, shift_tech_busy):
                    eligible.append(tech)

        return eligible

    def _has_required_skills(self, technician: User, required_skills: List[str]) -> bool:
        """Check if technician has all required skills."""
        tech_skills = {ts.skill.name for ts in technician.skills}
        return all(skill in tech_skills for skill in required_skills)

    def _has_available_time(
        self,
        technician: User,
        workloads: Dict[int, TechnicianWorkload],
        task_duration: int,
        shift_tech_busy: Dict[int, bool] = None
    ) -> bool:
        """Check if technician has enough available time."""
        # Check if technician is already busy in this shift (parallel execution)
        if shift_tech_busy is not None:
            if technician.id in shift_tech_busy and shift_tech_busy[technician.id]:
                # Technician is already assigned to a task in this shift
                return False
        
        # Also check global workload (for multi-shift scenarios)
        workload = workloads.get(technician.id)
        if not workload:
            return False

        remaining_time = workload.total_available_minutes - workload.total_assigned_minutes
        return remaining_time >= task_duration

    def _find_team_with_skill_coverage(
        self,
        technicians: List[User],
        required_skills: List[str],
        team_size: int,
        workloads: Dict[int, TechnicianWorkload],
        task_duration: int,
        shift_tech_busy: Dict[int, bool] = None
    ) -> List[User]:
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
            if self._has_available_time(t, workloads, task_duration, shift_tech_busy)
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
        team: List[User],
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
        eligible_technicians: List[User],
        team_size: int,
        workloads: Dict[int, TechnicianWorkload]
    ) -> List[User]:
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
        scored_technicians: List[Tuple[User, float, int, float]],
        team_size: int
    ) -> List[User]:
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

