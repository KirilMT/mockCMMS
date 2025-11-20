# apps/workforceManager/src/services/data_transformation.py

from src.services.db_utils import MaintenanceOrder
from .planning_models import PlanningTask

def transform_mo_to_planning_task(maintenance_order: MaintenanceOrder) -> PlanningTask:
    """
    Transforms a MaintenanceOrder object from the main CMMS database into a
    PlanningTask domain object for the planning engine.
    """
    if not isinstance(maintenance_order, MaintenanceOrder):
        raise TypeError("Input must be a MaintenanceOrder object.")

    # Basic mapping
    planning_task = PlanningTask(
        maintenance_order_id=maintenance_order.id,
        # The following fields will be populated by the planning engine
        schedule_id=None,
        planned_start_time=None,
        planned_end_time=None,
        status='Unplanned',
        assigned_technician_id=None
    )

    # Here you would include more complex mapping logic, for example:
    # - Deriving priority
    # - Validating required fields
    # - etc.

    return planning_task

def validate_task_data(planning_task: PlanningTask, maintenance_order: MaintenanceOrder) -> (bool, list):
    """
    Validates that a PlanningTask has all the necessary data to be scheduled.
    Returns a tuple of (is_valid, error_messages).
    """
    errors = []
    if not maintenance_order.estimated_completion_time or maintenance_order.estimated_completion_time <= 0:
        errors.append(f"Task ID {planning_task.maintenance_order_id}: Missing or invalid 'estimated_completion_time'.")

    if not maintenance_order.labour_count or maintenance_order.labour_count <= 0:
        errors.append(f"Task ID {planning_task.maintenance_order_id}: Missing or invalid 'labour_count'.")

    # Add more validation rules as needed
    # e.g., check for required skills, asset information, etc.

    is_valid = len(errors) == 0
    return is_valid, errors

