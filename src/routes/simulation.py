"""Simulation routes for generating test data and simulating events."""

from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.services.db_utils import Asset, MaintenanceOrder, Role, SparePart, User, db
from src.services.simulation_service import DataSimulationService

simulation_bp = Blueprint("simulation", __name__, url_prefix="/simulation")


@simulation_bp.route("/")
def index():
    """Render the simulation dashboard."""
    # Get stats for the dashboard
    total_assets = Asset.query.count()
    total_mos = MaintenanceOrder.query.count()
    # Count all users
    total_users = User.query.count()
    total_parts = SparePart.query.count()

    # Get recent breakdowns (Reactive orders created recently)
    recent_breakdowns = (
        MaintenanceOrder.query.filter(
            MaintenanceOrder.order_type.in_(["Reactive", "Emergency"])
        )
        .order_by(MaintenanceOrder.created_at.desc())
        .limit(5)
        .all()
    )

    # Get technicians for the availability control (Keep this for the dropdown)
    technicians = User.query.join(User.roles).filter(Role.name == "Technician").all()

    return render_template(
        "simulation/index.html",
        total_assets=total_assets,
        total_mos=total_mos,
        total_users=total_users,
        total_parts=total_parts,
        recent_breakdowns=recent_breakdowns,
        technicians=technicians,
    )


@simulation_bp.route("/generate", methods=["POST"])
def generate_data():
    """Generate bulk random data."""
    try:
        data_type = request.form.get("type")
        count = int(request.form.get("count", 10))

        if data_type == "assets":
            DataSimulationService.generate_random_assets(count)
            flash(f"Successfully generated {count} assets.", "success")
        elif data_type == "users" or data_type == "technicians":
            # "technicians" kept for backward compatibility if UI sends it
            DataSimulationService.generate_random_users(count)
            flash(f"Successfully generated {count} users.", "success")
        elif data_type == "orders":
            DataSimulationService.generate_random_orders(count)
            flash(f"Successfully generated {count} maintenance orders.", "success")
        elif data_type == "spare_parts":
            DataSimulationService.generate_random_spare_parts(count)
            flash(f"Successfully generated {count} spare parts.", "success")
        else:
            flash("Invalid data type selected.", "error")

    except Exception as e:
        flash(f"Simulation failed: {str(e)}", "error")

    return redirect(url_for("simulation.index"))


@simulation_bp.route("/trigger-breakdown", methods=["POST"])
def trigger_breakdown():
    """Simulate a sudden machine breakdown."""
    try:
        # Pick a random operational asset
        asset = (
            Asset.query.filter_by(status="Operational")
            .order_by(db.func.random())
            .first()
        )

        if not asset:
            flash("No operational assets available to break down!", "warning")
            return redirect(url_for("simulation.index"))

        # Update asset status
        asset.status = "Offline"

        # Create Emergency Work Order (Using 'Reactive' as per strict enum config)
        mo = MaintenanceOrder(
            description=f"🚨 BREAKDOWN: {asset.name} - Simulated Failure",
            asset_id=asset.id,
            order_type="Reactive",
            status="Open",
            priority="Critical",
            created_at=datetime.now(timezone.utc),
            schedule_name="Unplanned Breakdown",
            labour_count=2,
            justification="Simulated immediate failure via Simulation Tools",
        )

        db.session.add(mo)
        db.session.commit()

        flash(
            f"💥 Breakdown on {asset.asset_code}! MO #{mo.id} created.",
            "error",
        )

    except Exception as e:
        flash(f"Failed to trigger breakdown: {str(e)}", "error")

    return redirect(url_for("simulation.index"))


@simulation_bp.route("/set-availability", methods=["POST"])
def set_availability():
    """Set a technician's availability status."""
    try:
        user_id = request.form.get("user_id")
        status = request.form.get("status")

        user = db.session.get(User, user_id)
        if user:
            user.availability_status = status
            db.session.commit()
            flash(f"Updated {user.username}'s status to {status}", "success")
        else:
            flash("User not found.", "error")

    except Exception as e:
        flash(f"Failed to update status: {str(e)}", "error")

    return redirect(url_for("simulation.index"))
