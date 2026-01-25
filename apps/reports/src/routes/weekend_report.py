from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, send_file, session

from apps.reports.src.services.data_aggregator import DataAggregator
from apps.reports.src.services.report_generator import ReportGenerator

weekend_bp = Blueprint(
    "weekend", __name__, url_prefix="/weekend", template_folder="../templates"
)


@weekend_bp.route("/", methods=["GET"])
def weekend_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Default to last weekend if not provided
    if not start_date or not end_date:
        today = datetime.now()
        # Find last Saturday
        idx = (today.weekday() + 1) % 7
        saturday = today - timedelta(7 + idx - 6)
        sunday = saturday + timedelta(days=1)
        start_date = saturday.strftime("%Y-%m-%d")
        end_date = sunday.strftime("%Y-%m-%d")

    aggregator = DataAggregator()
    tasks = aggregator.get_weekend_tasks(start_date, end_date)

    generator = ReportGenerator()
    stats = generator.generate_summary_stats({"tasks": tasks})

    return render_template(
        "weekend_report.html",
        tasks=tasks,
        stats=stats,
        start_date=start_date,
        end_date=end_date,
    )


@weekend_bp.route("/export", methods=["POST"])
def export_weekend_report():
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    fmt = request.form.get("format", "csv")

    aggregator = DataAggregator()
    tasks = aggregator.get_weekend_tasks(start_date, end_date)

    generator = ReportGenerator()
    file_path = generator.generate_report(
        "weekend_report",
        f"Weekend Report ({start_date} to {end_date})",
        {"start_date": start_date, "end_date": end_date},
        fmt,
        session.get("user_id"),
        data={"tasks": tasks},
    )

    return send_file(file_path, as_attachment=True)
