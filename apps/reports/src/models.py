from datetime import datetime
from src.services.db_utils import db

class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    incident_type = db.Column(db.String(50), nullable=False)
    equipment_line = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    technician_name = db.Column(db.String(100), nullable=False)
    resolved = db.Column(db.Boolean, default=False)
    resolution_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_type": self.incident_type,
            "equipment_line": self.equipment_line,
            "description": self.description,
            "severity": self.severity,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M") if self.timestamp else None,
            "technician_name": self.technician_name,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None
        }
