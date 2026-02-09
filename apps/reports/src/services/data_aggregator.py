"""Data aggregation service for reports."""

import logging
from datetime import datetime, timedelta, timezone

from src.services.db_utils import MaintenanceOrder
from src.services.shift_utils import ShiftUtils

logger = logging.getLogger(__name__)


class DataAggregator:
    """Service for aggregating data for various report types."""

    def _get_shift_incidents(self, start_time, end_time):
        """Get breakdowns (Reactive MOs) within the shift window."""
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type.in_(["Reactive", "Corrective"]),
            MaintenanceOrder.created_at >= start_time,
            MaintenanceOrder.created_at <= end_time,
        ).all()

        incidents = []
        for mo in mos:
            asset_name = mo.asset.name if mo.asset else "N/A"
            incidents.append(
                {
                    "id": mo.id,
                    "asset_code": mo.asset.asset_code if mo.asset else "N/A",
                    "asset_name": asset_name,
                    "description": mo.description,
                    "start_time": (
                        mo.created_at.strftime("%H:%M") if mo.created_at else "N/A"
                    ),
                    "priority": mo.priority,
                    "status": mo.status,
                }
            )
        return incidents

    def get_weekend_tasks(self, start_date, end_date):
        """Query MaintenanceOrder for tasks in the date range."""
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).replace(
            tzinfo=timezone.utc
        )

        tasks = MaintenanceOrder.query.filter(
            MaintenanceOrder.due_date >= start, MaintenanceOrder.due_date < end
        ).all()

        return [task.to_dict() for task in tasks]

    def get_shift_data(self, date_str, shift):
        """Query MaintenanceOrder and other relevant data for the specific shift."""
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        shift_utils = ShiftUtils()
        start_time, end_time = shift_utils.get_shift_window(date, shift)

        tasks = MaintenanceOrder.query.filter(
            MaintenanceOrder.created_at >= start_time,
            MaintenanceOrder.created_at < end_time,
        ).all()

        return [task.to_dict() for task in tasks]

    def get_aggregated_shift_data(self, date_str, shift):
        """Aggregate data for Shift Report (Breakdowns and Break Activities)."""
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        shift_utils = ShiftUtils()
        start_time, end_time = shift_utils.get_shift_window(date, shift)

        # 1. Breakdowns (Reactive/Corrective MOs created in shift)
        breakdowns_data = self._get_shift_incidents(start_time, end_time)

        # 2. Break Activities (Completed MOs in shift - using due_date as proxy)
        completed_mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.due_date >= start_time,
            MaintenanceOrder.due_date <= end_time,
        ).all()

        break_activities = []
        for mo in completed_mos:
            asset_name = mo.asset.name if mo.asset else "N/A"
            break_activities.append(
                {
                    "asset": asset_name,
                    "description": mo.description,
                    "status": mo.status,
                }
            )

        return {
            "shift_info": {
                "date": date_str,
                "shift": shift,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
            },
            "breakdowns": breakdowns_data,
            "break_activities": break_activities,
        }

    def get_aggregated_weekend_data(self, weekend_date_str):
        """Aggregate data for Weekend Report."""
        d = datetime.strptime(weekend_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # Find Saturday of this week
        wd = d.weekday()
        days_since_sat = (wd - 5) % 7
        saturday = d - timedelta(days=days_since_sat)
        sunday = saturday + timedelta(days=1)

        # Weekend window: Saturday 6am to Monday 6am
        start_time = saturday.replace(hour=6, minute=0, second=0)
        end_time = (sunday + timedelta(days=1)).replace(hour=6, minute=0, second=0)

        # PMs completed during weekend
        pms = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type == "PM",
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.due_date >= start_time,
            MaintenanceOrder.due_date <= end_time,
        ).all()

        pm_data = []
        for mo in pms:
            asset_name = mo.asset.name if mo.asset else "N/A"
            pm_data.append(
                {
                    "asset": asset_name,
                    "description": mo.description,
                    "status": mo.status,
                }
            )

        # MOs/Tickets (non-PM work orders)
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type.in_(["Reactive", "Corrective"]),
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.due_date >= start_time,
            MaintenanceOrder.due_date <= end_time,
        ).all()

        mo_data = []
        for mo in mos:
            asset_name = mo.asset.name if mo.asset else "N/A"
            mo_data.append(
                {
                    "id": mo.id,
                    "asset": asset_name,
                    "description": mo.description,
                    "status": mo.status,
                }
            )

        return {
            "weekend_info": {
                "start_date": saturday.strftime("%Y-%m-%d"),
                "end_date": sunday.strftime("%Y-%m-%d"),
            },
            "pms": pm_data,
            "mos_tickets": mo_data,
            "additional_tickets": [],
        }
