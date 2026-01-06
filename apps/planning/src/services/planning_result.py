# apps/planning/src/services/planning_result.py
"""Planning Result Data Structures.

This module defines the data structures returned by the planning engine. It provides a
clear, structured format for assignment results, unassigned tasks, and metadata about
the planning run.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class UnassignedReason(Enum):
    """Enumeration of reasons why a task could not be assigned."""

    NO_MATCHING_SKILLS = "no_matching_skills"
    INSUFFICIENT_PARTS = "insufficient_parts"
    NO_AVAILABLE_TECHNICIANS = "no_available_technicians"
    INSUFFICIENT_TIME = "insufficient_time"
    INVALID_DATA = "invalid_data"
    TEAM_SIZE_CONFLICT = "team_size_conflict"
    WORKLOAD_LIMIT_EXCEEDED = "workload_limit_exceeded"


@dataclass
class TaskAssignment:
    """Represents a successfully assigned task."""

    planning_task_id: int
    maintenance_order_id: int
    task_description: str
    assigned_technician_ids: List[int]
    assigned_technician_names: List[str]
    planned_start_time: datetime
    planned_end_time: datetime
    estimated_duration_minutes: int
    actual_duration_minutes: int  # May differ due to team size optimization
    required_skills: List[str]
    priority: str
    task_type: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "planning_task_id": self.planning_task_id,
            "maintenance_order_id": self.maintenance_order_id,
            "task_description": self.task_description,
            "assigned_technician_ids": self.assigned_technician_ids,
            "assigned_technician_names": self.assigned_technician_names,
            "planned_start_time": self.planned_start_time.isoformat(),
            "planned_end_time": self.planned_end_time.isoformat(),
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "actual_duration_minutes": self.actual_duration_minutes,
            "required_skills": self.required_skills,
            "priority": self.priority,
            "task_type": self.task_type,
        }


@dataclass
class UnassignedTask:
    """Represents a task that could not be assigned."""

    planning_task_id: int
    maintenance_order_id: int
    task_description: str
    reason: UnassignedReason
    reason_detail: str  # Human-readable explanation
    required_skills: List[str]
    priority: str
    task_type: str
    missing_skills: Optional[List[str]] = None
    insufficient_parts: Optional[Dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "planning_task_id": self.planning_task_id,
            "maintenance_order_id": self.maintenance_order_id,
            "task_description": self.task_description,
            "reason": self.reason.value,
            "reason_detail": self.reason_detail,
            "required_skills": self.required_skills,
            "priority": self.priority,
            "task_type": self.task_type,
            "missing_skills": self.missing_skills,
            "insufficient_parts": self.insufficient_parts,
        }


@dataclass
class TechnicianWorkload:
    """Represents a technician's workload summary."""

    technician_id: int
    technician_name: str
    total_assigned_minutes: int
    total_available_minutes: int
    utilization_percentage: float
    assigned_task_count: int
    assigned_task_ids: List[int]
    shift_name: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "technician_id": self.technician_id,
            "technician_name": self.technician_name,
            "total_assigned_minutes": self.total_assigned_minutes,
            "total_available_minutes": self.total_available_minutes,
            "utilization_percentage": round(self.utilization_percentage, 2),
            "assigned_task_count": self.assigned_task_count,
            "assigned_task_ids": self.assigned_task_ids,
            "shift_name": self.shift_name,
        }


@dataclass
class PlanningStatistics:
    """Overall statistics about the planning run."""

    total_tasks: int
    assigned_tasks: int
    unassigned_tasks: int
    assignment_success_rate: float
    total_technicians: int
    utilized_technicians: int
    average_utilization: float
    planning_duration_seconds: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_tasks": self.total_tasks,
            "assigned_tasks": self.assigned_tasks,
            "unassigned_tasks": self.unassigned_tasks,
            "assignment_success_rate": round(self.assignment_success_rate, 2),
            "total_technicians": self.total_technicians,
            "utilized_technicians": self.utilized_technicians,
            "average_utilization": round(self.average_utilization, 2),
            "planning_duration_seconds": round(self.planning_duration_seconds, 3),
        }


@dataclass
class PlanningResult:
    """Complete result of a planning run.

    This is the primary output structure of the planning engine. It contains all
    assignments, unassigned tasks, workload summaries, and metadata.
    """

    schedule_id: int
    schedule_name: str
    planning_mode: str  # "shift_break" or "weekend"
    start_date: datetime
    end_date: datetime
    created_at: datetime

    assigned_tasks: List[TaskAssignment] = field(default_factory=list)
    unassigned_tasks: List[UnassignedTask] = field(default_factory=list)
    technician_workloads: List[TechnicianWorkload] = field(default_factory=list)
    statistics: Optional[PlanningStatistics] = None

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert entire result to dictionary for JSON serialization."""
        return {
            "schedule_id": self.schedule_id,
            "schedule_name": self.schedule_name,
            "planning_mode": self.planning_mode,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "assigned_tasks": [task.to_dict() for task in self.assigned_tasks],
            "unassigned_tasks": [task.to_dict() for task in self.unassigned_tasks],
            "technician_workloads": [wl.to_dict() for wl in self.technician_workloads],
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "warnings": self.warnings,
            "errors": self.errors,
        }

    def add_assignment(self, assignment: TaskAssignment):
        """Add a successful assignment to the result."""
        self.assigned_tasks.append(assignment)

    def add_unassigned(self, unassigned: UnassignedTask):
        """Add an unassigned task to the result."""
        self.unassigned_tasks.append(unassigned)

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)

    def calculate_statistics(self):
        """Calculate and set planning statistics based on current assignments."""
        total_tasks = len(self.assigned_tasks) + len(self.unassigned_tasks)
        assigned_count = len(self.assigned_tasks)
        unassigned_count = len(self.unassigned_tasks)

        success_rate = (assigned_count / total_tasks * 100) if total_tasks > 0 else 0

        total_techs = len(self.technician_workloads)
        utilized_techs = len(
            [wl for wl in self.technician_workloads if wl.assigned_task_count > 0]
        )
        avg_utilization = (
            sum(wl.utilization_percentage for wl in self.technician_workloads)
            / total_techs
            if total_techs > 0
            else 0
        )

        self.statistics = PlanningStatistics(
            total_tasks=total_tasks,
            assigned_tasks=assigned_count,
            unassigned_tasks=unassigned_count,
            assignment_success_rate=success_rate,
            total_technicians=total_techs,
            utilized_technicians=utilized_techs,
            average_utilization=avg_utilization,
            planning_duration_seconds=0,  # Will be set by the engine
        )
