import json
import logging
import os
from datetime import datetime

from apps.planning.src.services.planning_models import PlanningTask, Schedule
from src.services.db_utils import MaintenanceOrder, db

logger = logging.getLogger(__name__)


def _load_dummy_data():
    """Load and parse the dummy data JSON file."""
    try:
        # Assuming we are in apps/planning/src/services/seeding.py
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
        logger.error(f"Dummy data file not found at {dummy_data_path}")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {dummy_data_path}")
    except Exception as e:
        logger.error(f"Unexpected error loading dummy data: {e}")
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
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("Checking if Planning database needs to be populated.")
    try:
        if Schedule.query.first():
            logger.info(
                "Planning database already contains data. Skipping main population."
            )
            return  # Already seeded

        logger.info("Populating Planning database with dummy data.")
        data = _load_dummy_data()
        if not data:
            logger.warning("No dummy data found for Planning App.")
            return

        schedules_data = data.get("schedules", [])
        if not schedules_data:
            logger.warning("No schedules data found in dummy_data.json.")
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

        logger.info(f"Loaded {schedule_count} schedules.")
        logger.info(f"Processed {task_count} planning tasks.")
        logger.info("Planning App dummy data population complete.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding Planning App data: {e}", exc_info=True)
