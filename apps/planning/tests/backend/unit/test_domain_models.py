# apps/planning/tests/test_domain_models.py

from datetime import datetime

import pytest

from apps.planning.src.services.planning_models import PlanningTask, Schedule
from src.services.db_utils import (
    MaintenanceOrder,
    SparePart,
    db,
    maintenance_order_spare_parts,
)


@pytest.fixture
def app_context(request):
    """Creates a temporary, in-memory SQLite database for testing."""
    from flask import Flask

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_BINDS"] = {
        "planning": "sqlite:///:memory:",
        "reports": "sqlite:///:memory:",
    }
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_schedule_and_planning_task_models(app_context):
    """Test Schedule and PlanningTask models and their relationship."""
    # Need a dummy MaintenanceOrder to link to
    mo = MaintenanceOrder(
        description="Test MO", order_type="PM", asset_id=1
    )  # Added asset_id
    db.session.add(mo)
    db.session.commit()

    schedule = Schedule(
        name="Weekend Plan",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 3),
    )
    db.session.add(schedule)
    db.session.commit()

    planning_task = PlanningTask(
        maintenance_order_id=mo.id, schedule_id=schedule.id, status="Planned"
    )
    db.session.add(planning_task)
    db.session.commit()

    retrieved_schedule = Schedule.query.first()
    assert retrieved_schedule is not None
    assert len(retrieved_schedule.planned_tasks) == 1
    assert retrieved_schedule.planned_tasks[0].status == "Planned"
    assert (
        retrieved_schedule.planned_tasks[0].maintenance_order.description == "Test MO"
    )


def test_spare_part_mo_relationship(app_context):
    """Test the many-to-many relationship between MaintenanceOrder and SparePart."""
    mo = MaintenanceOrder(
        description="Install new motor", order_type="Corrective", asset_id=1
    )  # Added asset_id
    part = SparePart(description="Motor XYZ", stock_quantity=10)
    db.session.add_all([mo, part])
    db.session.commit()

    # Use the association table helper to link them
    statement = maintenance_order_spare_parts.insert().values(
        maintenance_order_id=mo.id, spare_part_id=part.id, quantity_required=2
    )
    db.session.execute(statement)
    db.session.commit()

    retrieved_mo = MaintenanceOrder.query.first()
    assert retrieved_mo is not None
    # To access the relationship, we need to query it properly
    assert len(retrieved_mo.required_spare_parts) == 1
    assert retrieved_mo.required_spare_parts[0].description == "Motor XYZ"

    retrieved_part = SparePart.query.first()
    assert len(retrieved_part.maintenance_orders) == 1
    assert retrieved_part.maintenance_orders[0].description == "Install new motor"


# def test_technician_model(app_context):
#     """Test the Technician model fields and relationships."""
#     # Models not yet implemented in SQLAlchemy
#     pass
#
#
# def test_technician_skill_model(app_context):
#     """Test the TechnicianSkill association model."""
#     # Models not yet implemented in SQLAlchemy
#     pass
