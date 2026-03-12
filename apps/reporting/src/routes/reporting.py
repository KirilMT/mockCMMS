"""Routes for the main Reporting dashboard."""

import json
import os
import re
import sys
from datetime import datetime, timezone
from functools import wraps
from html import escape

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

# Add the main src directory to the path to import from mockCMMS
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))
from apps.reporting.src import models as report_models  # noqa: E402
from apps.reporting.src.services import data_aggregator as da_service  # noqa: E402
from apps.reporting.src.services import report_generator as rg_service  # noqa: E402
from src.services.db_utils import Team, db  # noqa: E402
from src.services.shift_utils import get_shift_teams  # noqa: E402

from .shift_report import shift_bp  # noqa: E402
from .weekend_report import weekend_bp  # noqa: E402

reporting_bp = Blueprint(
    "reporting",
    __name__,
    url_prefix="/reporting",
    template_folder="../templates",
    static_folder="../static",
    static_url_path="/static",
)

# Register sub-blueprints
reporting_bp.register_blueprint(weekend_bp)
reporting_bp.register_blueprint(shift_bp)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: login_required check. Session keys: {list(session.keys())}")
        if "user_id" not in session:
            flash("Login required to access this page.", "warning")
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def _build_display_title(report_obj, report_dict):
    """Return a title aligned with the editable report header format."""
    raw_data = report_obj.data or {}
    data = raw_data if isinstance(raw_data, dict) else {}
    report_info = data.get("report_info", {}) if isinstance(data, dict) else {}

    date_value = (
        report_info.get("date") or data.get("weekend_date") or data.get("shift_date")
    )
    shift_value = report_info.get("shift") or data.get("shift")
    team_value = report_info.get("team_name") or data.get("team_name")

    if not date_value:
        return report_dict.get("title") or "Report"

    label = (
        "Shift Report"
        if report_obj.report_type == "shift_report"
        else "Weekend Shift Report"
    )
    title = f"{label} - {date_value}"
    if shift_value:
        title += f" - {shift_value}"
    if team_value:
        title += f" - {team_value}"
    return title


