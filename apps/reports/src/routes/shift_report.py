from datetime import datetime

from flask import Blueprint, render_template, request, send_file, session

from apps.reports.src.services.data_aggregator import DataAggregator
from apps.reports.src.services.report_generator import ReportGenerator

shift_bp = Blueprint(
    "shift", __name__, url_prefix="/shift", template_folder="../templates"
)


@shift_bp.route("/", methods=["GET"])
def shift_report():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    shift = request.args.get("shift", "Morning")

    aggregator = DataAggregator()
    tasks = aggregator.get_shift_data(date_str, shift)

    generator = ReportGenerator()
    stats = generator.generate_summary_stats({"tasks": tasks})

    return render_template(
        "shift_report.html", tasks=tasks, stats=stats, date=date_str, shift=shift
    )


@shift_bp.route("/export", methods=["POST"])
def export_shift_report():
    date_str = request.form.get("date")
    shift = request.form.get("shift")
    fmt = request.form.get("format", "csv")

    aggregator = DataAggregator()
    tasks = aggregator.get_shift_data(date_str, shift)

    generator = ReportGenerator()
    file_path = generator.generate_report(
        "shift_report",
        f"Shift Report - {shift} ({date_str})",
        {"date": date_str, "shift": shift},
        fmt,
        session.get("user_id"),
        data={"tasks": tasks},
    )

    return send_file(file_path, as_attachment=True)
