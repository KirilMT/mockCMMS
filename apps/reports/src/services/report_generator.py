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
        """Generate PDF report (placeholder - requires reportlab)"""
        # For now, create a simple text file as placeholder
        # In a real scenario, we would use reportlab or similar
        txt_path = file_path.replace(".pdf", ".txt")
        with open(txt_path, "w") as f:
            f.write(f"PDF Report Placeholder: {title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {data.get('generated_at', 'N/A')}\n")

            # Try to find list data
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

        # Return the text file path for now
        return txt_path

    def _generate_markdown_report(self, data, title, file_path):
        """Generate Markdown report."""
        with open(file_path, "w") as f:
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

        return file_path

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
