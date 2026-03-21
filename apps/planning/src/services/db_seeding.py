import json
import logging
import os
from datetime import datetime

from flask import current_app

from apps.planning.src.services.planning_db_utils import (
    get_db_connection,
    init_db,
)
from apps.planning.src.services.planning_db_utils import (
    populate_dummy_data as populate_planning_dummy_data,
)
from apps.planning.src.services.planning_models import PlanningTask, Schedule
from src.services.db_utils import MaintenanceOrder, db

logger = logging.getLogger(__name__)


_PLANNING_SEED_PREFIX = "[SEED][PLANNING]"


class _PlanningSeedLoggerAdapter(logging.LoggerAdapter):
    """Attach a stable planning seeding prefix to log messages."""

    def process(self, msg, kwargs):
        return f"{self.extra['seed_prefix']} {msg}", kwargs


def _get_planning_seed_logger(base_logger):
    """Return a logger that prefixes planning seeding messages consistently."""
    if (
        isinstance(base_logger, logging.LoggerAdapter)
        and base_logger.extra.get("seed_prefix") == _PLANNING_SEED_PREFIX
    ):
        return base_logger
    return _PlanningSeedLoggerAdapter(
        base_logger,
        {"seed_prefix": _PLANNING_SEED_PREFIX},
    )


def _load_dummy_data(log=None):
    """Load and parse the dummy data JSON file."""
    log = _get_planning_seed_logger(log or logger)
    dummy_data_path = ""
    try:
        # Assuming we are in apps/planning/src/services/db_seeding.py
        # Test data is at root/test_data/dummy_data.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up: services -> src -> planning -> apps -> root
        dummy_data_path = os.path.join(
            current_dir, "..", "..", "..", "..", "test_data", "dummy_data.json"
        )
        dummy_data_path = os.path.normpath(dummy_data_path)

        if not os.path.exists(dummy_data_path):
            # Fallback try relative to CWD if running from root
            dummy_data_path = os.path.abspath("test_data/dummy_data.json")

        with open(dummy_data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        log.error(f"Dummy data file not found at {dummy_data_path}")
    except json.JSONDecodeError:
        log.error(f"Error decoding JSON from {dummy_data_path}")
    except Exception as e:
        log.error(f"Unexpected error loading dummy data: {e}")
    return None


def _get_or_create(model, **kwargs):
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        return instance, True


def seed_planning_data(logger=None):
    """Seeds the Planning App data if not already present."""
    base_logger = logger or logging.getLogger(__name__)
    log = _get_planning_seed_logger(base_logger)

    # Ensure planning DB table structure exists (raw SQLite)
    try:
        planning_bind = current_app.config.get("SQLALCHEMY_BINDS", {}).get("planning")
        if planning_bind and planning_bind.startswith("sqlite:///"):
            db_path = planning_bind.replace("sqlite:///", "")
            # Ensure tables exist (including 'tasks')
            init_db(db_path, logger=base_logger)

            # Optionally populate raw dummy data for satellite points, etc.
            # This is safe as it uses get_or_create logic
            conn = get_db_connection(db_path)
            populate_planning_dummy_data(conn, base_logger)
            conn.close()

    except Exception as e:
        log.error(f"Error initializing Planning App raw DB structure: {e}")

    log.info("Checking if Planning database needs to be populated.")
    try:
        if Schedule.query.first():
            log.info(
                "Planning database already contains data. Skipping main population."
            )
            return  # Already seeded

        log.info("Populating Planning database with dummy data.")
        data = _load_dummy_data(log)
        if not data:
            log.warning("No dummy data found for Planning App.")
            return

        schedules_data = data.get("schedules", [])
        if not schedules_data:
            log.warning("No schedules data found in dummy_data.json.")
            return

        schedule_count = 0
        task_count = 0
        for sched_info in schedules_data:
            start_date = datetime.strptime(
                sched_info["start_date"], "%Y-%m-%dT%H:%M:%S"
            )
            end_date = datetime.strptime(sched_info["end_date"], "%Y-%m-%dT%H:%M:%S")

            schedule, created = _get_or_create(
                Schedule,
                name=sched_info["name"],
                start_date=start_date,
                end_date=end_date,
            )
            if created:
                schedule.planning_status = sched_info.get("planning_status", "Draft")
                schedule_count += 1

                # Link MOs to this schedule
                mo_list = sched_info.get("maintenance_orders", [])
                for mo_ref in mo_list:
                    # Prefer title matching (stable, concise), then fallback to
                    # description exact. Keep description-prefix fallback for
                    # backward compatibility with older seed references.
                    mo = (
                        db.session.query(MaintenanceOrder)
                        .filter_by(title=mo_ref)
                        .first()
                    )
                    if not mo:
                        mo = (
                            db.session.query(MaintenanceOrder)
                            .filter_by(description=mo_ref)
                            .first()
                        )
                    if not mo:
                        mo = (
                            db.session.query(MaintenanceOrder)
                            .filter(MaintenanceOrder.description.startswith(mo_ref))
                            .first()
                        )
                    if mo:
                        # Create PlanningTask
                        pt = PlanningTask(
                            maintenance_order_id=mo.id,
                            schedule_id=schedule.id,
                            status="Unplanned",
                        )
                        db.session.add(pt)
                        task_count += 1

        db.session.commit()

        log.info(f"Loaded {schedule_count} schedules.")
        log.info(f"Processed {task_count} planning tasks.")
        log.info("Planning App dummy data population complete.")
    except Exception as e:
        db.session.rollback()
        log.error(f"Error seeding Planning App data: {e}", exc_info=True)
