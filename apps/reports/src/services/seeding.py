import json
import logging
import os

from apps.reports.src.models import Report
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


def seed_reports_data(app_logger=None):
    """Seeds the Reports App data if not already present."""
    log = app_logger or logger

    log.info("Checking if Reports database needs to be populated.")

    # Check if table exists first (in case of fresh install)
    try:
        if Report.query.first():
            log.info("Reports database already contains data. Skipping population.")
            return
    except Exception as e:
        log.warning(f"Report table query failed (might not exist yet): {e}")
        return

    log.info("Populating Reports database with dummy data.")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # apps/reports/src/services -> apps/reports/test_data/dummy_data.json
        dummy_path = os.path.join(
            current_dir, "..", "..", "test_data", "dummy_data.json"
        )

        if not os.path.exists(dummy_path):
            log.warning(f"Reports dummy data not found: {dummy_path}")
            return

        with open(dummy_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        reports_list = data.get("reports", [])

        for r_data in reports_list:
            report = Report(
                title=r_data["title"],
                report_type=r_data["report_type"],
                parameters=r_data["parameters"],
                data=r_data["data"],
                generated_by=1,  # System/Admin
            )
            db.session.add(report)

        db.session.commit()
        log.info(f"Seeded {len(reports_list)} reports.")

    except Exception as e:
        log.error(f"Failed to seed reports data: {e}")
        db.session.rollback()
