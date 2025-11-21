# apps/planning/src/services/inventory_service.py

from sqlalchemy import select
from src.services.db_utils import MaintenanceOrder, SparePart, db, maintenance_order_spare_parts

def check_spare_parts_availability(maintenance_order: MaintenanceOrder) -> (bool, dict):
    """
    Checks the stock levels for all spare parts required by a maintenance order.

    Args:
        maintenance_order: The MaintenanceOrder object to check.

    Returns:
        A tuple containing:
        - bool: True if all parts are available in sufficient quantity, False otherwise.
        - dict: A dictionary detailing the status of each required part.
                e.g., {'part_id': {'required': 2, 'available': 5, 'sufficient': True}}
    """
    if not maintenance_order.required_spare_parts:
        return True, {}

    availability_status = {}
    all_parts_sufficient = True

    # Query the association table to get quantity_required information
    for part in maintenance_order.required_spare_parts:
        # Get the quantity required from the association table
        stmt = select(maintenance_order_spare_parts.c.quantity_required).where(
            maintenance_order_spare_parts.c.maintenance_order_id == maintenance_order.id,
            maintenance_order_spare_parts.c.spare_part_id == part.id
        )
        result = db.session.execute(stmt).scalar()
        required = result if result is not None else 0

        available = part.stock_quantity

        is_sufficient = available >= required
        if not is_sufficient:
            all_parts_sufficient = False

        availability_status[part.id] = {
            'description': part.description,
            'required': required,
            'available': available,
            'sufficient': is_sufficient
        }

    return all_parts_sufficient, availability_status

def get_tasks_with_insufficient_parts(tasks: list[MaintenanceOrder]) -> dict:
    """
    Filters a list of maintenance orders and returns a dictionary of tasks
    that cannot be planned due to insufficient spare parts.

    Args:
        tasks: A list of MaintenanceOrder objects.

    Returns:
        A dictionary where keys are maintenance order IDs and values are the
        detailed availability status for that order's parts.
    """
    unplannable_tasks = {}
    for task in tasks:
        is_available, details = check_spare_parts_availability(task)
        if not is_available:
            unplannable_tasks[task.id] = details

    return unplannable_tasks

