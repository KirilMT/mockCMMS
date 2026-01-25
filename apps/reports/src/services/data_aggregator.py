from datetime import datetime, timedelta, timezone

from apps.reports.src.models import Incident
from src.services.db_utils import MaintenanceOrder


class DataAggregator:
    def get_weekend_tasks(self, start_date, end_date):
        """Query MaintenanceOrder for tasks in the date range."""
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).replace(
            tzinfo=timezone.utc
        )  # Include end date

        tasks = MaintenanceOrder.query.filter(
            MaintenanceOrder.due_date >= start, MaintenanceOrder.due_date < end
        ).all()

        return [task.to_dict() for task in tasks]

    def get_shift_data(self, date_str, shift):
        """Query MaintenanceOrder and other relevant data for the specific shift."""
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # Define shift hours (simplified)
        if shift.lower() == "morning":
            start_hour, end_hour = 6, 14
        elif shift.lower() == "afternoon":
            start_hour, end_hour = 14, 22
        else:  # Night
            start_hour, end_hour = 22, 6

        start_time = date.replace(hour=start_hour, minute=0, second=0)
        if shift.lower() == "night":
            end_time = (date + timedelta(days=1)).replace(
                hour=end_hour, minute=0, second=0
            )
        else:
            end_time = date.replace(hour=end_hour, minute=0, second=0)

        tasks = MaintenanceOrder.query.filter(
            MaintenanceOrder.created_at >= start_time,
            MaintenanceOrder.created_at < end_time,
        ).all()

        return [task.to_dict() for task in tasks]

    def get_incidents(self, filters=None):
        """Query Incident model."""
        query = Incident.query

        if filters:
            if filters.get("incident_type"):
                query = query.filter_by(incident_type=filters["incident_type"])
            if filters.get("severity"):
                query = query.filter_by(severity=filters["severity"])
            if filters.get("start_date"):
                query = query.filter(
                    Incident.timestamp
                    >= datetime.strptime(filters["start_date"], "%Y-%m-%d")
                )
            if filters.get("end_date"):
                query = query.filter(
                    Incident.timestamp
                    < datetime.strptime(filters["end_date"], "%Y-%m-%d")
                    + timedelta(days=1)
                )

        return [incident.to_dict() for incident in query.all()]