def _safe_json_for_template(payload):
    """Serialize payload for embedding in templates, coercing unknown objects to
    strings."""
    # Ensure payload is a dict, never None or other types
    if payload is None:
        return json.dumps({})
    if not isinstance(payload, dict):
        return json.dumps({})

    try:
        # First attempt: normal JSON dump (fails if custom objects present)
        return json.dumps(payload)
    except TypeError:
        # Fallback: convert objects to strings recursively
        def convert_value(obj):
            """Recursively convert non-serializable objects to strings."""
            if isinstance(obj, dict):
                return {k: convert_value(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_value(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                # Custom objects: convert to string
                return str(obj)

        converted = convert_value(payload)
        return json.dumps(converted)


def _resolve_shift_team_id(date_str, shift_name):
    """Resolve the team assigned to the given date/shift using shift-calendar logic."""
    if not date_str or not shift_name:
        return None, None

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None, None

    teams = Team.query.all()
    early_team, late_team = get_shift_teams(date_obj, teams)

    normalized_shift = (shift_name or "").strip().lower()
    target_team = late_team if normalized_shift in {"night", "late"} else early_team
    if not target_team:
        return None, None

    return str(target_team.id), target_team.name


def _sync_file_reporting_records():
    """Scan the reporting directory for JSON files and ensure they exist in the DB."""
    try:
        report_dir = rg_service.ReportGenerator().reporting_dir
        if not os.path.exists(report_dir):
            return

        json_files = [f for f in os.listdir(report_dir) if f.endswith(".json")]

        # Get existing file paths from DB to avoid duplicates
        existing_paths = {
            r[0]
            for r in report_models.Report.query.with_entities(
                report_models.Report.file_path
            ).all()
            if r[0]
        }

        new_reporting_entries = []
        for filename in json_files:
            file_path = os.path.join(report_dir, filename)
            if file_path in existing_paths:
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract metadata
                title = data.get("title", f"Imported Report {filename}")
                report_type = data.get("report_type", "shift_report")

                # Attempt to determine type from content if missing
                if "report_type" not in data:
                    if "shift_info" in data:
                        report_type = "shift_report"
                    elif "weekend_info" in data:
                        report_type = "weekend_report"

                # Extract date for generated_on
                generated_at = data.get("generated_at")
                generated_on = datetime.now(timezone.utc)
                if generated_at:
                    try:
                        generated_on = datetime.fromisoformat(generated_at)
                    except ValueError:
                        pass

                # Extract parameters
                parameters = data.get("parameters", {})

                report = report_models.Report(
                    title=title,
                    report_type=report_type,
                    generated_on=generated_on,
                    parameters=parameters,
                    data=data,
                    file_path=file_path,
                    format="html",
                )
                new_reporting_entries.append(report)

            except Exception as e:
                current_app.logger.error(f"Failed to sync report file {filename}: {e}")

        if new_reporting_entries:
            db.session.add_all(new_reporting_entries)
            db.session.commit()
            current_app.logger.info(
                "Synced %s file-based reporting entries to DB.",
                len(new_reporting_entries),
            )

    except Exception as e:
        current_app.logger.error(f"Error syncing file-based reporting data: {e}")


_sync_file_reporting = _sync_file_reporting_records


@reporting_bp.route("/")
@login_required
def index():
    try:
        # Import User from db_utils where it's defined (not src.models)
        from src.services.db_utils import User

        # Create reporting table if it does not exist using checkfirst=True
        # This safely handles the case where table already exists
        try:
            reporting_engine = db.get_engine(bind="reporting")
            report_models.Report.__table__.create(reporting_engine, checkfirst=True)
        except Exception as table_err:
            current_app.logger.debug(f"Table check skipped: {table_err}")

        # Sync legacy file-based reporting data to DB
        _sync_file_reporting_records()

        # Fetch only reporting records generated by current logic (or all)
        reporting_records = report_models.Report.query.order_by(
            report_models.Report.generated_on.desc()
        ).all()

        reporting_items = []
        for r in reporting_records:
            r_dict = r.to_dict()
            # Resolve generated_by ID to Name if possible
            r_dict["generated_by_name"] = "System"
            if r.generated_by:
                try:
                    user = User.query.filter_by(id=r.generated_by).first()
                    if user:
                        r_dict["generated_by_name"] = user.username
                except Exception:
                    r_dict["generated_by_name"] = "Unknown"
            r_dict["title"] = _build_display_title(r, r_dict)
            reporting_items.append(r_dict)

        # Get current user data and teams for modal
        user_data = {}
        if session.get("user_id"):
            from src.services.db_utils import User

            user = User.query.filter_by(id=session.get("user_id")).first()
            if user:
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "team_id": user.team_id,
                }

        teams_orm = Team.query.order_by(Team.name).all()
        # Serialize to plain dicts so tojson works in the template
        teams = [{"id": t.id, "name": t.name} for t in teams_orm]

        return render_template(
            "reporting.html",
            reporting_items=reporting_items,
            user_data=user_data,
            teams=teams,
        )
    except Exception as e:
        current_app.logger.error(
            f"Error loading reporting dashboard: {e}", exc_info=True
        )
        # Fallback if table creation fails or other DB issues
        return render_template(
            "reporting.html",
            reporting_items=[],
            user_data={},
            teams=[],
        )


reporting = index


@reporting_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate_report():
    if request.method == "POST":
        # Ensure table exists using checkfirst=True to avoid errors
        try:
            reporting_engine = db.get_engine(bind="reporting")
            report_models.Report.__table__.create(reporting_engine, checkfirst=True)
        except Exception as e:
            current_app.logger.debug(f"Table check skipped: {e}")

        report_type = request.form.get("report_type")

        # Validate required fields
        if not report_type:
            flash("Report Type is required.", "danger")
            return redirect(url_for("reporting.index"))

        # New Feature: Handover Inputs (Process as list based on newlines)
        handover_from_raw = request.form.get("handover_from_previous", "")
        handover_to_raw = request.form.get("handover_to_next", "")

        # Split by newline and filter empty
        handover_from_previous = [
            line.strip() for line in handover_from_raw.splitlines() if line.strip()
        ]
        handover_to_next = [
            line.strip() for line in handover_to_raw.splitlines() if line.strip()
        ]

        parameters = {}
        data = {}
        title = "Report"  # Default title (will be overridden)

        if report_type == "shift_report":
            date_str = request.form.get("shift_date")
            shift_name = request.form.get("shift_name")

            # Validation: Ensure date is provided
            if not date_str:
                flash("Shift Date is required.", "danger")
                return redirect(url_for("reporting.index"))

            # Handle Team Assignment: Prefer user selection, fallback to calendar
            form_team_id = request.form.get("team_id")
            field_team_id, field_team_name = _resolve_shift_team_id(
                date_str, shift_name
            )

            if form_team_id:
                team_id = form_team_id
                # Fetch name for the ID
                team_obj = Team.query.get(team_id)
                team_name = team_obj.name if team_obj else field_team_name
            else:
                team_id = field_team_id
                team_name = field_team_name

            # Auto-generate title
            title = f"Shift Report - {date_str}"
            if shift_name:
                title += f" - {shift_name}"
            if team_name:
                title += f" - {team_name}"

            parameters = {"date": date_str, "shift": shift_name, "team_id": team_id}
            aggregator = da_service.DataAggregator()
            data = aggregator.get_aggregated_shift_data(
                date_str, shift_name, team_id=team_id
            )

            # Combine auto-generated handovers with user input
            auto_handover_from = data.get("handover_from_previous", [])
            auto_handover_to = data.get("handover_to_next", [])

            def _merge_handover(auto_items, user_items):
                merged = list(auto_items or [])
                for item in user_items or []:
                    if item not in merged:
                        merged.append(item)
                return merged

            handover_from_combined = _merge_handover(
                auto_handover_from, handover_from_previous
            )
            handover_to_combined = _merge_handover(auto_handover_to, handover_to_next)

            # Inject team information
            if "report_info" not in data:
                data["report_info"] = {}
            data["report_info"]["team_id"] = team_id
            data["report_info"]["team_name"] = team_name

            # Inject handover notes into the data
            if "report_info" in data:
                data["report_info"]["handover_from_previous"] = handover_from_combined
                data["report_info"]["handover_to_next"] = handover_to_combined

                # Backward compatibility for existing consumers/tests
                if "shift_info" not in data or not isinstance(
                    data.get("shift_info"), dict
                ):
                    data["shift_info"] = data["report_info"]
                data["shift_info"]["handover_from_previous"] = handover_from_combined
                data["shift_info"]["handover_to_next"] = handover_to_combined
            elif "shift_info" in data and isinstance(data.get("shift_info"), dict):
                data["shift_info"]["handover_from_previous"] = handover_from_combined
                data["shift_info"]["handover_to_next"] = handover_to_combined
                data["report_info"] = data["shift_info"]
            else:
                data["handover_from_previous"] = handover_from_previous
                data["handover_to_next"] = handover_to_next
                data["report_type"] = "shift_report"

        elif report_type == "weekend_report":
            weekend_date = request.form.get("weekend_date")
            team_id = request.form.get("team_id")
            weekend_shift = request.form.get("weekend_shift")

            if not team_id and session.get("user_id"):
                from src.services.db_utils import User

                current_user = User.query.filter_by(id=session.get("user_id")).first()
                if current_user and current_user.team_id:
                    team_id = str(current_user.team_id)

            # Validation
            if not weekend_date:
                flash("Weekend Date is required.", "danger")
                return redirect(url_for("reporting.index"))

            # Backward-compatible default shift derivation when not provided by form
            if not weekend_shift:
                try:
                    selected_date = datetime.strptime(weekend_date, "%Y-%m-%d")
                    if selected_date.weekday() == 5:
                        weekend_shift = "Night"
                    elif selected_date.weekday() == 6:
                        weekend_shift = "Early"
                except ValueError:
                    weekend_shift = None

            team_name = None
            if team_id:
                team = Team.query.get(team_id)
                if team:
                    team_name = team.name

            # Auto-generate title for weekend report using the selected date
            title = f"Weekend Shift Report - {weekend_date}"
            if weekend_shift:
                title += f" - {weekend_shift}"
            if team_name:
                title += f" - {team_name}"

            parameters = {
                "weekend_date": weekend_date,
                "team_id": team_id,
                "shift": weekend_shift,
            }
            aggregator = da_service.DataAggregator()
            data = aggregator.get_aggregated_weekend_data(
                weekend_date,
                team_id=team_id,
                shift=weekend_shift,
            )

            # Override dynamic metadata with selected values
            if "report_info" in data:
                data["report_info"]["date"] = weekend_date
                data["report_info"]["shift"] = weekend_shift
                if team_id:
                    data["report_info"]["team_id"] = team_id
                if team_name:
                    data["report_info"]["team_name"] = team_name

            data["shift"] = weekend_shift
            # Append handover notes if relevant for weekend report too
            data["handover_instructions"] = handover_to_next
            data["report_type"] = "weekend_report"

        # STRICT DB ONLY: No file generation for the main report entry
        file_path = None

        # Create DB entry with DATA stored directly
        new_report = report_models.Report(
            title=title,
            report_type=report_type,
            parameters=parameters,
            data=data,  # Store content in DB
            file_path=file_path,
            generated_by=session.get("user_id"),
        )
        db.session.add(new_report)
        db.session.commit()

        flash("Report generated successfully!", "success")
        return redirect(url_for("reporting.index"))

    return render_template("report_generate.html")


@reporting_bp.route("/<int:report_id>")
@login_required
def report_detail(report_id):
    from src.services.db_utils import Asset, MaintenanceOrder, SparePart, User

    report = report_models.Report.query.get_or_404(report_id)

    # Resolve generated_by ID to name
    report.generated_by_name = "System"
    if report.generated_by:
        try:
            user = User.query.filter_by(id=report.generated_by).first()
            if user:
                report.generated_by_name = user.username
        except Exception:
            report.generated_by_name = "Unknown"

    # Load report data from DB
    data = report.data or {}

    # Fallback for older reporting entries or if data is missing in DB but file exists
    # (migration path)
    if (
        not data
        and report.file_path
        and report.file_path.endswith(".json")
        and os.path.exists(report.file_path)
    ):
        try:
            with open(report.file_path, "r") as f:
                data = json.load(f)
        except Exception:
            pass

    if not data:
        flash("Report data not available.", "warning")

    # Data compatibility layer: Ensure report_info exists
    if "report_info" not in data:
        if report.report_type == "shift_report" and "shift_info" in data:
            data["report_info"] = data["shift_info"]
        elif report.report_type == "weekend_report" and "weekend_info" in data:
            data["report_info"] = data["weekend_info"]
        else:
            data["report_info"] = {}

    # Keep backward-compatible alias for shift reporting entries
    if report.report_type == "shift_report":
        if "shift_info" not in data or not isinstance(data.get("shift_info"), dict):
            data["shift_info"] = data["report_info"]
        else:
            data["report_info"] = data["shift_info"]

    # Map legacy keys or ensure they exist in report_info
    ri = data["report_info"]
    if "date" not in ri:
        ri["date"] = (
            ri.get("shift_date")
            or ri.get("weekend_date")
            or report.generated_on.strftime("%Y-%m-%d")
        )
    if "shift" not in ri:
        ri["shift"] = ri.get("shift_name") or data.get("shift") or "Early"
    if "team_name" not in ri:
        ri["team_name"] = data.get("team_name") or ri.get("team_name") or "Technician"
    if "team_color" not in ri:
        ri["team_color"] = data.get("team_color") or ri.get("team_color") or "#95a5a6"

    # Sync back to top level for template convenience
    data["team_name"] = ri["team_name"]
    data["team_color"] = ri["team_color"]
    data["report_type"] = report.report_type

    def _manual_only(items):
        manual_items = []
        for entry in items or []:
            if isinstance(entry, dict):
                if entry.get("mo_id") or entry.get("id"):
                    continue
                manual_items.append(entry)
            else:
                manual_items.append(entry)
        return manual_items

    def _manual_handover_only(items):
        manual_items = []
        for entry in items or []:
            if not isinstance(entry, dict):
                manual_items.append(entry)
                continue

            mo_raw = entry.get("mo_id") or entry.get("id")
            if not mo_raw:
                manual_items.append(entry)
                continue

            mo_match = re.search(r"\d+", str(mo_raw))
            if not mo_match:
                continue

            mo_obj = MaintenanceOrder.query.get(int(mo_match.group(0)))
            # Keep only currently in-progress MOs in handover sections.
            if mo_obj and mo_obj.status == "In Progress":
                manual_items.append(entry)
        return manual_items

    # Dynamic refresh: recompute MO-driven sections for display
    try:
        params = report.parameters if isinstance(report.parameters, dict) else {}

        def _merge_manual_lists(*item_lists):
            merged = []
            seen = set()
            for raw_list in item_lists:
                for entry in _manual_only(raw_list):
                    key = json.dumps(entry, sort_keys=True, default=str)
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append(entry)
            return merged

        def _merge_handover_manual_lists(*item_lists):
            merged = []
            seen = set()
            for raw_list in item_lists:
                for entry in _manual_handover_only(raw_list):
                    key = json.dumps(entry, sort_keys=True, default=str)
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append(entry)
            return merged

        if report.report_type == "shift_report":
            date_str = params.get("date") or ri.get("date")
            shift_name = params.get("shift") or ri.get("shift")
            team_id = params.get("team_id") or ri.get("team_id")
            if date_str and shift_name:
                aggregator = da_service.DataAggregator()
                auto_data = aggregator.get_aggregated_shift_data(
                    date_str, shift_name, team_id=team_id
                )
                data["breakdowns"] = auto_data.get("breakdowns", []) + _manual_only(
                    data.get("breakdowns", [])
                )
                data["break_activities"] = auto_data.get(
                    "break_activities", []
                ) + _manual_only(data.get("break_activities", []))
                data["engineering_support"] = auto_data.get(
                    "engineering_support", []
                ) + _manual_only(data.get("engineering_support", []))

                data["handover_from_previous"] = auto_data.get(
                    "handover_from_previous", []
                ) + _merge_handover_manual_lists(
                    data.get("handover_from_previous", []),
                    ri.get("handover_from_previous", []),
                )
                data["handover_to_next"] = auto_data.get(
                    "handover_to_next", []
                ) + _merge_handover_manual_lists(
                    data.get("handover_to_next", []),
                    ri.get("handover_to_next", []),
                )

                # Keep template sources synchronized to prevent stale duplicate sections
                ri["handover_from_previous"] = data.get("handover_from_previous", [])
                ri["handover_to_next"] = data.get("handover_to_next", [])
                data["shift_info"] = ri

        elif report.report_type == "weekend_report":
            weekend_date = params.get("weekend_date") or ri.get("date")
            team_id = params.get("team_id") or ri.get("team_id")
            shift_name = params.get("shift") or ri.get("shift") or data.get("shift")
            if weekend_date:
                aggregator = da_service.DataAggregator()
                auto_data = aggregator.get_aggregated_weekend_data(
                    weekend_date,
                    team_id=team_id,
                    shift=shift_name,
                )
                data["pms"] = auto_data.get("pms", []) + _manual_only(
                    data.get("pms", [])
                )
                data["mos_tickets"] = auto_data.get("mos_tickets", []) + _manual_only(
                    data.get("mos_tickets", [])
                )
                data["additional_tickets"] = auto_data.get(
                    "additional_tickets", []
                ) + _manual_only(data.get("additional_tickets", []))
                data["engineering_support"] = auto_data.get(
                    "engineering_support", []
                ) + _manual_only(data.get("engineering_support", []))
                data["handover_from_previous"] = auto_data.get(
                    "handover_from_previous", []
                ) + _merge_handover_manual_lists(
                    data.get("handover_from_previous", []),
                    ri.get("handover_from_previous", []),
                )
                data["handover_to_next"] = auto_data.get(
                    "handover_to_next", []
                ) + _merge_handover_manual_lists(
                    data.get("handover_to_next", []),
                    ri.get("handover_to_next", []),
                )
                ri["handover_from_previous"] = data.get("handover_from_previous", [])
                ri["handover_to_next"] = data.get("handover_to_next", [])
                ri["shift"] = shift_name
                data["shift"] = shift_name
    except Exception as e:
        current_app.logger.warning(f"Dynamic report refresh failed: {e}")

    # CRITICAL: Flatten handover data to top level for template compatibility
    # Weekend seeded reporting entries have handover data nested in report_info
    if report.report_type == "weekend_report":
        if "handover_from_previous" not in data:
            data["handover_from_previous"] = ri.get("handover_from_previous", [])
        if "handover_to_next" not in data:
            data["handover_to_next"] = ri.get("handover_to_next", [])

    # Select template based on report type
    template_name = "shift_report_detail.html"
    if report.report_type == "weekend_report":
        template_name = "weekend_report_detail.html"

    # Fetch teams for dropdowns
    # Get distinct team names from users
    teams = []
    try:
        # Query Team table directly for team names
        teams_query = db.session.query(Team.name).order_by(Team.name).all()
        teams = [t[0] for t in teams_query if t[0]]
    except Exception as e:
        current_app.logger.warning(f"Failed to fetch teams: {e}")
        # Standard fallback teams for mock data
        teams = [
            "Red Shift",
            "Blue Shift",
            "Green Shift",
            "Yellow Shift",
            "Team A",
            "Team B",
            "Team C",
            "Team D",
        ]

    # Fetch Assets for dropdowns
    assets = []
    asset_link_map = {}
    try:
        assets_query = (
            Asset.query.with_entities(Asset.id, Asset.asset_code)
            .order_by(Asset.asset_code)
            .all()
        )
        assets = [a[1] for a in assets_query]
        asset_link_map = {
            code: url_for("main.asset_detail", asset_id=asset_id)
            for asset_id, code in assets_query
            if code
        }
    except Exception as e:
        current_app.logger.warning(f"Failed to fetch assets: {e}")

    # Build MO link map for existing Maintenance Orders
    mo_link_map = {}
    mo_data_map = {}
    try:
        existing_mo_ids = [
            mo_id
            for (mo_id,) in MaintenanceOrder.query.with_entities(MaintenanceOrder.id)
            .order_by(MaintenanceOrder.id)
            .all()
        ]
        if existing_mo_ids and report.title and "Seeded" in report.title:

            def _normalize_mo_ids(items, key):
                for index, item in enumerate(items or []):
                    if not isinstance(item, dict):
                        continue
                    raw_mo = item.get(key)
                    match = re.search(r"\d+", str(raw_mo)) if raw_mo else None
                    if not match or int(match.group(0)) not in existing_mo_ids:
                        target_id = existing_mo_ids[index % len(existing_mo_ids)]
                        item[key] = f"MO-{target_id}"

            _normalize_mo_ids(data.get("break_activities", []), "mo_id")
            _normalize_mo_ids(data.get("mos_tickets", []), "id")
            _normalize_mo_ids(data.get("mos", []), "id")
            _normalize_mo_ids(data.get("additional_tickets", []), "id")

        mo_numbers = set()
        for section in [
            data.get("breakdowns", []),
            data.get("handover_from_previous", []),
            data.get("handover_to_next", []),
            (data.get("report_info") or {}).get("handover_from_previous", []),
            (data.get("report_info") or {}).get("handover_to_next", []),
            data.get("break_activities", []),
            data.get("engineering_support", []),
            data.get("activities", []),
            data.get("mos_tickets", []),
            data.get("mos", []),
            data.get("additional_tickets", []),
        ]:
            for item in section or []:
                if not isinstance(item, dict):
                    continue
                raw_mo = item.get("mo_id") or item.get("id")
                if not raw_mo:
                    continue
                match = re.search(r"\d+", str(raw_mo))
                if match:
                    mo_numbers.add(int(match.group(0)))
        if mo_numbers:
            existing_mos = MaintenanceOrder.query.filter(
                MaintenanceOrder.id.in_(mo_numbers)
            ).all()
            mo_link_map = {
                mo.id: url_for("main.mo_detail", mo_id=mo.id) for mo in existing_mos
            }
            # Build MO data map with actual database information
            for mo in existing_mos:
                asset_name = mo.asset.name if mo.asset else "Unknown Asset"
                asset_code = mo.asset.asset_code if mo.asset else "UNKNOWN"
                asset_url = (
                    url_for("main.asset_detail", asset_id=mo.asset.id)
                    if mo.asset
                    else None
                )
                mo_data_map[mo.id] = {
                    "asset_name": asset_name,
                    "asset_code": asset_code,
                    "asset_url": asset_url,
                    "title": mo.title or "",
                    "description": mo.description or "No description",
                    "status": mo.status or "Unknown",
                    "downtime_duration": mo.downtime_duration,
                    "root_cause": mo.root_cause,
                    "recovery": mo.recovery,
                    "created_at": (
                        mo.created_at.strftime("%H:%M") if mo.created_at else "N/A"
                    ),
                }
    except Exception as e:
        current_app.logger.warning(f"Failed to build MO links: {e}")

    # Build spare-part link map for description matching
    spare_part_link_map = {}
    try:
        parts_query = SparePart.query.with_entities(
            SparePart.id,
            SparePart.description,
            SparePart.manufacturer_part_id,
        ).all()
        for part_id, description, part_number in parts_query:
            if description:
                spare_part_link_map[description.strip().lower()] = url_for(
                    "main.spare_part_detail", part_id=part_id
                )
            if part_number:
                spare_part_link_map[part_number.strip().lower()] = url_for(
                    "main.spare_part_detail", part_id=part_id
                )
    except Exception as e:
        current_app.logger.warning(f"Failed to build spare part links: {e}")

    def linkify_spare_parts(text):
        """Build escaped HTML with optional spare-part links (template applies
        |safe)."""
        if not text:
            return ""

        raw_text = str(text)
        if not spare_part_link_map:
            return escape(raw_text)

        terms = sorted(
            (str(term) for term in spare_part_link_map.keys()),
            key=len,
            reverse=True,
        )
        pattern = re.compile(
            "|".join(re.escape(term) for term in terms),
            re.IGNORECASE,
        )

        parts = []
        last_index = 0
        for match in pattern.finditer(raw_text):
            start, end = match.span()
            parts.append(escape(raw_text[last_index:start]))
            matched_text = raw_text[start:end]
            link_url = spare_part_link_map.get(matched_text.lower())
            if link_url:
                safe_href = escape(link_url, quote=True)
                safe_text = escape(matched_text)
                parts.append(f'<a href="{safe_href}">{safe_text}</a>')
            else:
                parts.append(escape(matched_text))
            last_index = end

        parts.append(escape(raw_text[last_index:]))
        return "".join(parts)

    # Load config for metadata totals (equipment, technology)
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "config.json"
    )
    default_config_data = {
        "metadata_totals": {
            "attendance_total": 20,
            "vigel_total": 10,
            "mds_total": 15,
            "description": (
                "Total numbers for each equipment or technology type in shift "
                "reporting entries. "
                "Replace with your own values as needed."
            ),
        }
    }
    metadata_config = default_config_data["metadata_totals"]

    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                metadata_config = config.get("metadata_totals", metadata_config)
        else:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(default_config_data, f, indent=2)
            current_app.logger.info(f"Created default config at {config_path}")
    except Exception as e:
        current_app.logger.warning(f"Failed to load config: {e}")

    # Get technician count for attendance total
    technician_count = 0
    try:
        if data.get("attendance_total"):
            technician_count = int(data.get("attendance_total"))
        else:
            report_team = data.get("team_name", "")
            if not report_team and "report_info" in data:
                report_team = data["report_info"].get("team_name", "")

            if report_team:
                team_obj = Team.query.filter_by(name=report_team).first()
                if team_obj:
                    technician_count = User.query.filter_by(team=team_obj).count()

            if technician_count == 0:
                l_team = report_team.lower()
                if "red" in l_team or "team" not in l_team:
                    team_obj = Team.query.filter_by(name="Team A").first()
                    if team_obj:
                        technician_count = User.query.filter_by(team=team_obj).count()

            if technician_count == 0:
                from src.services.db_utils import Role

                tech_role = Role.query.filter_by(name="Technician").first()
                if tech_role:
                    technician_count = User.query.filter(
                        User.roles.contains(tech_role)
                    ).count()

            if technician_count == 0:
                technician_count = metadata_config.get("attendance_total", 20)

            attendance_val = int(data.get("attendance", 0))
            if attendance_val > technician_count or report_team in [
                "Team A",
                "Team B",
                "Team C",
                "Team D",
            ]:
                technician_count = metadata_config.get("attendance_total", 20)

    except Exception as e:
        current_app.logger.warning(f"Failed to count technicians: {e}")

    return render_template(
        template_name,
        report=report,
        data=data,
        teams=teams,
        assets=assets,
        asset_link_map=asset_link_map,
        mo_link_map=mo_link_map,
        mo_data_map=mo_data_map,
        linkify_spare_parts=linkify_spare_parts,
        vigel_total=metadata_config.get("vigel_total", 10),
        mds_total=metadata_config.get("mds_total", 15),
        technician_count=technician_count,
        report_data_json=_safe_json_for_template(data),
        report_meta_json=_safe_json_for_template(report.to_dict() if report else {}),
        report_mo_json=_safe_json_for_template(mo_data_map),
    )


@reporting_bp.route("/<int:report_id>/update", methods=["POST"])
@login_required
def update_report_data(report_id):
    """Update a specific section of the report data.

    Expects JSON payload with:
    - section: 'header', 'metadata', 'breakdown', etc.
    - index: index of item in list (if applicable)
    - action: 'edit', 'add', 'delete'
    - ... specific fields ...
    """
    report = report_models.Report.query.get_or_404(report_id)
    payload = request.get_json()

    if not payload:
        return {"success": False, "error": "No data provided"}, 400

    current_data = report.data or {}
    section = payload.get("section")
    action = payload.get("action")
    index = payload.get("index")
    report_type = str(getattr(report, "report_type", ""))

    # Helper to save
    def save():
        report.data = current_data
        # Force strict update
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(report, "data")
        db.session.commit()

    try:
        # --- HEADER ---
        if section == "header":
            new_team = payload.get("team_name")
            new_team_color = payload.get("team_color")
            current_data["team_name"] = new_team
            current_data["team_color"] = new_team_color

            # Standard: all report types use 'report_info'
            if "report_info" not in current_data:
                current_data["report_info"] = {}
            current_data["report_info"]["date"] = payload.get("date")
            current_data["report_info"]["shift"] = payload.get("shift")
            current_data["report_info"]["team_name"] = new_team
            current_data["report_info"]["team_color"] = new_team_color

            # Backward compatibility for shift reporting entries
            if report_type == "shift_report":
                current_data["shift_info"] = current_data["report_info"]

            # Weekend reporting entries also store shift at top level
            if report_type == "weekend_report":
                current_data["shift"] = payload.get("shift")

            # Update actual report title for DB persistence and UI consistency
            date = payload.get("date")
            shift = payload.get("shift")
            if date and shift:
                rtype_label = (
                    "Shift Report"
                    if report_type == "shift_report"
                    else "Weekend Shift Report"
                )
                new_title = f"{rtype_label} – {date} – {shift}"
                if new_team:
                    new_title += f" – {new_team}"
                report.title = new_title

            # Backward compatibility for non-weekend reporting entries
            if report_type != "weekend_report":
                if "shift_info" not in current_data or not isinstance(
                    current_data.get("shift_info"), dict
                ):
                    current_data["shift_info"] = current_data["report_info"]
                current_data["shift_info"]["date"] = payload.get("date")
                current_data["shift_info"]["shift"] = payload.get("shift")
                current_data["shift_info"]["team_name"] = new_team
                current_data["shift_info"]["team_color"] = new_team_color

            save()
            return {"success": True}

        # --- METADATA ---
        if section == "metadata":
            key = payload.get("key")
            value = payload.get("value")
            if key:
                current_data[key] = value
                save()
                return {"success": True}

        # --- HANDOVER ---
        if section in ["handover_from", "handover_to", "handover"]:
            # Standard: all report types use 'report_info'
            if section == "handover_from":
                if report_type == "weekend_report":
                    target_list = current_data.setdefault("handover_from_previous", [])
                else:
                    if "report_info" not in current_data:
                        current_data["report_info"] = {}
                    target_list = current_data.get("report_info", {}).get(
                        "handover_from_previous", []
                    )
                    if "handover_from_previous" not in current_data.get(
                        "report_info", {}
                    ):
                        current_data["report_info"]["handover_from_previous"] = []
                        target_list = current_data["report_info"][
                            "handover_from_previous"
                        ]
            elif section == "handover_to":
                if report_type == "weekend_report":
                    target_list = current_data.setdefault("handover_to_next", [])
                else:
                    if "report_info" not in current_data:
                        current_data["report_info"] = {}
                    target_list = current_data.get("report_info", {}).get(
                        "handover_to_next", []
                    )
                    if "handover_to_next" not in current_data.get("report_info", {}):
                        current_data["report_info"]["handover_to_next"] = []
                        target_list = current_data["report_info"]["handover_to_next"]
            else:
                # Weekend legacy / general
                target_list = current_data.get("handover_instructions", [])
                if "handover_instructions" not in current_data:
                    current_data["handover_instructions"] = []
                    target_list = current_data["handover_instructions"]

            # Construct Item
            item = payload.get("description")  # fallback
            # If we want detailed object:
            if payload.get("asset") or payload.get("title"):
                item = {
                    "asset": payload.get("asset"),
                    "title": payload.get("title"),
                    "description": payload.get("description"),
                }
                mo_id_payload = payload.get("mo_id") or payload.get("id")
                if mo_id_payload:
                    item["mo_id"] = mo_id_payload

            # ACTION
            if action == "edit" and index is not None:
                index = int(index)
                if 0 <= index < len(target_list):
                    if isinstance(item, dict) and isinstance(target_list[index], dict):
                        existing_mo = target_list[index].get("mo_id") or target_list[
                            index
                        ].get("id")
                        if existing_mo and not item.get("mo_id"):
                            item["mo_id"] = existing_mo
                    target_list[index] = item
            elif action == "add":
                target_list.append(item)
            elif action == "delete" and index is not None:
                index = int(index)
                if 0 <= index < len(target_list):
                    target_list.pop(index)

            # Keep shift backward-compatible key synchronized
            if report_type != "weekend_report":
                current_data["shift_info"] = current_data.get("report_info", {})

            # Keep weekend legacy and new keys synchronized
            if report_type == "weekend_report":
                if section == "handover_to":
                    current_data["handover_instructions"] = [
                        i.get("description", "") if isinstance(i, dict) else str(i)
                        for i in target_list
                    ]
                if section == "handover":
                    current_data["handover_to_next"] = target_list

            save()
            return {"success": True}

        # --- BREAKDOWNS ---
        if section == "breakdown":
            target_list = current_data.get("breakdowns", [])
            existing_item = None
            if action == "edit" and index is not None:
                idx = int(index)
                if 0 <= idx < len(target_list) and isinstance(target_list[idx], dict):
                    existing_item = target_list[idx]

            item = {
                "equipment_line": payload.get("asset")
                or payload.get("asset_code")
                or (existing_item.get("equipment_line") if existing_item else None),
                "asset": payload.get("asset")
                or payload.get("asset_code")
                or (existing_item.get("asset") if existing_item else None),
                "asset_code": payload.get("asset_code")
                or payload.get("asset")
                or (existing_item.get("asset_code") if existing_item else None),
                "timestamp": payload.get("timestamp"),
                "duration": payload.get("duration"),
                "description": payload.get("description"),
                "root_cause": payload.get("root_cause"),
                "resolution_notes": payload.get("resolution_notes"),
            }

            mo_id_payload = payload.get("mo_id") or payload.get("id")
            existing_mo_id = (
                (existing_item.get("mo_id") or existing_item.get("id"))
                if isinstance(existing_item, dict)
                else None
            )
            if mo_id_payload or existing_mo_id:
                item["mo_id"] = mo_id_payload or existing_mo_id

            if action == "edit" and index is not None:
                target_list[int(index)] = item
            elif action == "add":
                target_list.append(item)
            elif action == "delete" and index is not None:
                target_list.pop(int(index))

            current_data["breakdowns"] = target_list
            save()
            return {"success": True}

        # --- ACTIVITIES (Generic Add / Specific Edit) ---
        # Handle 'activities' (Add), 'flux_tickets' (Edit/Del),
        # 'engineering_support' (Edit/Del)
        if section in ["activities", "flux_tickets", "engineering_support"]:
            # Determine target list based on section or type (for Add)
            target_key = "break_activities"  # Default
            target_list = []

            # If explicit section (Edit/Delete)
            if section == "flux_tickets":
                target_key = "break_activities"
            elif section == "engineering_support":
                target_key = "engineering_support"
            elif section == "activities" and action == "add":
                # For ADD via generic modal, check type from payload
                act_type = payload.get("type", "flux_ticket")
                if act_type == "flux_ticket":
                    target_key = "break_activities"
                else:
                    target_key = "engineering_support"

            # Fetch current list
            target_list = current_data.get(target_key, [])
            if not target_list and target_key in current_data:
                # target_list = current_data[target_key]
                # Use retrieval by key directly if get returned empty list but key
                # exists
                target_list = current_data[target_key]

            # Construct Item
            item = {
                "asset": payload.get("asset"),
                "title": payload.get("title"),  # For Eng Support
                "description": payload.get("description"),
                "type": payload.get("type"),  # For FLUX
                "mo_id": payload.get("mo_id"),  # For FLUX
                "status": payload.get("status"),  # For FLUX
            }

            if action == "edit" and index is not None:
                # For FLUX tickets, we need to be careful if list is mixed?
                # No, break_activities is list of all Flux tickets usually.
                # But engineering_support is separate key.
                if 0 <= int(index) < len(target_list):
                    target_list[int(index)] = item
            elif action == "add":
                target_list.append(item)
            elif action == "delete" and index is not None:
                if 0 <= int(index) < len(target_list):
                    target_list.pop(int(index))

            current_data[target_key] = target_list
            save()
            return {"success": True}

        # --- TASKS (PMs / MOs) ---
        if section in ["pms", "mos", "additional"]:
            key_map = {
                "pms": "pms",
                "mos": "mos",
                "additional": "additional_tickets",  # Check exact key in weekend data
            }
            key = key_map.get(section, section)
            target_list = current_data.get(key, [])

            item = {
                "asset": payload.get("asset"),
                "description": payload.get("description"),
                "status": payload.get("status"),
            }
            if payload.get("id"):
                item["id"] = payload.get("id")

            if action == "edit" and index is not None:
                target_list[int(index)] = item
            elif action == "add":
                target_list.append(item)
            elif action == "delete" and index is not None:
                target_list.pop(int(index))

            current_data[key] = target_list
            save()
            return {"success": True}

        # Fallback
        return {"success": False, "error": "Unknown section or action"}, 400

    except Exception as e:
        current_app.logger.error(f"Update failed: {e}")
        return {"success": False, "error": str(e)}, 500


@reporting_bp.route("/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = report_models.Report.query.get_or_404(report_id)
    if report.file_path and os.path.exists(report.file_path):
        return send_file(report.file_path, as_attachment=True)
    else:
        # Generate on the fly if missing?
        flash("File not found. Try Export options.", "danger")
        return redirect(url_for("reporting.report_detail", report_id=report_id))


@reporting_bp.route("/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_report(report_id):
    report = report_models.Report.query.get_or_404(report_id)
    try:
        # Optional: Delete file
        if report.file_path and os.path.exists(report.file_path):
            os.remove(report.file_path)

        db.session.delete(report)
        db.session.commit()
        flash("Report deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting report: {e}", "danger")

    return redirect(url_for("reporting.index"))


@reporting_bp.route("/<int:report_id>/export/<fmt>")
@login_required
def export_report(report_id, fmt):
    """On-the-fly export of a report to a different format.

    Regenerates the report content using the stored DB data.
    """
    report = report_models.Report.query.get_or_404(report_id)

    # Get valye from DB
    data = report.data

    # Fallback to file if DB empty
    if (
        not data
        and report.file_path
        and report.file_path.endswith(".json")
        and os.path.exists(report.file_path)
    ):
        with open(report.file_path, "r") as f:
            data = json.load(f)

    if not data:
        flash("Source data for this report is missing. Cannot export.", "danger")
        return redirect(url_for("reporting.report_detail", report_id=report_id))

    # Ensure report_type is in data for proper format detection
    if "report_type" not in data:
        data["report_type"] = report.report_type

    # CRITICAL: Dynamically refresh data from database before export
    # This matches what report_detail does for UI display
    try:
        # Ensure report_info exists for data aggregation
        if "report_info" not in data:
            if report.report_type == "shift_report" and "shift_info" in data:
                data["report_info"] = data["shift_info"]
            elif report.report_type == "weekend_report" and "weekend_info" in data:
                data["report_info"] = data["weekend_info"]
            else:
                data["report_info"] = {}

        ri = data["report_info"]
        params = report.parameters if isinstance(report.parameters, dict) else {}

        def _manual_only(items):
            """Filter out items that are linked to MOs (auto-generated)."""
            manual_items = []
            for entry in items or []:
                if isinstance(entry, dict):
                    if entry.get("mo_id") or entry.get("id"):
                        continue
                    manual_items.append(entry)
                else:
                    manual_items.append(entry)
            return manual_items

        # Refresh shift report data
        if report.report_type == "shift_report":
            date_str = params.get("date") or ri.get("date")
            shift_name = params.get("shift") or ri.get("shift")
            team_id = params.get("team_id") or ri.get("team_id")
            if date_str and shift_name:
                aggregator = da_service.DataAggregator()
                auto_data = aggregator.get_aggregated_shift_data(
                    date_str, shift_name, team_id=team_id
                )
                # Merge auto-generated data with manual entries
                data["breakdowns"] = auto_data.get("breakdowns", []) + _manual_only(
                    data.get("breakdowns", [])
                )
                data["break_activities"] = auto_data.get(
                    "break_activities", []
                ) + _manual_only(data.get("break_activities", []))
                data["engineering_support"] = auto_data.get(
                    "engineering_support", []
                ) + _manual_only(data.get("engineering_support", []))
                data["handover_from_previous"] = auto_data.get(
                    "handover_from_previous", []
                ) + _manual_only(data.get("handover_from_previous", []))
                data["handover_to_next"] = auto_data.get(
                    "handover_to_next", []
                ) + _manual_only(data.get("handover_to_next", []))

        # Refresh weekend report data
        elif report.report_type == "weekend_report":
            weekend_date = params.get("weekend_date") or ri.get("date")
            team_id = params.get("team_id") or ri.get("team_id")
            shift_name = params.get("shift") or ri.get("shift") or data.get("shift")
            if weekend_date:
                aggregator = da_service.DataAggregator()
                auto_data = aggregator.get_aggregated_weekend_data(
                    weekend_date, team_id=team_id, shift=shift_name
                )
                # Merge auto-generated data with manual entries
                data["pms"] = auto_data.get("pms", []) + _manual_only(
                    data.get("pms", [])
                )
                data["mos_tickets"] = auto_data.get("mos_tickets", []) + _manual_only(
                    data.get("mos_tickets", [])
                )
                data["additional_tickets"] = auto_data.get(
                    "additional_tickets", []
                ) + _manual_only(data.get("additional_tickets", []))
                data["handover_from_previous"] = auto_data.get(
                    "handover_from_previous", []
                ) + _manual_only(data.get("handover_from_previous", []))
                data["handover_to_next"] = auto_data.get(
                    "handover_to_next", []
                ) + _manual_only(data.get("handover_to_next", []))

    except Exception as e:
        current_app.logger.warning(f"Dynamic data refresh for export failed: {e}")
        # Continue with static data if refresh fails

    # Generate the requested format
    generator = rg_service.ReportGenerator()

    export_title = f"{report.title}_export_{fmt}"

    try:
        target_fmt = fmt
        # if fmt == "txt":
        #    target_fmt = "markdown"

        # Handle parameters - could be dict (from JSON column) or string
        params = report.parameters
        if isinstance(params, str):
            params = json.loads(params)
        elif params is None:
            params = {}

        new_file_path = generator.generate_report(
            report.report_type,
            export_title,
            params,
            target_fmt,
            session.get("user_id"),
            data=data,
        )

        if new_file_path and os.path.exists(new_file_path):
            return send_file(
                new_file_path,
                as_attachment=True,
                download_name=os.path.basename(new_file_path),
            )
        else:
            flash("Export file could not be created.", "danger")

    except Exception as e:
        current_app.logger.error(f"Export failed: {e}")
        flash(f"Export failed: {e}", "danger")

    return redirect(url_for("reporting.report_detail", report_id=report_id))
