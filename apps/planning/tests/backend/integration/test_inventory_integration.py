# apps/planning/tests/test_inventory_integration.py

import pytest

from apps.planning.src.services.inventory_service import (
    check_spare_parts_availability,
    get_tasks_with_insufficient_parts,
)
from src.services.db_utils import (
    MaintenanceOrder,
    SparePart,
    db,
    maintenance_order_spare_parts,
)


@pytest.fixture
def app_context_inventory():
    """Creates a temporary, in-memory SQLite database for inventory tests."""
    from flask import Flask

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_BINDS"] = {
        "planning": "sqlite:///:memory:",
        "reporting": "sqlite:///:memory:",
    }
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Seed data
        part1 = SparePart(id=1, description="Filter A", stock_quantity=10)
        part2 = SparePart(id=2, description="Bearing B", stock_quantity=2)
        part3 = SparePart(id=3, description="Seal C", stock_quantity=0)

        mo1 = MaintenanceOrder(
            id=101,
            asset_id=1,
            description="Task with sufficient parts",
            order_type="PM",
        )
        mo2 = MaintenanceOrder(
            id=102,
            asset_id=1,
            description="Task with insufficient parts",
            order_type="PM",
        )
        mo3 = MaintenanceOrder(
            id=103,
            asset_id=1,
            description="Task with zero stock parts",
            order_type="PM",
        )
        mo4 = MaintenanceOrder(
            id=104,
            asset_id=1,
            description="Task with no parts required",
            order_type="PM",
        )

        db.session.add_all([part1, part2, part3, mo1, mo2, mo3, mo4])
        db.session.commit()

        # Link parts to MOs
        db.session.execute(
            maintenance_order_spare_parts.insert().values(
                maintenance_order_id=101, spare_part_id=1, quantity_required=5
            )
        )
        db.session.execute(
            maintenance_order_spare_parts.insert().values(
                maintenance_order_id=102, spare_part_id=2, quantity_required=3
            )
        )
        db.session.execute(
            maintenance_order_spare_parts.insert().values(
                maintenance_order_id=103, spare_part_id=3, quantity_required=1
            )
        )
        db.session.commit()

        yield app
        db.drop_all()


def test_check_parts_sufficient(app_context_inventory):
    """Test when all parts are available in sufficient quantity."""
    mo = db.session.get(MaintenanceOrder, 101)
    is_available, details = check_spare_parts_availability(mo)

    assert is_available is True
    assert details[1]["sufficient"] is True
    assert details[1]["required"] == 5
    assert details[1]["available"] == 10


def test_check_parts_insufficient(app_context_inventory):
    """Test when a part is available but in insufficient quantity."""
    mo = db.session.get(MaintenanceOrder, 102)
    is_available, details = check_spare_parts_availability(mo)

    assert is_available is False
    assert details[2]["sufficient"] is False
    assert details[2]["required"] == 3
    assert details[2]["available"] == 2


def test_check_parts_zero_stock(app_context_inventory):
    """Test when a required part has zero stock."""
    mo = db.session.get(MaintenanceOrder, 103)
    is_available, details = check_spare_parts_availability(mo)

    assert is_available is False
    assert details[3]["sufficient"] is False
    assert details[3]["required"] == 1
    assert details[3]["available"] == 0


def test_check_no_parts_required(app_context_inventory):
    """Test a maintenance order that requires no spare parts."""
    mo = db.session.get(MaintenanceOrder, 104)
    is_available, details = check_spare_parts_availability(mo)

    assert is_available is True
    assert len(details) == 0


def test_get_tasks_with_insufficient_parts(app_context_inventory):
    """Test the filtering of tasks based on part availability."""
    all_mos = MaintenanceOrder.query.all()
    unplannable_tasks = get_tasks_with_insufficient_parts(all_mos)

    assert len(unplannable_tasks) == 2
    assert 101 not in unplannable_tasks
    assert 104 not in unplannable_tasks

    assert 102 in unplannable_tasks
    assert unplannable_tasks[102][2]["sufficient"] is False

    assert 103 in unplannable_tasks
    assert unplannable_tasks[103][3]["sufficient"] is False
