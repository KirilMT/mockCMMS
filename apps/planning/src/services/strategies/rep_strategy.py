from .assignment_strategy import AssignmentStrategy


class REPAssignmentStrategy(AssignmentStrategy):
    """Strategy for assigning Repair (REP) tasks."""

    def assign_task(self, context: dict) -> dict:
        """Implements the REP assignment logic (simplified/direct assignment)."""
        task_to_assign = context["task_to_assign"]
        instance_num = context["instance_num"]
        quantity = context["quantity"]
        rep_assignments = context["rep_assignments"]

        task_id = task_to_assign["id"]
        task_name_excel = task_to_assign.get("name", "Unknown")
        base_duration = int(task_to_assign.get("planned_worktime_min", 0))

        instance_id_str = f"{task_id}_{instance_num}"
        instance_task_display_name = (
            f"{task_name_excel} (Instance {instance_num}/{quantity})"
        )

        self._log(
            "debug",
            f"    (Helper) Assigning REP instance: {instance_task_display_name}",
        )

        result = {
            "success": False,
            "failure_reason": "",
            "assignments": [],
            "incomplete_instance_id": None,
        }

        rep_assignments_map = (
            {item["task_id"]: item for item in rep_assignments}
            if rep_assignments
            else {}
        )
        assignment_info_rep = rep_assignments_map.get(task_id)

        if not assignment_info_rep:
            result["failure_reason"] = "Skipped (REP): Task data not received from UI."
            return result

        if assignment_info_rep.get("skipped"):
            result["failure_reason"] = assignment_info_rep.get(
                "skip_reason", "Skipped by user."
            )
            return result

        tech_name = assignment_info_rep.get("technician")
        assigned_start_time = assignment_info_rep.get("time_slot")

        # Validate Tech Exists (assuming validation happened elsewhere)
        # In legacy code, it just tries to assign.

        if tech_name and assigned_start_time is not None:
            assigned_start_time = int(assigned_start_time)
            duration = base_duration

            # Check overlap (Legacy code didn't robustly check overlap for REP)
            # Legacy logic: It appends to schedule.

            result["success"] = True
            result["assignments"] = [
                {
                    "technician": tech_name,
                    "start": assigned_start_time,
                    "duration": duration,
                    "task_name": instance_task_display_name,
                    "is_incomplete": False,
                    "original_duration": duration,
                    "instance_id": instance_id_str,
                }
            ]
            self._log(
                "info",
                f"    (Helper) Assigned REP {instance_task_display_name} "
                f"to {tech_name} at {assigned_start_time}",
            )
            return result

        result["failure_reason"] = "REP Assignment Incomplete (missing tech or time)."
        return result
