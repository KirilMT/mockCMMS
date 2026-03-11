"""Database models for the Reports application."""

from datetime import datetime

from src.services.db_utils import db


class Report(db.Model):  # type: ignore
    __bind_key__ = "reports"
    __tablename__ = "reports"
    __table_args__ = {"extend_existing": True}  # Fix for duplicate metadata error

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)
    format = db.Column(db.String(20), nullable=False, default="html")  # Always html
    generated_on = db.Column(db.DateTime, default=datetime.utcnow)
    parameters = db.Column(db.JSON)  # Stores generation params
    data = db.Column(db.JSON)  # Stores the actual report content
    file_path = db.Column(db.String(500))
    generated_by = db.Column(db.Integer)  # User ID, loosely coupled

    def to_dict(self):
        # Extract shift from parameters (primary), then report data/title fallback
        shift = None
        if self.parameters:
            params = self.parameters if isinstance(self.parameters, dict) else {}
            shift = params.get("shift")

        data_payload = self.data if isinstance(self.data, dict) else {}
        report_info = data_payload.get("report_info") or {}
        if not shift:
            shift = report_info.get("shift") or data_payload.get("shift")

        if not shift and self.title:
            title_match = (
                "Night"
                if " - Night" in self.title
                else ("Early" if " - Early" in self.title else None)
            )
            shift = title_match

        data = {
            "id": self.id,
            "title": self.title,
            "report_type": self.report_type,
            "shift": shift,
            "generated_on": (
                self.generated_on.isoformat() if self.generated_on else None
            ),
            "parameters": self.parameters,
            "data": self.data,
            "file_path": self.file_path,
            "generated_by": self.generated_by,
        }

        # Include dynamically added attributes like generated_by_name
        if hasattr(self, "generated_by_name"):
            data["generated_by_name"] = self.generated_by_name

        return data
