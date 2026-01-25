from apps.reports.src.models import Incident
from src.services.db_utils import db


def test_incident_model(app):
    with app.app_context():
        incident = Incident(
            incident_type="Breakdown",
            equipment_line="Line 1",
            description="Test breakdown",
            severity="High",
            technician_name="Tech 1",
        )
        db.session.add(incident)
        db.session.commit()

        saved_incident = Incident.query.first()
        assert saved_incident.incident_type == "Breakdown"
        assert saved_incident.equipment_line == "Line 1"
