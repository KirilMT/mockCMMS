# src/routes/main.py

import calendar
import json
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import joinedload

from src.services.db_utils import (
    Asset,
    MaintenanceOrder,
    Role,
    SatellitePoint,
    SparePart,
    Team,
    User,
    db,
)
from src.services.shift_utils import get_shift_teams

main_bp = Blueprint("main", __name__)


# --- Authentication Helper ---
def login_required(f):
    """Decorator to ensure a user is logged in before accessing a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Login required to access this page.", "warning")
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)

    return decorated_function


# --- Data Fetching Helpers ---
def _get_technicians_and_teams():
    """Fetches all users with the 'Technician' role and all teams."""
    technician_role = Role.query.filter_by(name="Technician").first()
    technicians = (
        User.query.filter(User.roles.contains(technician_role)).all()
        if technician_role
        else []
    )
    teams = Team.query.all()
    return technicians or [], teams or []


def _resolve_assignees_from_tokens(assignee_tokens):
    """Resolve user:/team: assignee tokens to User records."""
    users = []
    seen_ids = set()

    for token in assignee_tokens or []:
        if not isinstance(token, str):
            continue
        value = token.strip()
        if not value:
            continue

        if value.startswith("user:"):
            username = value.split(":", 1)[1].strip()
            user = User.query.filter_by(username=username).first()
            if user and user.id not in seen_ids:
                users.append(user)
                seen_ids.add(user.id)
            continue

        if value.startswith("team:"):
            team_name = value.split(":", 1)[1].strip()
            team = Team.query.filter_by(name=team_name).first()
            if not team:
                continue
            for user in User.query.filter_by(team_id=team.id).all():
                if user.id not in seen_ids:
                    users.append(user)
                    seen_ids.add(user.id)

    return users


def _get_selected_assignees_for_form(mo):
    """Build selected assignee tokens for MO form prefill."""
    selected = []

    if mo.assignees_json:
        try:
            parsed = json.loads(mo.assignees_json)
            if isinstance(parsed, list):
                selected.extend(str(item) for item in parsed if item)
        except (TypeError, json.JSONDecodeError):
            selected = []

    if not selected and getattr(mo, "assignees", None):
        selected = [f"user:{user.username}" for user in mo.assignees if user.username]

    return selected


# --- Form Processing Helper for Maintenance Orders ---
def _process_mo_form(mo, form_data):
    """Processes form data for creating or updating a MaintenanceOrder."""
    mo.asset_id = form_data.get("asset_id")
    mo.title = form_data.get("title")  # New field
    mo.description = form_data.get("description")
    mo.category = form_data.get("category")  # New field

    order_type_raw = (form_data.get("order_type") or "").strip()
    order_type_map = {
        "pm": "PM",
        "reactive": "Reactive",
        "corrective": "Corrective",
    }
    mo.order_type = order_type_map.get(order_type_raw.lower(), order_type_raw)
    mo.priority = form_data.get("priority")

    # Get estimated_time early for PM validation
    estimated_time = form_data.get("estimated_completion_time", "")

    # PM-specific fields
    schedule_name = form_data.get("schedule_name", "")
    frequency = form_data.get("frequency", "")
    if mo.order_type == "PM":
        if not frequency:
            flash(
                "Frequency is required for PM (Preventive Maintenance) orders.",
                "error",
            )
            return False
        if not schedule_name:
            flash(
                "Schedule Name is required for PM (Preventive Maintenance) orders.",
                "error",
            )
            return False
        if not estimated_time:
            flash(
                "Estimated Time is required for PM (Preventive Maintenance) orders.",
                "error",
            )
            return False

    mo.schedule_name = schedule_name if schedule_name else None
    mo.frequency = frequency if frequency else None

    # Optional & other fields
    mo.estimated_completion_time = (
        int(estimated_time) if estimated_time and estimated_time.isdigit() else None
    )

    labour_count = form_data.get("labour_count", "1")
    mo.labour_count = int(labour_count) if labour_count.isdigit() else 1

    assignees_list = request.form.getlist("assignees")
    mo.assignees_json = json.dumps(assignees_list) if assignees_list else None
    mo.assignees = _resolve_assignees_from_tokens(assignees_list)

    justification = form_data.get("justification", "")
    mo.justification = justification if justification else None

    # Breakdown-specific fields (Reactive MOs can leave these blank)
    downtime_duration = form_data.get("downtime_duration", "")
    root_cause = form_data.get("root_cause", "")
    recovery = form_data.get("recovery", "")

    mo.downtime_duration = (
        int(downtime_duration)
        if downtime_duration and downtime_duration.isdigit()
        else None
    )
    mo.root_cause = root_cause if root_cause else None
    mo.recovery = recovery if recovery else None

    due_date_str = form_data.get("due_date", "")
    mo.due_date = datetime.strptime(due_date_str, "%Y-%m-%d") if due_date_str else None

    # Set timestamps for edits
    if mo.id:  # If the MO already exists
        mo.modified_by = session.get("user_id")
        mo.modified_on = datetime.now(timezone.utc)
    else:  # For new MOs
        mo.status = "Open"
        mo.created_by = session.get("user_id")

    # Handle status for existing MOs
    if "status" in form_data:
        mo.status = form_data.get("status")

    return True


# --- Calendar Generation Helper ---
def _generate_calendar_data(year, month):
    """Generates the data structure required for the shift calendar template."""
    teams = Team.query.options(joinedload(Team.users)).all()
    calendar_days = []

    # Get the first day of the month
    first_day = datetime(year, month, 1)
    # 0 = Monday, 6 = Sunday
    start_weekday = first_day.weekday()

    # Calculate the start date of the calendar grid (last Monday)
    current_date = first_day - timedelta(days=start_weekday)

    # Calculate end of month
    _, num_days_in_month = calendar.monthrange(year, month)
    last_day = datetime(year, month, num_days_in_month)

    # Calculate end date of the calendar grid (next Sunday)
    end_date = last_day + timedelta(days=(6 - last_day.weekday()))

    while current_date <= end_date:
        early_team, late_team = get_shift_teams(current_date, teams)

        day_data = {
            "date_str": current_date.strftime("%Y-%m-%d"),
            "day_num": current_date.day,
            "day_name": current_date.strftime("%A"),
            "week_num": current_date.isocalendar()[1],
            "is_today": current_date.date() == datetime.now().date(),
            "is_current_month": current_date.month == month,
            "early_teams": (
                [
                    {
                        "name": early_team.name,
                        "users": [{"username": u.username} for u in early_team.users],
                    }
                ]
                if early_team
                else []
            ),
            "late_teams": (
                [
                    {
                        "name": late_team.name,
                        "users": [{"username": u.username} for u in late_team.users],
                    }
                ]
                if late_team
                else []
            ),
        }
        calendar_days.append(day_data)
        current_date += timedelta(days=1)

    return calendar_days


# --- General Routes ---
@main_bp.route("/")
def index():
    return redirect(url_for("main.assets"))


@main_bp.route("/tickets/<string:ticket_id>")
def ticket_page(ticket_id):
    return render_template("ticket.html", ticket_id=ticket_id)


@main_bp.route("/maintenance_grid/<string:ids>")
def maintenance_grid_page(ids):
    return render_template("maintenance_grid.html", ids=ids)


# --- Asset Routes ---
@main_bp.route("/assets")
@login_required
def assets():
    all_assets = Asset.query.all()
    return render_template(
        "assets.html", assets=[asset.to_dict() for asset in all_assets]
    )


@main_bp.route("/assets/add", methods=["GET", "POST"])
@login_required
def add_asset():
    if request.method == "POST":
        asset_code = request.form.get("asset_code")
        name = request.form.get("name")
        description = request.form.get("description", "")
        asset_type = request.form.get("asset_type")
        cost_center = request.form.get("cost_center")
        status = request.form.get("status")

        if not asset_code or not name:
            flash("Asset code and name are required.", "error")
            return (
                render_template("asset_detail.html", asset=None, active_mos=[]),
                400,
            )

        new_asset = Asset(
            asset_code=asset_code,
            name=name,
            description=description,
            asset_type=asset_type,
            cost_center=cost_center,
            status=status,
        )
        db.session.add(new_asset)
        db.session.commit()
        flash("Asset added successfully!", "success")
        return redirect(url_for("main.assets"))
    return render_template("asset_detail.html", asset=None, active_mos=[])


@main_bp.route("/assets/<int:asset_id>")
@login_required
def asset_detail(asset_id):
    asset = db.get_or_404(Asset, asset_id)
    active_mos = [mo.to_dict() for mo in asset.maintenance_orders]
    return render_template("asset_detail.html", asset=asset, active_mos=active_mos)


@main_bp.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
@login_required
def edit_asset(asset_id):
    asset = db.get_or_404(Asset, asset_id)
    if request.method == "POST":
        asset.asset_code = request.form["asset_code"]
        asset.name = request.form["name"]
        asset.description = request.form["description"]
        asset.asset_type = request.form["asset_type"]
        asset.cost_center = request.form["cost_center"]
        asset.status = request.form["status"]
        db.session.commit()
        flash("Asset updated successfully!", "success")
        return redirect(url_for("main.assets"))
    active_mos = [mo.to_dict() for mo in asset.maintenance_orders]
    return render_template("asset_detail.html", asset=asset, active_mos=active_mos)


@main_bp.route("/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
def delete_asset(asset_id):
    asset = db.get_or_404(Asset, asset_id)
    db.session.delete(asset)
    db.session.commit()
    flash("Asset deleted successfully!", "success")
    return redirect(url_for("main.assets"))


# --- Maintenance Order Routes ---
@main_bp.route("/maintenance_orders")
@login_required
def maintenance_orders():
    all_mos = MaintenanceOrder.query.all()
    return render_template(
        "maintenance_orders.html", mos=[mo.to_dict() for mo in all_mos]
    )


@main_bp.route("/maintenance_orders/add", methods=["GET", "POST"])
@login_required
def add_mo():
    technicians, teams = _get_technicians_and_teams()
    assets = Asset.query.all()
    return_to = request.args.get("return_to")
    asset_id = request.args.get("asset_id")
    preselected_asset = db.session.get(Asset, asset_id) if asset_id else None

    if request.method == "POST":
        new_mo = MaintenanceOrder()
        if _process_mo_form(new_mo, request.form):
            db.session.add(new_mo)
            db.session.commit()
            flash("Maintenance Order added successfully!", "success")
            if return_to == "asset" and new_mo.asset_id:
                return redirect(url_for("main.asset_detail", asset_id=new_mo.asset_id))
            return redirect(url_for("main.maintenance_orders"))
        # If processing fails, fall through to render the form again

    return render_template(
        "maintenance_order_detail.html",
        mo=None,
        assets=assets,
        technicians=technicians,
        teams=teams,
        return_to=return_to,
        asset_id=asset_id,
        preselected_asset=preselected_asset,
    )


@main_bp.route("/maintenance_orders/<int:mo_id>")
@login_required
def mo_detail(mo_id):
    mo = db.get_or_404(MaintenanceOrder, mo_id)
    technicians, teams = _get_technicians_and_teams()
    assets = Asset.query.all()
    selected_assignees = _get_selected_assignees_for_form(mo)
    asset_id = request.args.get("asset_id")

    return render_template(
        "maintenance_order_detail.html",
        mo=mo,
        assets=assets,
        technicians=technicians,
        teams=teams,
        selected_assignees=selected_assignees,
        asset_id=asset_id,
        return_to="asset" if asset_id else None,
    )


@main_bp.route("/maintenance_orders/<int:mo_id>/edit", methods=["GET", "POST"])
@login_required
def edit_mo(mo_id):
    mo = db.get_or_404(MaintenanceOrder, mo_id)
    technicians, teams = _get_technicians_and_teams()
    assets = Asset.query.all()
    return_to = request.args.get("return_to")
    asset_id = request.args.get("asset_id")

    if request.method == "POST":
        if _process_mo_form(mo, request.form):
            db.session.commit()
            flash("Maintenance Order updated successfully!", "success")
            if return_to == "asset" and asset_id:
                return redirect(url_for("main.asset_detail", asset_id=asset_id))
            return redirect(url_for("main.maintenance_orders"))
        # If processing fails, fall through to render the form again

    selected_assignees = _get_selected_assignees_for_form(mo)
    return render_template(
        "maintenance_order_detail.html",
        mo=mo,
        assets=assets,
        technicians=technicians,
        teams=teams,
        selected_assignees=selected_assignees,
        return_to=return_to,
        asset_id=asset_id,
    )


@main_bp.route("/maintenance_orders/<int:mo_id>/delete", methods=["POST"])
@login_required
def delete_mo(mo_id):
    mo = db.get_or_404(MaintenanceOrder, mo_id)
    asset_id = mo.asset_id
    try:
        db.session.delete(mo)
        db.session.commit()
        flash("Maintenance Order deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting Maintenance Order: {e}", "danger")

    if request.referrer and f"/assets/{asset_id}" in request.referrer:
        return redirect(url_for("main.asset_detail", asset_id=asset_id))
    return redirect(url_for("main.maintenance_orders"))


# --- Spare Part Routes ---
@main_bp.route("/spare_parts")
@login_required
def spare_parts():
    all_parts = SparePart.query.all()
    return render_template(
        "spare_parts.html", spare_parts=[part.to_dict() for part in all_parts]
    )


@main_bp.route("/spare_parts/add", methods=["GET", "POST"])
@login_required
def add_spare_part():
    if request.method == "POST":
        new_part = SparePart(
            description=request.form["description"],
            manufacturer=request.form["manufacturer"],
            manufacturer_part_id=request.form["manufacturer_part_id"],
            stock_quantity=request.form["stock_quantity"],
            location=request.form["location"],
            min_quantity=request.form["min_quantity"],
        )
        db.session.add(new_part)
        db.session.commit()
        flash("Spare Part added successfully!", "success")
        return redirect(url_for("main.spare_parts"))
    return render_template("spare_part_detail.html", part=None)


@main_bp.route("/spare_parts/<int:part_id>")
@login_required
def spare_part_detail(part_id):
    part = db.get_or_404(SparePart, part_id)
    return render_template("spare_part_detail.html", part=part)


@main_bp.route("/spare_parts/<int:part_id>/edit", methods=["GET", "POST"])
@login_required
def edit_spare_part(part_id):
    part = db.get_or_404(SparePart, part_id)
    if request.method == "POST":
        part.description = request.form["description"]
        part.manufacturer = request.form["manufacturer"]
        part.manufacturer_part_id = request.form["manufacturer_part_id"]
        part.stock_quantity = request.form["stock_quantity"]
        part.location = request.form["location"]
        part.min_quantity = request.form["min_quantity"]
        db.session.commit()
        flash("Spare Part updated successfully!", "success")
        return redirect(url_for("main.spare_parts"))
    return render_template("spare_part_detail.html", part=part)


@main_bp.route("/spare_parts/<int:part_id>/delete", methods=["POST"])
@login_required
def delete_spare_part(part_id):
    part = db.get_or_404(SparePart, part_id)
    db.session.delete(part)
    db.session.commit()
    flash("Spare Part deleted successfully!", "success")
    return redirect(url_for("main.spare_parts"))


# --- User and Role Routes ---
@main_bp.route("/users")
@login_required
def users():
    all_users = User.query.options(
        db.joinedload(User.roles), db.joinedload(User.team)
    ).all()
    return render_template(
        "users.html", users=[user.to_dict(include_roles=True) for user in all_users]
    )


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("main.register"))

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        roles_selected = request.form.getlist("roles")
        for role_name in roles_selected:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                new_user.roles.append(role)

        # Handle Team Assignment
        team_id = request.form.get("team_id")
        if team_id:
            new_user.team_id = int(team_id)

        # Handle Satellite Point Assignment
        sp_id = request.form.get("satellite_point_id")
        if sp_id:
            new_user.satellite_point_id = int(sp_id)

        db.session.add(new_user)
        db.session.commit()
        flash("User registered successfully!", "success")
        return redirect(url_for("main.users"))

    return render_template(
        "user_detail.html",
        user=None,
        all_roles=Role.query.all(),
        all_teams=Team.query.all(),
        all_satellite_points=SatellitePoint.query.all(),
    )


@main_bp.route("/users/<int:user_id>")
@login_required
def user_detail(user_id):
    user = db.get_or_404(User, user_id)
    is_technician = any(role.name == "Technician" for role in user.roles)
    return render_template(
        "user_detail.html",
        user=user,
        all_roles=Role.query.all(),
        all_teams=Team.query.all(),
        all_satellite_points=SatellitePoint.query.all(),
        is_technician=is_technician,
    )


@main_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    if request.method == "POST":
        user.username = request.form["username"]
        user.email = request.form["email"]

        password = request.form.get("password")
        if password:
            user.set_password(password)

        user.is_active = "is_active" in request.form

        user.roles.clear()
        roles_selected = request.form.getlist("roles")
        for role_name in roles_selected:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                user.roles.append(role)

        # Handle Team Assignment
        team_id = request.form.get("team_id")
        if team_id:
            user.team_id = int(team_id)
        else:
            user.team_id = None

        # Handle Satellite Point Assignment
        sp_id = request.form.get("satellite_point_id")
        if sp_id:
            user.satellite_point_id = int(sp_id)
        else:
            user.satellite_point_id = None

        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("main.users"))

    is_technician = any(role.name == "Technician" for role in user.roles)
    return render_template(
        "user_detail.html",
        user=user,
        all_roles=Role.query.all(),
        all_teams=Team.query.all(),
        is_technician=is_technician,
    )


@main_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("main.users"))


# --- Authentication Routes ---
@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            session["user_id"] = user.id
            session["username"] = user.username
            # Initialize session activity tracking
            session["last_active"] = datetime.now(timezone.utc).timestamp()
            # Ensure session is not permanent (cleared on browser close)
            session.permanent = False
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@main_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


# --- Deprecated & Planning Routes ---
@main_bp.route("/technicians/<int:technician_id>")
@login_required
def technician_detail(technician_id):
    flash("Technician view is deprecated. Please use the User view.", "warning")
    return redirect(url_for("main.user_detail", user_id=technician_id))


@main_bp.route("/planning")
@login_required
def planning():
    return redirect(url_for("planning.planning_index"))


@main_bp.route("/shift_calendar")
@login_required
def shift_calendar():
    year = request.args.get("year", type=int, default=datetime.now().year)
    month = request.args.get("month", type=int, default=datetime.now().month)

    # Navigation logic
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    context = {
        "calendar_days": _generate_calendar_data(year, month),
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }
    return render_template("shift_calendar.html", **context)
