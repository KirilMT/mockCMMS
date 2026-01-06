from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    send_file,
    current_app,
)
import sys
import os
from functools import wraps
from datetime import datetime, timedelta

# Add the main src directory to the path to import from mockCMMS
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from ..services.report_generator import ReportGenerator
from .weekend_report import weekend_bp
from .shift_report import shift_bp
from .incidents import incidents_bp


def get_db_connection():
    """Get database connection using current app's SQLAlchemy."""
    from flask_sqlalchemy import SQLAlchemy

    db = current_app.extensions["sqlalchemy"]
    return db


reports_bp = Blueprint(
    "reports", __name__, url_prefix="/reports", template_folder="../templates"
)

# Register sub-blueprints
reports_bp.register_blueprint(weekend_bp)
reports_bp.register_blueprint(shift_bp)
reports_bp.register_blueprint(incidents_bp)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Login required to access this page.", "warning")
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@reports_bp.route("/")
@login_required
def reports():
    try:
        db = get_db_connection()

        # Check if reports table exists
        check_query = (
            "SELECT name FROM sqlite_master WHERE type='table' AND name='reports'"
        )
        result = db.session.execute(db.text(check_query))
        table_exists = result.fetchone() is not None

        if not table_exists:
            # Return empty reports list if table doesn't exist
            reports_data = []
        else:
            # Use raw SQL to avoid SQLAlchemy instance conflicts
            query = """
            SELECT r.id, r.title, r.report_type, r.format, r.generated_on, r.parameters, r.file_path,
                   u.username as generated_by_name
            FROM reports r
            LEFT JOIN users u ON r.generated_by = u.id
            ORDER BY r.generated_on DESC
            """

            result = db.session.execute(db.text(query))
            reports_data = []

            for row in result:
                reports_data.append(
                    {
                        "id": row.id,
                        "title": row.title,
                        "report_type": row.report_type,
                        "format": row.format,
                        "generated_on": (
                            row.generated_on.isoformat() if row.generated_on else None
                        ),
                        "generated_by_name": row.generated_by_name or "Unknown",
                        "parameters": row.parameters,
                        "file_path": row.file_path,
                    }
                )

        return render_template("reports.html", reports=reports_data)
    except Exception as e:
        flash(
            f"Reports feature is not yet available. Database setup required.", "warning"
        )
        return render_template("reports.html", reports=[])


@reports_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate_report():
    if request.method == "POST":
        flash(
            "Report generation is not yet available. Database setup required.",
            "warning",
        )
        return redirect(url_for("reports.reports"))

    return render_template("report_generate.html")


@reports_bp.route("/<int:report_id>")
@login_required
def report_detail(report_id):
    flash("Report details not available. Database setup required.", "warning")
    return redirect(url_for("reports.reports"))


@reports_bp.route("/<int:report_id>/download")
@login_required
def download_report(report_id):
    flash("Report download not available. Database setup required.", "warning")
    return redirect(url_for("reports.reports"))


@reports_bp.route("/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_report(report_id):
    flash("Report deletion not available. Database setup required.", "warning")
    return redirect(url_for("reports.reports"))
