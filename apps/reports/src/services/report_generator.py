import csv
import os
from datetime import datetime, timedelta

from src.services.db_utils import MaintenanceOrder


class ReportGenerator:
    """Generates reports in various formats."""

    def __init__(self):
        """Initialize with reports directory path (lazy creation)."""
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
        if data is None:
            if report_type == "reactive_production":
                data = self._get_reactive_production_data(parameters)
            elif report_type == "completed_weekend":
                data = self._get_completed_weekend_data(parameters)
            else:
                raise ValueError(f"Data required for report type: {report_type}")
        else:
            if "generated_at" not in data:
                data["generated_at"] = datetime.now().isoformat()
            if "title" not in data:
                data["title"] = title
            if "report_type" not in data:
                data["report_type"] = report_type

        # Generate filename
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_shift = ""
        ri = (
            data.get("report_info")
            or data.get("shift_info")
            or data.get("weekend_info")
            or {}
        )
        if ri.get("date"):
            report_date = str(ri["date"]).replace("/", "-")
        if ri.get("shift"):
            report_shift = f"_{ri['shift']}"

        type_prefix = report_type.replace("_report", "").capitalize()
        ext = format_type.lower()
        if ext == "markdown":
            ext = "md"

        filename = f"{type_prefix}_Report_{report_date}{report_shift}.{ext}"
        os.makedirs(self.reports_dir, exist_ok=True)
        file_path = os.path.join(self.reports_dir, filename)

        if format_type.lower() in ["pdf", "txt"]:
            file_path = self._generate_text_report(data, title, file_path)
        elif format_type.lower() == "csv":
            self.generate_csv(data, file_path)
        elif format_type.lower() == "markdown":
            self._generate_markdown_report(data, title, file_path)
        elif format_type.lower() == "json":
            import json

            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(data, f, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        return file_path

    @staticmethod
    def _clean_field(val, prefix=None):
        """Clean potential internal labels from fields (e.g. 'Start Time')."""
        if not val or str(val).lower() == "n/a":
            return "N/A"
        res = str(val)
        # Case-insensitive removal of common labels
        for label in ["Start Time:", "Duration:", "Start Time", "Duration"]:
            if label.lower() in res.lower():
                import re

                res = re.sub(re.escape(label), "", res, flags=re.IGNORECASE)

        if prefix:
            import re

            res = re.sub(re.escape(f"{prefix}:"), "", res, flags=re.IGNORECASE)
            res = re.sub(re.escape(prefix), "", res, flags=re.IGNORECASE)

        res = res.strip()
        # Handle cases where multiple values might be present
        # (take only the last part if it looks like a single field)
        if " " in res and ":" not in res:
            res = res.split(" ")[-1]
        return res

    def _get_reactive_production_data(self, parameters):
        """Get reactive maintenance orders during production."""
        query = MaintenanceOrder.query.filter_by(order_type="Reactive")
        if parameters.get("start_date"):
            sd = datetime.strptime(parameters["start_date"], "%Y-%m-%d")
            query = query.filter(MaintenanceOrder.created_at >= sd)
        if parameters.get("end_date"):
            ed = datetime.strptime(parameters["end_date"], "%Y-%m-%d")
            query = query.filter(MaintenanceOrder.created_at <= ed)
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
        wd = datetime.strptime(parameters["weekend_date"], "%Y-%m-%d")
        days_ahead = 5 - wd.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        sat = wd + timedelta(days=days_ahead)
        sun = sat + timedelta(days=1)
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.status == "Completed",
            MaintenanceOrder.modified_on >= sat,
            MaintenanceOrder.modified_on <= sun + timedelta(days=1),
        ).all()
        return {
            "title": f"Completed MOs - Weekend of {sat.strftime('%Y-%m-%d')}",
            "parameters": parameters,
            "weekend_dates": {
                "saturday": sat.strftime("%Y-%m-%d"),
                "sunday": sun.strftime("%Y-%m-%d"),
            },
            "maintenance_orders": [mo.to_dict() for mo in mos],
            "total_count": len(mos),
            "generated_at": datetime.now().isoformat(),
        }

    def _generate_text_report(self, data, title, file_path):
        """Generate formatted text report."""
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            rtype = data.get("report_type") or ""
            if rtype == "shift_report" or data.get("shift_info"):
                self._generate_shift_report_text(f, data, title)
            elif rtype == "weekend_report" or data.get("weekend_info"):
                self._generate_weekend_report_text(f, data, title)
            else:
                self._generate_generic_text(f, data, title)
        return file_path

    def _generate_pdf_report(self, data, title, file_path):
        """Generate PDF report (redirects to text report)."""
        # PDF generation uses same text format
        txt_path = file_path.replace(".pdf", ".txt")
        return self._generate_text_report(data, title, txt_path)

    def _generate_shift_report_text(self, f, data, title):
        """Generate shift report as formatted text."""
        ri = data.get("report_info") or data.get("shift_info") or {}
        date = ri.get("date", data.get("date", "N/A"))
        shift = ri.get("shift", data.get("shift", "N/A"))
        team = ri.get("team_name", data.get("team_name", "N/A"))

        f.write(f"SHIFT REPORT - {date} - {shift} - {team}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Attendance: {data.get('attendance', 'N/A')}\n")
        f.write(f"EHS incidents: {data.get('ehs_incidents', 0)}\n")
        f.write(f"VIGEL: {data.get('vigel', '-/-')}\n")
        f.write(f"MDS: {data.get('mds', '-/-')}\n\n")

        f.write("HANDOVER FROM PREVIOUS SHIFT\n")
        f.write("-" * 40 + "\n")
        hf = ri.get("handover_from_previous", []) or data.get(
            "handover_from_previous", []
        )
        if hf:
            for item in hf:
                if isinstance(item, dict):
                    f.write(
                        f"  * {item.get('asset', 'ASSET')} - "
                        f"{item.get('title', 'Title')}: "
                        f"{item.get('description', '')}\n"
                    )
                else:
                    f.write(f"  * {item}\n")
        else:
            f.write("  No notes\n")
        f.write("\n")

        f.write("BREAKDOWNS\n")
        f.write("-" * 40 + "\n")
        breakdowns = data.get("breakdowns", [])
        if breakdowns:
            for bd in breakdowns:
                asset = bd.get("equipment_line") or bd.get("asset", "ASSET")
                ts_str = self._clean_field(bd.get("timestamp"), "Start Time")
                dur_raw = self._clean_field(bd.get("duration"), "Duration")
                d_unit = (
                    f"{dur_raw} min"
                    if (dur_raw != "N/A" and "min" not in dur_raw.lower())
                    else dur_raw
                )
                f.write(f"\n  {asset} - {ts_str} - {d_unit}:\n")
                f.write(f"    Fault: {bd.get('description', 'N/A')}\n")
                f.write(f"    Root cause: {bd.get('root_cause', 'N/A')}\n")
                f.write(f"    Recovery: {bd.get('resolution_notes', 'N/A')}\n")
        else:
            f.write("  No breakdowns\n")
        f.write("\n")

        f.write("ENGINEERING SUPPORT / BREAK ACTIVITIES\n")
        f.write("-" * 40 + "\n")
        activities = data.get("break_activities", [])
        eng_support = data.get("engineering_support", [])

        f.write("  FLUX Tickets/MOs:\n")
        flux = [
            a for a in activities if a.get("type") == "flux_ticket" or a.get("mo_id")
        ]
        if flux:
            for a in flux:
                asset = a.get("asset", "ASSET")
                title_text = a.get("title") or a.get("description", "Title")
                mo_id = a.get("mo_id", "Num.")
                f.write(
                    f"    * {asset} - {title_text} (ID: {mo_id}): "
                    f"{a.get('description', '')}\n"
                )
        else:
            f.write("    None\n")

        f.write("\n  Engineering Support:\n")
        if eng_support:
            for e in eng_support:
                f.write(
                    f"    * {e.get('asset', 'ASSET')} - "
                    f"{e.get('title', 'Title')}: "
                    f"{e.get('description', '')}\n"
                )
        else:
            f.write("    None\n")
        f.write("\n")

        f.write("HANDOVER TO NEXT SHIFT\n")
        f.write("-" * 40 + "\n")
        ht = ri.get("handover_to_next", []) or data.get("handover_to_next", [])
        if ht:
            for item in ht:
                if isinstance(item, dict):
                    f.write(
                        f"  * {item.get('asset', 'ASSET')} - "
                        f"{item.get('title', 'Title')}: "
                        f"{item.get('description', '')}\n"
                    )
                else:
                    f.write(f"  * {item}\n")
        else:
            f.write("  No notes\n")
        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write(f"Have a good shift,\n{data.get('generated_by_name', 'Technician')}\n")

    def _generate_shift_report_markdown(self, f, data, title):
        """Generate shift report in Markdown format."""
        ri = data.get("report_info") or data.get("shift_info") or {}
        date = ri.get("date", data.get("date", "N/A"))
        shift = ri.get("shift", data.get("shift", "N/A"))
        team = ri.get("team_name", data.get("team_name", "N/A"))

        f.write(f"# Shift Report - {date} - {shift} - {team}\n\n")
        f.write(f"**Attendance:** {data.get('attendance', 'N/A')}\n")
        f.write(f"**EHS incidents:** {data.get('ehs_incidents', 0)}\n")
        f.write(f"**VIGEL:** {data.get('vigel', '-/-')}\n")
        f.write(f"**MDS:** {data.get('mds', '-/-')}\n\n")

        f.write("## Handover from previous Shift\n\n")
        hf = ri.get("handover_from_previous", []) or data.get(
            "handover_from_previous", []
        )
        if hf:
            for item in hf:
                if isinstance(item, dict):
                    f.write(
                        f"- **{item.get('asset', 'ASSET')}** - "
                        f"*{item.get('title', 'Title')}*: "
                        f"{item.get('description', '')}\n"
                    )
                else:
                    f.write(f"- {item}\n")
        else:
            f.write("- No notes\n")
        f.write("\n")

        f.write("## Breakdowns\n\n")
        breakdowns = data.get("breakdowns", [])
        if breakdowns:
            for bd in breakdowns:
                asset_code = (
                    bd.get("equipment_line")
                    or bd.get("asset_code")
                    or bd.get("asset", "ASSET")
                )
                start_time = self._clean_field(
                    bd.get("timestamp") or bd.get("start_time"), "Start Time"
                )
                dur_raw = self._clean_field(bd.get("duration"), "Duration")
                duration = (
                    f"{dur_raw} min"
                    if (dur_raw != "N/A" and "min" not in dur_raw.lower())
                    else dur_raw
                )
                f.write(f"**{asset_code}** - {start_time} - {duration}:\n")
                f.write(f"- Fault: {bd.get('description') or bd.get('fault', 'N/A')}\n")
                f.write(f"- Root cause: {bd.get('root_cause', 'N/A')}\n")
                recovery = bd.get("resolution_notes") or bd.get("recovery", "N/A")
                f.write(f"- Recovery: {recovery}\n\n")
        else:
            f.write("- No breakdowns\n\n")

        f.write("## Engineering Support / FLUX Tickets\n\n")
        f.write("### FLUX Tickets/MOs\n\n")
        activities = data.get("break_activities", [])
        flux = [
            a for a in activities if a.get("type") == "flux_ticket" or a.get("mo_id")
        ]
        if flux:
            for a in flux:
                asset = a.get("asset", "ASSET")
                title_text = a.get("title") or a.get("description", "Title")
                mo_id = a.get("mo_id", "N/A")
                f.write(
                    f"- **{asset}** - *{title_text}* (ID: {mo_id}): "
                    f"{a.get('description', '')} {a.get('status', '')}\n"
                )
        else:
            f.write("- None\n")
        f.write("\n")

        f.write("### Engineering Support\n\n")
        eng = data.get("engineering_support", [])
        if eng:
            for e in eng:
                f.write(
                    f"- **{e.get('asset', 'ASSET')}** - "
                    f"*{e.get('title', 'Title')}*: "
                    f"{e.get('description', '')}\n"
                )
        else:
            f.write("- None\n")
        f.write("\n")

        f.write("## Handover to next Shift\n\n")
        ht = ri.get("handover_to_next", []) or data.get("handover_to_next", [])
        if ht:
            for item in ht:
                if isinstance(item, dict):
                    f.write(
                        f"- **{item.get('asset', 'ASSET')}** - "
                        f"*{item.get('title', 'Title')}*: "
                        f"{item.get('description', '')}\n"
                    )
                else:
                    f.write(f"- {item}\n")
        else:
            f.write("- No notes\n")
        f.write("\n")
        f.write(
            f"---\n\nHave a good shift,\n\n"
            f"**{data.get('generated_by_name', 'Technician')}**\n"
        )

    def _generate_weekend_report_text(self, f, data, title):
        """Generate weekend report as formatted text."""
        ri = data.get("report_info") or data.get("weekend_info") or {}
        date = ri.get("date", data.get("date", "N/A"))
        shift = ri.get("shift", data.get("shift", "Early"))
        team = ri.get("team_name", data.get("team_name", "Weekend Team"))

        f.write(f"WEEKEND SHIFT REPORT - {date} - {shift} - {team}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Attendance: {data.get('attendance', 'N/A')}\n")
        f.write(f"EHS incidents: {data.get('ehs_incidents', 0)}\n\n")

        # Handover From
        f.write("HANDOVER FROM PREVIOUS SHIFT\n")
        f.write("-" * 40 + "\n")
        hf = data.get("handover_from_previous", [])
        if hf:
            for item in hf:
                if isinstance(item, dict):
                    asset = item.get("asset", "ASSET")
                    title = item.get("title", "Title")
                    desc = item.get("description", "")
                    f.write(f"  * {asset} - {title}: {desc}\n")
                else:
                    f.write(f"  * {item}\n")
        else:
            f.write("  No notes\n")
        f.write("\n")

        f.write("HANDOVER INSTRUCTIONS / TO NEXT SHIFT\n")
        f.write("-" * 40 + "\n")
        instr = data.get("handover_instructions", []) or data.get(
            "handover_to_next", []
        )
        if instr:
            for h in instr:
                if isinstance(h, dict):
                    asset = h.get("asset", "ASSET")
                    title = h.get("title", "Title")
                    desc = h.get("description", "")
                    f.write(f"  * {asset} - {title}: {desc}\n")
                else:
                    f.write(f"  * {h}\n")
        else:
            f.write("  No instructions\n")
        f.write("\n")

        f.write("PMs\n")
        f.write("-" * 40 + "\n")
        pms = data.get("pms", [])
        if pms:
            for pm in pms:
                f.write(
                    f"  * {pm.get('asset', 'ASSET')} - "
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
                    f"  * {mo.get('asset', 'ASSET')} - {mo.get('description', 'N/A')}\n"
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
                    f"  * {t.get('asset', 'ASSET')} - {t.get('description', 'N/A')}\n"
                )
        else:
            f.write("  None\n")
        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write("Have a good shift,\nTechnician\n")

    def _generate_markdown_report(self, data, title, file_path):
        """Generate Markdown report."""
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            rtype = data.get("report_type") or ""
            if rtype == "shift_report" or data.get("shift_info"):
                self._generate_shift_report_markdown(f, data, title)
            elif rtype == "weekend_report" or data.get("weekend_info"):
                self._generate_weekend_report_markdown(f, data, title)
            else:
                self._generate_generic_markdown(f, data, title)
        return file_path

    def _generate_generic_text(self, f, data, title):
        """Fallback for generic data."""
        f.write(f"Report: {title}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {data.get('generated_at', 'N/A')}\n")
        items = (
            data.get("maintenance_orders")
            or data.get("incidents")
            or data.get("tasks")
            or []
        )
        f.write(f"Total Records: {len(items)}\n\n")
        for item in items:
            f.write(str(item) + "\n")

    def _generate_generic_markdown(self, f, data, title):
        """Generate generic Markdown report for legacy types."""
        f.write(f"# {title}\n\n")
        f.write(f"**Generated:** {data.get('generated_at', 'N/A')}\n")
        items = (
            data.get("maintenance_orders")
            or data.get("incidents")
            or data.get("tasks")
            or []
        )
        f.write(f"**Total Records:** {len(items)}\n\n")
        if data.get("weekend_dates"):
            f.write(
                f"**Weekend Period:** {data['weekend_dates']['saturday']} "
                f"to {data['weekend_dates']['sunday']}\n\n"
            )
        f.write("## Data\n\n")
        if items:
            headers = list(items[0].keys())
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for item in items:
                v = [str(item.get(h, "")) for h in headers]
                f.write("| " + " | ".join(v) + " |\n")
        else:
            f.write("No data found for the specified criteria.\n")

    def generate_csv(self, data, file_path):
        """Generate CSV export from data."""
        items = (
            data.get("maintenance_orders")
            or data.get("incidents")
            or data.get("tasks")
            or []
        )
        if not items:
            with open(file_path, "w", newline="") as f:
                f.write("No data found")
            return file_path
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=items[0].keys())
            writer.writeheader()
            writer.writerows(items)
        return file_path

    def _generate_weekend_report_markdown(self, f, data, title):
        """Generate weekend report in Markdown format."""
        ri = data.get("report_info") or data.get("weekend_info") or {}
        date = ri.get("date", data.get("date", "N/A"))
        shift = ri.get("shift", data.get("shift", "Early"))
        team = ri.get("team_name", data.get("team_name", "Weekend Team"))

        f.write(f"# Weekend Shift Report - {date} - {shift} - {team}\n\n")
        f.write(f"**Attendance:** {data.get('attendance', 'N/A')}\n")
        f.write(f"**EHS incidents:** {data.get('ehs_incidents', 0)}\n\n")

        f.write("## Handover from previous Shift\n\n")
        hf = data.get("handover_from_previous", [])
        if hf:
            for item in hf:
                if isinstance(item, dict):
                    asset = item.get("asset", "ASSET")
                    title = item.get("title", "Title")
                    desc = item.get("description", "")
                    f.write(f"- **{asset}** - {title}: {desc}\n")
                else:
                    f.write(f"- {item}\n")
        else:
            f.write("- No notes\n")
        f.write("\n")

        f.write("## Handover Instructions / To Next\n\n")
        instr = data.get("handover_instructions", []) or data.get(
            "handover_to_next", []
        )
        if instr:
            for h in instr:
                if isinstance(h, dict):
                    asset = h.get("asset", "ASSET")
                    title = h.get("title", "Title")
                    desc = h.get("description", "")
                    f.write(f"- **{asset}** - {title}: {desc}\n")
                else:
                    f.write(f"- {h}\n")
        else:
            f.write("- No instructions\n")
        f.write("\n")

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

        f.write("## Additional Tickets\n\n")
        additional = data.get("additional_tickets", [])
        if additional:
            for t in additional:
                f.write(
                    f"- **{t.get('asset', 'ASSET')}** - {t.get('description', 'N/A')}\n"
                )
        else:
            f.write("- None\n")
        f.write("\n")
        f.write(
            f"---\n\nHave a good shift,\n\n"
            f"**{data.get('generated_by_name', 'Technician')}**\n"
        )

    def generate_summary_stats(self, data):
        """Calculate high-level totals/completion metrics for report views."""
        payload = data if isinstance(data, dict) else {}

        items = []
        for key in ("maintenance_orders", "incidents", "tasks"):
            value = payload.get(key)
            if isinstance(value, list):
                items = value
                break

        total_count = len(items)
        stats = {"total_count": total_count}
        if total_count == 0:
            return stats

        completed_count = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "")).strip().lower()
            if status == "completed":
                completed_count += 1

        stats["completed_count"] = completed_count
        stats["open_count"] = max(total_count - completed_count, 0)
        stats["completion_rate"] = f"{(completed_count / total_count) * 100:.1f}%"
        return stats
