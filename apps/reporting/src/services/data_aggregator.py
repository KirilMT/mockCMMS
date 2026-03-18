"""Data aggregation service for reporting."""

import json
import logging
import re
from datetime import datetime, timedelta, timezone

from flask import has_app_context

from apps.reporting.src import models as report_models
from src.services.db_utils import MaintenanceOrder, Team, User
from src.services.shift_utils import ShiftUtils

logger = logging.getLogger(__name__)


class DataAggregator:
    """Service for aggregating data for various report types."""

    @staticmethod
    def _normalize_utc(dt_value):
        """Normalize datetimes to UTC-aware values for safe comparisons."""
        if dt_value is None:
            return None
        if dt_value.tzinfo is None:
            return dt_value.replace(tzinfo=timezone.utc)
        return dt_value.astimezone(timezone.utc)

    @staticmethod
    def _has_assignees(mo):
        """Support both normalized assignees relation and legacy assignees_json."""
        if getattr(mo, "assignees", None):
            return len(mo.assignees) > 0

        assignees_json = getattr(mo, "assignees_json", None)
        if assignees_json is None:
            return False

        assignees_text = str(assignees_json).strip()
        return assignees_text not in {"", "[]", "null", "None"}

    @staticmethod
    def _extract_assignee_ids(mo):
        """Return assignee user IDs from relationship or legacy JSON payloads."""
        assignee_ids = set()
        assignees = getattr(mo, "assignees", None)
        if assignees:
            assignee_ids.update(
                user.id for user in assignees if getattr(user, "id", None) is not None
            )

        assignees_json = getattr(mo, "assignees_json", None)
        if not assignees_json:
            return assignee_ids

        try:
            payload = (
                json.loads(assignees_json)
                if isinstance(assignees_json, str)
                else assignees_json
            )
        except (TypeError, json.JSONDecodeError):
            return assignee_ids

        if isinstance(payload, dict):
            payload = payload.get("assignees") or payload.get("users") or [payload]

        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    user_id = item.get("id") or item.get("user_id")
                    if user_id is not None:
                        assignee_ids.add(user_id)
                        continue
                    username = item.get("username")
                    if username:
                        user = User.query.filter_by(username=username).first()
                        if user:
                            assignee_ids.add(user.id)
                        continue
                    team_name = item.get("team") or item.get("team_name")
                    if team_name:
                        team = Team.query.filter_by(name=team_name).first()
                        if team:
                            members = User.query.filter_by(team_id=team.id).all()
                            assignee_ids.update(member.id for member in members)
                elif isinstance(item, int):
                    assignee_ids.add(item)
                elif isinstance(item, str):
                    token = item.strip()
                    if not token:
                        continue
                    if token.startswith("user:"):
                        username = token.split(":", 1)[1]
                        user = User.query.filter_by(username=username).first()
                        if user:
                            assignee_ids.add(user.id)
                    elif token.startswith("team:"):
                        team_name = token.split(":", 1)[1]
                        team = Team.query.filter_by(name=team_name).first()
                        if team:
                            members = User.query.filter_by(team_id=team.id).all()
                            assignee_ids.update(member.id for member in members)
                    elif token.isdigit():
                        assignee_ids.add(int(token))

        return assignee_ids

    @staticmethod
    def _get_team_user_ids(team_id):
        """Return a set of user IDs for a team_id, or None when not provided."""
        if not team_id:
            return None
        try:
            team_id_int = int(team_id)
        except (TypeError, ValueError):
            return None
        return {user.id for user in User.query.filter_by(team_id=team_id_int).all()}

    def _mo_matches_team(self, mo, team_user_ids):
        """Check whether a MO has assignees from the selected team."""
        if team_user_ids is None:
            return True
        assignee_ids = self._extract_assignee_ids(mo)
        return bool(assignee_ids & team_user_ids)

    def _is_assigned_for_report(self, mo, team_user_ids):
        """Return True when a MO should be included based on assignments."""
        if team_user_ids is None:
            return self._has_assignees(mo)
        return self._mo_matches_team(mo, team_user_ids)

    def _get_shift_incidents(self, start_time, end_time, team_user_ids=None):
        """Get breakdowns (Completed Reactive MOs) within the shift window."""
        # Strip timezone for SQLite compatibility (stored values are naive)
        naive_start = (
            start_time.replace(tzinfo=None)
            if start_time and start_time.tzinfo
            else start_time
        )
        naive_end = (
            end_time.replace(tzinfo=None) if end_time and end_time.tzinfo else end_time
        )
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type == "Reactive",
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.created_at >= naive_start,
            MaintenanceOrder.created_at <= naive_end,
        ).all()

        incidents = []
        for mo in mos:
            if team_user_ids is not None and not self._mo_matches_team(
                mo, team_user_ids
            ):
                continue
            asset_name = mo.asset.name if mo.asset else "N/A"
            incidents.append(
                {
                    "id": mo.id,
                    "mo_id": mo.id,
                    "asset_code": mo.asset.asset_code if mo.asset else "N/A",
                    "asset_name": asset_name,
                    "title": mo.title or mo.description,
                    "description": mo.description,
                    "start_time": (
                        mo.created_at.strftime("%H:%M") if mo.created_at else "N/A"
                    ),
                    "timestamp": (
                        mo.created_at.strftime("%H:%M") if mo.created_at else "N/A"
                    ),
                    "duration": mo.downtime_duration or "N/A",
                    "root_cause": mo.root_cause or "N/A",
                    "resolution_notes": mo.recovery or "N/A",
                    "priority": mo.priority,
                    "status": mo.status,
                }
            )
        return incidents

    def _get_handover_from_previous(
        self, start_time, team_user_ids=None, weekend_mode=False
    ):
        """Get handover notes from In Progress MOs before shift start.

        Args:
            start_time: Start of shift
            team_user_ids: Team filter
            weekend_mode: If True, only include Corrective/PM types (exclude Reactive)
        """
        if weekend_mode:
            mos = MaintenanceOrder.query.filter(
                MaintenanceOrder.order_type.in_(["Corrective", "PM"]),
                MaintenanceOrder.status == "In Progress",
            ).all()
        else:
            mos = MaintenanceOrder.query.filter(
                MaintenanceOrder.order_type.in_(["Reactive", "Corrective"]),
                MaintenanceOrder.status == "In Progress",
            ).all()

        normalized_start = self._normalize_utc(start_time)
        lower_bound = None
        if weekend_mode and normalized_start:
            lower_bound = normalized_start - timedelta(hours=12)
        handovers = []
        for mo in mos:
            # Skip cancelled MOs
            if mo.status == "Cancelled":
                continue
            if not self._is_assigned_for_report(mo, team_user_ids):
                continue
            created_at = self._normalize_utc(getattr(mo, "created_at", None))
            if not (created_at and normalized_start and created_at < normalized_start):
                continue
            if lower_bound and created_at < lower_bound:
                continue
            asset_code = mo.asset.asset_code if mo.asset else "UNKNOWN"
            handovers.append(
                {
                    "mo_id": mo.id,
                    "id": mo.id,
                    "title": mo.title or mo.description,
                    "asset_code": asset_code,
                    "description": mo.description,
                    "note": f"{asset_code} - MO-{mo.id} - {mo.title or mo.description}",
                }
            )
        return handovers

    def _get_handover_to_next(
        self, start_time, end_time, team_user_ids=None, weekend_mode=False
    ):
        """Get in-progress MOs created during this shift.

        Args:
            start_time: Shift start
            end_time: Shift end
            team_user_ids: Team filter
            weekend_mode: If True, only include Corrective/PM types (exclude Reactive)
        """
        if weekend_mode:
            mos = MaintenanceOrder.query.filter(
                MaintenanceOrder.order_type.in_(["Corrective", "PM"]),
                MaintenanceOrder.status == "In Progress",
            ).all()
        else:
            mos = MaintenanceOrder.query.filter(
                MaintenanceOrder.order_type.in_(["Reactive", "Corrective"]),
                MaintenanceOrder.status == "In Progress",
            ).all()

        normalized_start = self._normalize_utc(start_time)
        normalized_end = self._normalize_utc(end_time)
        handovers = []
        for mo in mos:
            # Skip cancelled MOs
            if mo.status == "Cancelled":
                continue
            if not self._is_assigned_for_report(mo, team_user_ids):
                continue
            created_at = self._normalize_utc(getattr(mo, "created_at", None))
            if not (
                created_at
                and normalized_start
                and normalized_end
                and normalized_start <= created_at <= normalized_end
            ):
                continue
            asset_code = mo.asset.asset_code if mo.asset else "UNKNOWN"
            handovers.append(
                {
                    "mo_id": mo.id,
                    "id": mo.id,
                    "title": mo.title or mo.description,
                    "asset_code": asset_code,
                    "description": mo.description,
                    "note": f"{asset_code} - MO-{mo.id} - {mo.title or mo.description}",
                }
            )
        return handovers

    def _get_engineering_support(self, start_time, end_time, team_user_ids=None):
        """Get Engineering-category MOs (Corrective) within the shift window.

        Note: logic typically looks for Completed Corrective MOs of Engineering
        category.
        """
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type == "Corrective",
            MaintenanceOrder.category == "Engineering",
            MaintenanceOrder.modified_on >= start_time,
            MaintenanceOrder.modified_on <= end_time,
        ).all()

        engineering_mos = []
        for mo in mos:
            if team_user_ids is not None and not self._mo_matches_team(
                mo, team_user_ids
            ):
                continue
            asset_code = mo.asset.asset_code if mo.asset else "N/A"
            engineering_mos.append(
                {
                    "mo_id": mo.id,
                    "id": mo.id,
                    "asset": asset_code,
                    "asset_code": asset_code,
                    "title": mo.title or f"MO-{mo.id}",
                    "description": mo.description,
                    "status": mo.status,
                }
            )
        return engineering_mos

    def _get_previous_shift(self, date_str, shift):
        """Return previous shift date/label for a given shift/date."""
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if shift == "Early":
            prev_date = (date - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_shift = "Night"
        else:
            prev_date = date.strftime("%Y-%m-%d")
            prev_shift = "Early"
        return prev_date, prev_shift

    def _get_previous_shift_team_user_ids(self, date_str, shift):
        """Get user IDs for the team that worked the previous shift.

        Uses shift_calendar logic to determine which team was assigned to the previous
        shift, then returns that team's user IDs.
        """
        if not has_app_context():
            return None

        from src.services.shift_utils import get_shift_teams

        prev_date, prev_shift = self._get_previous_shift(date_str, shift)
        try:
            prev_date_obj = datetime.strptime(prev_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            return None

        teams = Team.query.all()
        early_team, late_team = get_shift_teams(prev_date_obj, teams)

        # Determine which team worked the previous shift
        prev_team = late_team if prev_shift in {"Night", "Late"} else early_team

        if not prev_team:
            return None

        return {user.id for user in User.query.filter_by(team_id=prev_team.id).all()}

    def _get_previous_shift_handover(self, date_str, shift):
        """Pull handover_to_next from previous shift report, or query DB directly."""
        prev_date, prev_shift = self._get_previous_shift(date_str, shift)
        shift_aliases = {
            "Night": {"Night", "Late"},
            "Early": {"Early"},
        }
        allowed_shifts = shift_aliases.get(prev_shift, {prev_shift})
        reporting_rows = (
            report_models.Report.query.filter_by(report_type="shift_report")
            .order_by(report_models.Report.generated_on.desc())
            .all()
        )
        for report in reporting_rows:
            data = report.data or {}
            report_info = data.get("report_info") or data.get("shift_info") or {}
            report_shift = report_info.get("shift")
            if report_info.get("date") == prev_date and report_shift in allowed_shifts:
                return (
                    report_info.get("handover_to_next")
                    or data.get("handover_to_next")
                    or []
                )

        # If no previous report found, query database directly for In-Progress MOs
        # from the previous shift that should be handed over
        date_obj = datetime.strptime(prev_date, "%Y-%m-%d")
        prev_shift_start, prev_shift_end = ShiftUtils().get_shift_window(
            date_obj, prev_shift
        )
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type.in_(["Reactive", "Corrective"]),
            MaintenanceOrder.status == "In Progress",
        ).all()

        handovers = []
        normalized_start = self._normalize_utc(prev_shift_start)
        normalized_end = self._normalize_utc(prev_shift_end)

        for mo in mos:
            if mo.status == "Cancelled":
                continue
            created_at = self._normalize_utc(getattr(mo, "created_at", None))
            if not (
                created_at
                and normalized_start
                and normalized_end
                and normalized_start <= created_at <= normalized_end
            ):
                continue
            asset_code = mo.asset.asset_code if mo.asset else "UNKNOWN"
            handovers.append(
                {
                    "mo_id": mo.id,
                    "id": mo.id,
                    "title": mo.title or mo.description,
                    "asset_code": asset_code,
                    "description": mo.description,
                    "timestamp": (
                        mo.created_at.strftime("%H:%M") if mo.created_at else "N/A"
                    ),
                    "duration": mo.downtime_duration or "N/A",
                    "status": mo.status,
                    "note": f"{asset_code} - MO-{mo.id} - {mo.title or mo.description}",
                }
            )
        return handovers

    def _normalize_handover_items(self, items):
        """Normalize handover items to a consistent asset/title/description format."""
        normalized = []
        for item in items or []:
            mo_id = None
            asset_code = "UNKNOWN"
            description = ""
            title = "Handover"
            status = None
            timestamp = "N/A"
            duration = "N/A"

            if isinstance(item, dict):
                mo_id = item.get("mo_id") or item.get("id")
                asset_code = item.get("asset_code") or item.get("asset") or asset_code
                description = item.get("description") or item.get("note") or ""
                title = item.get("title") or title
                status = item.get("status")
                timestamp = item.get("timestamp") or item.get("start_time") or "N/A"
                duration = item.get("duration") or "N/A"
            else:
                description = str(item)
                match = re.search(r"\bMO-?(\d+)\b", description)
                if match:
                    mo_id = int(match.group(1))

            if mo_id:
                mo = MaintenanceOrder.query.get(mo_id)
                if mo:
                    if mo.status == "Cancelled":
                        continue
                    asset_code = mo.asset.asset_code if mo.asset else asset_code
                    description = mo.description or description
                    status = mo.status
                    title = mo.title or mo.description or title
                    timestamp = (
                        mo.created_at.strftime("%H:%M") if mo.created_at else timestamp
                    )
                    duration = mo.downtime_duration or duration

            normalized.append(
                {
                    "mo_id": mo_id,
                    "asset": asset_code,
                    "title": title,
                    "description": description,
                    "status": status,
                    "timestamp": timestamp,
                    "duration": duration,
                }
            )
        return normalized

    def _filter_handover_items_by_team(self, items, team_user_ids):
        """Filter handover items by team assignees when mo_id is available."""
        if team_user_ids is None:
            return items
        filtered = []
        for item in items or []:
            mo_id = item.get("mo_id")
            if not mo_id:
                filtered.append(item)
                continue
            mo = MaintenanceOrder.query.get(mo_id)
            if mo and self._mo_matches_team(mo, team_user_ids):
                filtered.append(item)
        return filtered

    def _merge_handover_lists(self, primary, secondary):
        """Merge two handover lists, de-duplicating by mo_id and description."""
        merged = []
        seen = set()
        for item in (primary or []) + (secondary or []):
            key = (item.get("mo_id"), item.get("description"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

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

    def get_aggregated_shift_data(self, date_str, shift, team_id=None):
        """Aggregate data for Shift Report (Breakdowns, Handovers, Engineering
        Support)."""
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        shift_utils = ShiftUtils()
        start_time, end_time = shift_utils.get_shift_window(date, shift)

        team_user_ids = self._get_team_user_ids(team_id)

        # 1. Breakdowns (Reactive MOs created in shift)
        breakdowns_data = self._get_shift_incidents(start_time, end_time, team_user_ids)

        # 2. Handover from previous shift report + in-progress at shift start
        # IMPORTANT: Use previous shift's team for filtering handover items
        prev_team_user_ids = self._get_previous_shift_team_user_ids(date_str, shift)
        prev_report_handover = self._normalize_handover_items(
            self._get_previous_shift_handover(date_str, shift)
        )
        prev_report_handover = self._filter_handover_items_by_team(
            prev_report_handover, prev_team_user_ids
        )
        in_progress_before = self._normalize_handover_items(
            self._get_handover_from_previous(start_time, prev_team_user_ids)
        )
        handover_from = self._merge_handover_lists(
            prev_report_handover, in_progress_before
        )

        # 3. Handover to next shift (In Progress Reactive MOs created during shift)
        handover_to = self._normalize_handover_items(
            self._get_handover_to_next(start_time, end_time, team_user_ids)
        )

        # 4. Engineering Support (MOs during shift + Corrective Engineering)
        # Note: logic merged below with break activities if we want split by category
        engineering_support = []  # Reset, will populate from MOs

        # 5. Break Activities (Completed Corrective MOs in shift)
        # Filter by modified_on (when status changed to Completed) OR created_at
        # if modified_on is None
        completed_corrective = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type == "Corrective",
            MaintenanceOrder.status == "Completed",
        ).all()

        # Filter to only MOs completed during this shift
        shift_start = self._normalize_utc(start_time)
        shift_end = self._normalize_utc(end_time)
        corrective_in_shift = []
        for mo in completed_corrective:
            if team_user_ids is not None and not self._mo_matches_team(
                mo, team_user_ids
            ):
                continue
            # Use modified_on when available; fallback to created_at.
            completion_time = mo.modified_on if mo.modified_on else mo.created_at
            normalized_completion = self._normalize_utc(completion_time)
            if (
                normalized_completion
                and shift_start
                and shift_end
                and shift_start <= normalized_completion <= shift_end
            ):
                corrective_in_shift.append(mo)

        break_activities = []
        for mo in corrective_in_shift:
            asset_code = mo.asset.asset_code if mo.asset else "N/A"
            category = getattr(mo, "category", None)

            # Create item dict
            item_dict = {
                "mo_id": f"MO-{mo.id}",
                "id": mo.id,  # Include raw ID for linking
                "asset": asset_code,
                "asset_code": asset_code,
                "title": mo.title or f"MO-{mo.id}",
                "description": mo.description,
                "status": mo.status,
            }

            if category == "Engineering":
                engineering_support.append(item_dict)
            else:
                item_dict["type"] = "flux_ticket"
                break_activities.append(item_dict)

        return {
            "report_info": {
                "date": date_str,
                "shift": shift,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
            },
            "breakdowns": breakdowns_data,
            "handover_from_previous": handover_from,
            "handover_to_next": handover_to,
            "engineering_support": engineering_support,
            "break_activities": break_activities,
        }

    def get_aggregated_weekend_data(self, weekend_date_str, team_id=None, shift=None):
        """Aggregate data for Weekend Report.

        Args:
            weekend_date_str: Date string in YYYY-MM-DD format
            team_id: Optional team ID for filtering
            shift: Optional shift ("Night" or "Early") for per-shift reporting
        """
        d = datetime.strptime(weekend_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # Calculate saturday/sunday for reference
        wd = d.weekday()
        days_since_sat = (wd - 5) % 7
        saturday = d - timedelta(days=days_since_sat)
        sunday = saturday + timedelta(days=1)

        # If shift is specified, use specific shift window for that date
        if shift:
            shift_utils = ShiftUtils()
            start_time, end_time = shift_utils.get_shift_window(d, shift)
        else:
            # Weekend window: Saturday 6am to Monday 6am
            start_time = saturday.replace(hour=6, minute=0, second=0)
            end_time = (sunday + timedelta(days=1)).replace(hour=6, minute=0, second=0)

        team_user_ids = self._get_team_user_ids(team_id)

        # PMs completed during weekend (use created_at for filtering)
        pms = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type == "PM",
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.created_at >= start_time,
            MaintenanceOrder.created_at <= end_time,
        ).all()

        pm_data = []
        for mo in pms:
            if team_user_ids is not None and not self._mo_matches_team(
                mo, team_user_ids
            ):
                continue
            asset_code = mo.asset.asset_code if mo.asset else "N/A"
            pm_data.append(
                {
                    "mo_id": mo.id,
                    "asset_code": asset_code,
                    "description": mo.description,
                    "status": mo.status,
                }
            )

        # MOs/Tickets (ONLY Corrective work orders completed during weekend)
        # Reactive MOs should NOT appear in weekend reporting
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type == "Corrective",
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.created_at >= start_time,
            MaintenanceOrder.created_at <= end_time,
        ).all()

        mo_data = []
        additional_data = []
        for mo in mos:
            if team_user_ids is not None and not self._mo_matches_team(
                mo, team_user_ids
            ):
                continue
            asset_code = mo.asset.asset_code if mo.asset else "N/A"
            mo_entry = {
                "id": f"MO-{mo.id}",
                "mo_id": mo.id,
                "asset": asset_code,
                "asset_code": asset_code,
                "description": mo.description,
                "status": mo.status,
            }

            title_text = (mo.title or "").lower()
            description_text = (mo.description or "").lower()
            if "additional" in title_text or "additional" in description_text:
                additional_data.append(mo_entry)
            else:
                mo_data.append(mo_entry)

        # Handover from previous shift (In Progress Corrective/PM only, no Reactive)
        handover_from = self._normalize_handover_items(
            self._get_handover_from_previous(
                start_time, team_user_ids, weekend_mode=True
            )
        )

        # Handover to next shift (In Progress Corrective/PM created during weekend)
        handover_to = self._normalize_handover_items(
            self._get_handover_to_next(
                start_time, end_time, team_user_ids, weekend_mode=True
            )
        )

        # Engineering Support during weekend
        engineering_support = self._get_engineering_support(
            start_time, end_time, team_user_ids
        )

        return {
            "report_info": {
                "start_date": (
                    d.strftime("%Y-%m-%d") if shift else saturday.strftime("%Y-%m-%d")
                ),
                "end_date": (
                    d.strftime("%Y-%m-%d") if shift else sunday.strftime("%Y-%m-%d")
                ),
                "date": weekend_date_str,
                "shift": shift if shift else None,
                "team_name": "Team C",
                "attendance_total": 20,
                "vigel_total": 10,
                "mds_total": 15,
                "ehs_incidents": 0,
            },
            "weekend_dates": {
                "saturday": (
                    d.strftime("%Y-%m-%d") if shift else saturday.strftime("%Y-%m-%d")
                ),
                "sunday": (
                    d.strftime("%Y-%m-%d") if shift else sunday.strftime("%Y-%m-%d")
                ),
            },
            "pms": pm_data,
            "mos_tickets": mo_data,
            "additional_tickets": additional_data,
            "engineering_support": engineering_support,
            "handover_from_previous": handover_from,
            "handover_to_next": handover_to,
            "generated_by_name": "System Aggregator",
        }
