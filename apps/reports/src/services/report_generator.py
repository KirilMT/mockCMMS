import csv
import os
from datetime import datetime, timedelta

from src.services.db_utils import MaintenanceOrder


class ReportGenerator:
    """Generates reports in various formats."""

    def __init__(self):
        """Initialize with reports directory path (lazy creation)."""
        # Calculate app root (2 levels up from apps/reports/src/services/)
        app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self._reports_dir = os.path.join(app_root, "instance", "reports")

    @property
    def reports_dir(self):
        """Get reports directory path."""
        return self._reports_dir

    def generate_report(
        self, report_type, title, parameters, format_type, user_id, data=None
    ):
        """Generate a report based on type and parameters."""

        # If data is not provided, fetch it based on legacy logic
        # (optional backward compatibility)
        if data is None:
            if report_type == "reactive_production":
                data = self._get_reactive_production_data(parameters)
            elif report_type == "completed_weekend":
                data = self._get_completed_weekend_data(parameters)
            else:
                # For new reports, data should be passed in
                raise ValueError(f"Data required for report type: {report_type}")
        else:
            # Ensure data has standard fields if not present
            if "generated_at" not in data:
                data["generated_at"] = datetime.now().isoformat()
            if "title" not in data:
                data["title"] = title

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.{format_type.lower()}"

        # Ensure directory exists before writing
        os.makedirs(self.reports_dir, exist_ok=True)
        file_path = os.path.join(self.reports_dir, filename)

        # Generate report based on format
        if format_type.lower() == "pdf":
            file_path = self._generate_pdf_report(data, title, file_path)
        elif format_type.lower() == "csv":
            self.generate_csv(data, file_path)
        elif format_type.lower() == "markdown":
            self._generate_markdown_report(data, title, file_path)
        elif format_type.lower() == "json":
            import json

            with open(file_path, "w") as f:
                json.dump(data, f, default=str)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        return file_path

    def _get_reactive_production_data(self, parameters):
        """Get reactive maintenance orders during production."""
        query = MaintenanceOrder.query.filter_by(order_type="Reactive")

        if parameters.get("start_date"):
            start_date = datetime.strptime(parameters["start_date"], "%Y-%m-%d")
            query = query.filter(MaintenanceOrder.created_at >= start_date)

        if parameters.get("end_date"):
            end_date = datetime.strptime(parameters["end_date"], "%Y-%m-%d")
            query = query.filter(MaintenanceOrder.created_at <= end_date)

        if parameters.get("priority") and parameters["priority"] != "All":
            query = query.filter(MaintenanceOrder.priority == parameters["priority"])

        mos = query.all()

        return {
            "title": "Reactive Maintenance Orders During Production",
            "parameters": parameters,
            "maintenance_orders": [mo.to_dict() for mo in mos],
            "total_count": len(mos),
            "generated_at": datetime.now().isoformat(),
        }

    def _get_completed_weekend_data(self, parameters):
        """Get completed maintenance orders for weekend."""
        weekend_date = datetime.strptime(parameters["weekend_date"], "%Y-%m-%d")

        # Get Saturday and Sunday of that week
        days_ahead = 5 - weekend_date.weekday()  # Saturday is 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = weekend_date + timedelta(days=days_ahead)
        sunday = saturday + timedelta(days=1)

        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.modified_on >= saturday,
            MaintenanceOrder.modified_on <= sunday + timedelta(days=1),
        ).all()

        return {
            "title": (
                "Completed Maintenance Orders - Weekend of "
                f"{saturday.strftime('%Y-%m-%d')}"
            ),
            "parameters": parameters,
            "weekend_dates": {
                "saturday": saturday.strftime("%Y-%m-%d"),
                "sunday": sunday.strftime("%Y-%m-%d"),
            },
            "maintenance_orders": [mo.to_dict() for mo in mos],
            "total_count": len(mos),
            "generated_at": datetime.now().isoformat(),
        }

    def _generate_pdf_report(self, data, title, file_path):
        """Generate PDF report (text format - requires reportlab for true PDF)."""
        # For now, create a formatted text file as placeholder
        txt_path = file_path.replace(".pdf", ".txt")
        with open(txt_path, "w") as f:
            # Handle shift_report type
            if data.get("shift_info"):
                self._generate_shift_report_text(f, data, title)
            # Handle weekend_report type
            elif data.get("weekend_info"):
                self._generate_weekend_report_text(f, data, title)
            # Handle legacy/generic reports
            else:
                f.write(f"Report: {title}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {data.get('generated_at', 'N/A')}\n")

                items = []
                if "maintenance_orders" in data:
                    items = data["maintenance_orders"]
                elif "incidents" in data:
                    items = data["incidents"]
                elif "tasks" in data:
                    items = data["tasks"]

                f.write(f"Total Records: {len(items)}\n\n")

                for item in items:
                    f.write(str(item) + "\n")

        return txt_path

    def _generate_shift_report_text(self, f, data, title):
        """Generate shift report as formatted text."""
        shift_info = data.get("shift_info", {})
        date = shift_info.get("date", "N/A")
        shift = shift_info.get("shift", "N/A")
        team = data.get("team_name", "Red Shift")

        f.write(f"SHIFT REPORT – {date} – {shift} – {team}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Attendance: {data.get('attendance', 'N/A')}\n")
        f.write(f"EHS incidents: {data.get('ehs_incidents', 0)}\n")
        f.write(f"VIGEL: {data.get('vigel', '-/-')}\n")
        f.write(f"MDS: {data.get('mds', '-/-')}\n\n")

        f.write("HANDOVER FROM PREVIOUS SHIFT\n")
        f.write("-" * 40 + "\n")
        hf = shift_info.get("handover_from_previous", [])
        if hf:
            for item in hf:
                f.write(f"  • {item}\n")
        else:
            f.write("  No notes\n")
        f.write("\n")

        f.write("BREAKDOWNS\n")
        f.write("-" * 40 + "\n")
        breakdowns = data.get("breakdowns", [])
        if breakdowns:
            for bd in breakdowns:
                f.write(
                    f"\n  {bd.get('equipment_line', 'ASSET')} - "
                    f"{bd.get('timestamp', 'N/A')}\n"
                )
                f.write(f"    Fault: {bd.get('description', 'N/A')}\n")
                f.write(f"    Root cause: {bd.get('root_cause', 'N/A')}\n")
                f.write(f"    Recovery: {bd.get('resolution_notes', 'N/A')}\n")
        else:
            f.write("  No breakdowns\n")
        f.write("\n")

        f.write("ENGINEERING SUPPORT / BREAK ACTIVITIES\n")
        f.write("-" * 40 + "\n")
        activities = data.get("break_activities", [])
        if activities:
            for a in activities:
                f.write(
                    f"  • {a.get('asset', 'ASSET')} - "
                    f"{a.get('description', 'N/A')}\n"
                )
        else:
            f.write("  None\n")
        f.write("\n")

        f.write("HANDOVER TO NEXT SHIFT\n")
        f.write("-" * 40 + "\n")
        ht = shift_info.get("handover_to_next", [])
        if ht:
            for item in ht:
                f.write(f"  • {item}\n")
        else:
            f.write("  No notes\n")
        f.write("\n")

        f.write("=" * 60 + "\n")
        f.write("Have a good shift,\nTechnician\n")

    def _generate_weekend_report_text(self, f, data, title):
        """Generate weekend report as formatted text."""
        weekend_info = data.get("weekend_info", {})
        date = weekend_info.get("date", "N/A")
        shift = data.get("shift", "Early")

        f.write(f"WEEKEND SHIFT REPORT – {date} – {shift}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Attendance: {data.get('attendance', 'N/A')}\n")
        f.write(f"EHS incidents: {data.get('ehs_incidents', 0)}\n\n")

        f.write("PMs\n")
        f.write("-" * 40 + "\n")
        pms = data.get("pms", [])
        if pms:
            for pm in pms:
                f.write(
                    f"  • {pm.get('asset', 'ASSET')} - "
                    f"{pm.get('description', 'N/A')} "
                    f"({pm.get('status', 'Completed')})\n"
                )
        else:
            f.write("  No PMs\n")
        f.write("\n")

        f.write("MOs/TICKETS\n")
        f.write("-" * 40 + "\n")
        mos = data.get("mos", []) or data.get("mos_tickets", [])
        if mos:
            for mo in mos:
                f.write(
                    f"  • {mo.get('asset', 'ASSET')} - "
                    f"{mo.get('description', 'N/A')}\n"
                )
        else:
            f.write("  No MOs/Tickets\n")
        f.write("\n")

        f.write("ADDITIONAL TICKETS NOT ON WEEKEND LIST\n")
        f.write("-" * 40 + "\n")
        additional = data.get("additional_tickets", [])
        if additional:
            for t in additional:
                f.write(
                    f"  • {t.get('asset', 'ASSET')} - "
                    f"{t.get('description', 'N/A')}\n"
                )
        else:
            f.write("  None\n")
        f.write("\n")

        f.write("HANDOVER INSTRUCTIONS\n")
        f.write("-" * 40 + "\n")
        instructions = data.get("handover_instructions", [])
        if instructions:
            for h in instructions:
                f.write(f"  • {h}\n")
        else:
            f.write("  No instructions\n")
        f.write("\n")

        f.write("=" * 60 + "\n")
        f.write("Have a good shift,\nTechnician\n")

    def _generate_markdown_report(self, data, title, file_path):
        """Generate Markdown report."""
        with open(file_path, "w") as f:
            # Handle shift_report type
            if data.get("shift_info"):
                self._generate_shift_report_markdown(f, data, title)
            # Handle weekend_report type
            elif data.get("weekend_info"):
                self._generate_weekend_report_markdown(f, data, title)
            # Handle legacy/generic reports
            else:
                self._generate_generic_markdown(f, data, title)

        return file_path

    def _generate_shift_report_markdown(self, f, data, title):
        """Generate shift report in Markdown format."""
        shift_info = data.get("shift_info", {})
        date = shift_info.get("date", "N/A")
        shift = shift_info.get("shift", "N/A")
        team = data.get("team_name", "Red Shift")

        f.write(f"# Shift Report – {date} – {shift} – {team}\n\n")
        f.write(f"**Attendance:** {data.get('attendance', 'N/A')}\n")
        f.write(f"**EHS incidents:** {data.get('ehs_incidents', 0)}\n")
        f.write(f"**VIGEL:** {data.get('vigel', '-/-')}\n")
        f.write(f"**MDS:** {data.get('mds', '-/-')}\n\n")

        # Handover from previous shift
        f.write("## Handover from previous Shift\n\n")
        hf = shift_info.get("handover_from_previous", [])
        if hf:
            for item in hf:
                f.write(f"- {item}\n")
        else:
            f.write("- No notes\n")
        f.write("\n")

        # Breakdowns
        f.write("## Breakdowns\n\n")
        breakdowns = data.get("breakdowns", [])
        if breakdowns:
            for bd in breakdowns:
                f.write(
                    f"### {bd.get('equipment_line', 'ASSET')} - "
                    f"{bd.get('timestamp', 'N/A')}\n"
                )
                f.write(f"- **Fault:** {bd.get('description', 'N/A')}\n")
                f.write(f"- **Root cause:** {bd.get('root_cause', 'N/A')}\n")
                f.write(f"- **Recovery:** {bd.get('resolution_notes', 'N/A')}\n\n")
        else:
            f.write("- No breakdowns\n\n")

        # Break Activities
        f.write("## Engineering Support / Break Activities\n\n")
        activities = data.get("break_activities", [])
        if activities:
            for a in activities:
                f.write(
                    f"- **{a.get('asset', 'ASSET')}** - "
                    f"{a.get('description', 'N/A')}\n"
                )
        else:
            f.write("- None\n")
        f.write("\n")

        # Handover to next shift
        f.write("## Handover to next Shift\n\n")
        ht = shift_info.get("handover_to_next", [])
        if ht:
            for item in ht:
                f.write(f"- {item}\n")
        else:
            f.write("- No notes\n")
        f.write("\n")

        f.write("---\n\nHave a good shift,\n\n**Technician**\n")

    def _generate_weekend_report_markdown(self, f, data, title):
        """Generate weekend report in Markdown format."""
        weekend_info = data.get("weekend_info", {})
        date = weekend_info.get("date", "N/A")
        shift = data.get("shift", "Early")

        f.write(f"# Weekend Shift Report – {date} – {shift}\n\n")
        f.write(f"**Attendance:** {data.get('attendance', 'N/A')}\n")
        f.write(f"**EHS incidents:** {data.get('ehs_incidents', 0)}\n\n")

        # PMs
        f.write("## PMs\n\n")
        pms = data.get("pms", [])
        if pms:
            for pm in pms:
                f.write(
                    f"- **{pm.get('asset', 'ASSET')}** - "
                    f"{pm.get('description', 'N/A')} "
                    f"({pm.get('status', 'Completed')})\n"
                )
        else:
            f.write("- No PMs\n")
        f.write("\n")

        # MOs/Tickets
        f.write("## MOs/Tickets\n\n")
        mos = data.get("mos", []) or data.get("mos_tickets", [])
        if mos:
            for mo in mos:
                f.write(
                    f"- **{mo.get('asset', 'ASSET')}** - "
                    f"{mo.get('description', 'N/A')}\n"
                )
        else:
            f.write("- No MOs/Tickets\n")
        f.write("\n")

        # Additional tickets
        f.write("## Additional tickets not on weekend list\n\n")
        additional = data.get("additional_tickets", [])
        if additional:
            for t in additional:
                f.write(
                    f"- **{t.get('asset', 'ASSET')}** - "
                    f"{t.get('description', 'N/A')}\n"
                )
        else:
            f.write("- None\n")
        f.write("\n")

        # Handover instructions
        f.write("## Handover Instructions\n\n")
        instructions = data.get("handover_instructions", [])
        if instructions:
            for h in instructions:
                f.write(f"- {h}\n")
        else:
            f.write("- No instructions\n")
        f.write("\n")

        f.write("---\n\nHave a good shift,\n\n**Technician**\n")

    def _generate_generic_markdown(self, f, data, title):
        """Generate generic Markdown report for legacy types."""
        f.write(f"# {title}\n\n")
        f.write(f"**Generated:** {data.get('generated_at', 'N/A')}\n")

        items = []
        if "maintenance_orders" in data:
            items = data["maintenance_orders"]
        elif "incidents" in data:
            items = data["incidents"]
        elif "tasks" in data:
            items = data["tasks"]

        f.write(f"**Total Records:** {len(items)}\n\n")

        if data.get("weekend_dates"):
            f.write(
                f"**Weekend Period:** {data['weekend_dates']['saturday']} "
                f"to {data['weekend_dates']['sunday']}\n\n"
            )

        f.write("## Data\n\n")

        if items:
            # Get headers from first item
            headers = list(items[0].keys())
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")

            for item in items:
                values = [str(item.get(h, "")) for h in headers]
                f.write("| " + " | ".join(values) + " |\n")
        else:
            f.write("No data found for the specified criteria.\n")

        f.write(
            f"\n---\n*Report generated by mockCMMS on "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        )

    def generate_csv(self, data, file_path):
        """Generate CSV export from data."""
        items = []
        if "maintenance_orders" in data:
            items = data["maintenance_orders"]
        elif "incidents" in data:
            items = data["incidents"]
        elif "tasks" in data:
            items = data["tasks"]

        if not items:
            with open(file_path, "w", newline="") as f:
                f.write("No data found")
            return file_path

        keys = items[0].keys()

        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(items)

        return file_path

    def generate_summary_stats(self, data):
        """Calculate summary statistics."""
        items = []
        if "maintenance_orders" in data:
            items = data["maintenance_orders"]
        elif "incidents" in data:
            items = data["incidents"]
        elif "tasks" in data:
            items = data["tasks"]

        stats = {
            "total_count": len(items),
        }

        # Add specific stats if available
        # Example: Completion rate for tasks
        completed = sum(1 for item in items if item.get("status") == "Completed")
        if items:
            stats["completion_rate"] = f"{(completed / len(items)) * 100:.1f}%"

        return stats
