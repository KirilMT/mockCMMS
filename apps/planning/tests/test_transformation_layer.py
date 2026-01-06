# apps/planning/tests/test_transformation_layer.py

import pytest
from src.services.db_utils import MaintenanceOrder
from apps.planning.src.services.data_transformation import (
    transform_mo_to_planning_task,
    validate_task_data,
)


def test_transform_mo_to_planning_task_success():
    """Test successful transformation of a MaintenanceOrder to a PlanningTask."""
    mo = MaintenanceOrder(
        id=101,
        description="Monthly checkup",
        estimated_completion_time=120,
        labour_count=2,
    )

    planning_task = transform_mo_to_planning_task(mo)

    assert planning_task is not None
    assert planning_task.maintenance_order_id == 101
    assert planning_task.status == "Unplanned"
    assert planning_task.schedule_id is None
    assert planning_task.assigned_technician_id is None


def test_transform_mo_to_planning_task_type_error():
    """Test that a TypeError is raised for invalid input."""
    with pytest.raises(TypeError):
        transform_mo_to_planning_task({"id": 1, "description": "Not a real MO"})


def test_validate_task_data_valid():
    """Test validation with a valid MaintenanceOrder."""
    mo = MaintenanceOrder(id=102, estimated_completion_time=60, labour_count=1)
    planning_task = transform_mo_to_planning_task(mo)

    is_valid, errors = validate_task_data(planning_task, mo)

    assert is_valid is True
    assert len(errors) == 0


def test_validate_task_data_invalid_time():
    """Test validation with missing estimated completion time."""
    mo = MaintenanceOrder(id=103, labour_count=1)
    planning_task = transform_mo_to_planning_task(mo)

    is_valid, errors = validate_task_data(planning_task, mo)

    assert is_valid is False
    assert len(errors) == 1
    assert "Missing or invalid 'estimated_completion_time'" in errors[0]


def test_validate_task_data_invalid_labour():
    """Test validation with zero labour count."""
    mo = MaintenanceOrder(id=104, estimated_completion_time=30, labour_count=0)
    planning_task = transform_mo_to_planning_task(mo)

    is_valid, errors = validate_task_data(planning_task, mo)

    assert is_valid is False
    assert len(errors) == 1
    assert "Missing or invalid 'labour_count'" in errors[0]


def test_validate_task_data_multiple_errors():
    """Test validation with multiple missing fields."""
    mo = MaintenanceOrder(id=105)
    planning_task = transform_mo_to_planning_task(mo)

    is_valid, errors = validate_task_data(planning_task, mo)

    assert is_valid is False
    assert len(errors) == 2
