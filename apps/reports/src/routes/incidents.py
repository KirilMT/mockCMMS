from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, session, current_app
from datetime import datetime
from apps.reports.src.services.data_aggregator import DataAggregator
from apps.reports.src.services.report_generator import ReportGenerator
from apps.reports.src.models import Incident

incidents_bp = Blueprint('incidents', __name__, url_prefix='/incidents', template_folder='../templates')

@incidents_bp.route('/', methods=['GET'])
def incident_list():
    filters = {
        'incident_type': request.args.get('type'),
        'severity': request.args.get('severity')
    }
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}

    aggregator = DataAggregator()
    incidents = aggregator.get_incidents(filters)

    return render_template('incident_list.html', incidents=incidents)

@incidents_bp.route('/new', methods=['GET'])
def new_incident():
    return render_template('incident_form.html')

@incidents_bp.route('/', methods=['POST'])
def create_incident():
    from src.services.db_utils import db

    try:
        new_incident = Incident(
            incident_type=request.form['incident_type'],
            equipment_line=request.form['equipment_line'],
            description=request.form['description'],
            severity=request.form['severity'],
            technician_name=session.get('username', 'Unknown'),
            timestamp=datetime.utcnow()
        )
        db.session.add(new_incident)
        db.session.commit()
        flash('Incident logged successfully', 'success')
        return redirect(url_for('reports.incidents.incident_list'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating incident: {e}")
        flash('Error creating incident', 'danger')
        return redirect(url_for('reports.incidents.new_incident'))

@incidents_bp.route('/aggregate', methods=['GET'])
def aggregate_report():
    start_date = request.args.get('start_date', datetime.now().strftime("%Y-%m-%d"))
    end_date = request.args.get('end_date', datetime.now().strftime("%Y-%m-%d"))

    aggregator = DataAggregator()
    incidents = aggregator.get_incidents({'start_date': start_date, 'end_date': end_date})

    generator = ReportGenerator()
    stats = generator.generate_summary_stats({'incidents': incidents})

    return render_template('incident_report.html',
                           incidents=incidents,
                           stats=stats,
                           start_date=start_date,
                           end_date=end_date)

@incidents_bp.route('/aggregate/export', methods=['POST'])
def export_aggregate_report():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    fmt = request.form.get('format', 'csv')

    aggregator = DataAggregator()
    incidents = aggregator.get_incidents({'start_date': start_date, 'end_date': end_date})

    generator = ReportGenerator()
    file_path = generator.generate_report(
        "incident_report",
        f"Incident Report ({start_date} to {end_date})",
        {"start_date": start_date, "end_date": end_date},
        fmt,
        session.get('user_id'),
        data={'incidents': incidents}
    )

    return send_file(file_path, as_attachment=True)
