import json
import logging
import os
from datetime import datetime, timedelta, timezone

from apps.reports.src.models import Incident
from src.services.db_utils import db

logger = logging.getLogger(__name__)


def _load_dummy_data():
    """Load and parse the dummy data JSON file locally for Reports app."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # services -> src -> reports -> apps
        dummy_data_path = os.path.join(
            current_dir, "..", "..", "test_data", "dummy_data.json"
        )
        dummy_data_path = os.path.normpath(dummy_data_path)

        if not os.path.exists(dummy_data_path):
            logger.warning(f"Dummy data file not found at {dummy_data_path}")
            return None

        with open(dummy_data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading Reports dummy data: {e}")
    return None


def _get_or_create_incident(data):
    """Helper to get or create an incident based on description and timestamp.

    Uses description and incident_type as keys.
    """
    # Since timestamp is dynamic, we use description and incident_type as key
    instance = Incident.query.filter_by(
        description=data["description"], incident_type=data["incident_type"]
    ).first()

    if instance:
        return instance, False

    # Calculate timestamp based on days_ago
    days_ago = data.get("days_ago", 0)
    timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)

    instance = Incident(
        incident_type=data["incident_type"],
        equipment_line=data["equipment_line"],
        description=data["description"],
        severity=data["severity"],
        technician_name=data["technician_name"],
        timestamp=timestamp,
        resolved=data.get("resolved", False),
        resolution_notes=data.get("resolution_notes"),
    )
    db.session.add(instance)
    return instance, True


def seed_reports_data(app_logger=None):
    """Seeds the Reports App data if not already present."""
    log = app_logger or logger

    log.info("Checking if Reports database needs to be populated.")
    try:
        if Incident.query.first():
            log.info("Reports database already contains data. Skipping seeding.")
            return

        data = _load_dummy_data()
        if not data or "incidents" not in data:
            log.warning("No incident dummy data found for Reports App.")
            return

        log.info("Populating Reports database with modular dummy data.")
        count = 0
        for item in data["incidents"]:
            _, created = _get_or_create_incident(item)
            if created:
                count += 1

        db.session.commit()
        log.info(f"Successfully seeded {count} incidents for Reports App.")
    except Exception as e:
        db.session.rollback()
        log.error(f"Error seeding Reports App data: {e}", exc_info=True)
