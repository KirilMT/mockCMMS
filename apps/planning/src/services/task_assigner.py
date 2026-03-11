# src/task_assigner.py


from .config_manager import TECHNICIAN_LINES

# Maximum number of high-priority tasks to consider for permutation-based optimization.
# 7! = 5040, 8! = 40320. Keep this value mindful of performance.
MAX_PERMUTATION_TASKS = 3

# Performance tuning: Maximum number of top-skilled technicians to consider
# for PM task combinations.
# This helps prevent combinatorial explosion with large numbers
# of eligible technicians.
MAX_TECHS_FOR_COMBINATIONS = 12
# Performance tuning: Range of group sizes to check around
# the required number of technicians.
# e.g., a range of 1 means for a 3-tech task, we check groups of size 2, 3, and 4.
# A smaller range reduces the number of combinations to check.
GROUP_SIZE_SEARCH_RANGE = 1


def _log(logger, level, message, *args):
    """Helper function to log or print."""
    if logger:
        if level == "info":
            logger.info(message, *args)
        elif level == "debug":
            logger.debug(message, *args)
        elif level == "warning":
            logger.warning(message, *args)
        elif level == "error":
            logger.error(message, *args)
    else:
        print(f"[{level.upper()}] {message % args if args else message}")


def _calculate_hp_assignment_score(
    hp_assignments_details,
    hp_tasks_in_permutation,
    hp_unassigned_reasons_for_permutation,
    logger,
):
    """Calculates a score for a given assignment of high-priority tasks.

    Primary goal: Maximize the number of fully assigned high-priority task definitions.
    Secondary goal: Minimize the sum of priority values of
                   unassigned/partially assigned HP task definitions.
                   (Effectively, maximize the negative sum).
    """
    num_fully_assigned_hp_task_definitions = 0
    penalty_score_from_unassigned_or_incomplete = 0  # Lower (more negative) is worse

    for task_def in hp_tasks_in_permutation:
        task_id = task_def["id"]
        quantity = int(task_def.get("quantity", 1))
        if quantity == 0:
            continue  # Skip 0-quantity tasks for scoring assignment success

        all_instances_of_this_task_def_assigned = True
        for i in range(1, quantity + 1):
            instance_id = f"{task_id}_{i}"
            if instance_id in hp_unassigned_reasons_for_permutation:
                all_instances_of_this_task_def_assigned = False
                break

        if all_instances_of_this_task_def_assigned:
            num_fully_assigned_hp_task_definitions += 1
        else:
            penalty_score_from_unassigned_or_incomplete += task_def["priority_val"]

    return (
        num_fully_assigned_hp_task_definitions,
        -penalty_score_from_unassigned_or_incomplete,
    )


def _assign_task_definition_to_schedule(
    task_to_assign,
    present_technicians,
    total_work_minutes,
    rep_assignments,
    logger,
    technician_schedules,
    all_task_assignments_details,
    unassigned_tasks_reasons_dict,
    incomplete_tasks_instance_ids,
    all_pm_task_names_from_excel_normalized_set,  # Passed through
    db_conn,  # Pass the database connection
    technician_technology_skills=None,
    under_resourced_tasks=None,
    technician_groups=None,
):
    """Processes a single task definition (which may have multiple instances due to
    quantity) and attempts to assign its instances to the provided schedules.

    This function encapsulates the main loop body from the original assign_tasks.
    Modifies technician_schedules, all_task_assignments_details, etc., in-place.
    """
    task_id = task_to_assign["id"]
    task_name_excel = task_to_assign.get("name", "Unknown")
    task_type = task_to_assign["task_type_upper"]
    base_duration = int(task_to_assign.get("planned_worktime_min", 0))
    num_technicians_needed = int(task_to_assign.get("mitarbeiter_pro_aufgabe", 1))
    quantity = int(task_to_assign.get("quantity", 1))
    is_additional_task_flag = task_to_assign.get("isAdditionalTask", False)

    if quantity <= 0:
        reason = f"Skipped ({task_type}): Invalid 'Quantity' ({quantity})."
        for i in range(1, max(1, quantity if quantity > 0 else 1)):
            unassigned_tasks_reasons_dict[f"{task_id}_{i}"] = reason
        return

    if num_technicians_needed == 0:
        if base_duration == 0:
            reason = (
                f"Skipped ({task_type}): Task requires 0 technicians and "
                "has 0 duration. Cannot be scheduled."
            )
        else:
            reason = (
                f"Skipped ({task_type}): Invalid 'Mitarbeiter pro Aufgabe' (0) "
                "for non-zero duration task."
            )

        for i in range(1, quantity + 1):
            unassigned_tasks_reasons_dict[f"{task_id}_{i}"] = reason
        _log(
            logger,
            "warning",
            f"Task definition {task_name_excel} (ID: {task_id}) unassigned "
            f"for all {quantity} instances: {reason}",
        )
        return

    if num_technicians_needed < 0:
        reason = (
            f"Skipped ({task_type}): Invalid 'Mitarbeiter pro Aufgabe' "
            f"({num_technicians_needed}) - value must be positive."
        )
        for i in range(1, quantity + 1):
            unassigned_tasks_reasons_dict[f"{task_id}_{i}"] = reason
        _log(
            logger,
            "warning",
            f"Task definition {task_name_excel} (ID: {task_id}) unassigned "
            f"for all {quantity} instances: {reason}",
        )
        return

    task_lines_str = str(task_to_assign.get("lines", ""))
    task_lines_list = []
    if (
        task_lines_str
        and task_lines_str.lower() != "nan"
        and task_lines_str.strip() != ""
    ):
        try:
            task_lines_list = [
                int(line.strip())
                for line in task_lines_str.split(",")
                if line.strip().isdigit()
            ]
        except ValueError:
            _log(
                logger,
                "warning",
                f"  Warning ({task_type}): Invalid line format "
                f"'{task_lines_str}' for task {task_name_excel}",
            )

    # Strategy Pattern Integration
    from .strategies.pm_strategy import PMAssignmentStrategy
    from .strategies.rep_strategy import REPAssignmentStrategy

    # Context Construction
    context = {
        "task_to_assign": task_to_assign,
        "quantity": quantity,
        "present_technicians": present_technicians,
        "technician_schedules": technician_schedules,
        "technician_technology_skills": technician_technology_skills,
        "task_lines_list": task_lines_list,
        "technician_lines": TECHNICIAN_LINES,  # Passing global
        "total_work_minutes": total_work_minutes,
        "db_conn": db_conn,
        "rep_assignments": rep_assignments,
        "under_resourced_tasks": under_resourced_tasks,
    }

    pm_strategy = PMAssignmentStrategy(logger)
    rep_strategy = REPAssignmentStrategy(logger)

    for instance_num in range(1, quantity + 1):
        instance_id_str = f"{task_id}_{instance_num}"
        context["instance_num"] = instance_num  # Update context per instance

        result = None
        if task_type == "PM" and not is_additional_task_flag:
            result = pm_strategy.assign_task(context)
        elif task_type == "REP":
            result = rep_strategy.assign_task(context)

        # Handle Result
        if result:
            if result["success"]:
                for assignment in result["assignments"]:
                    tech_name = assignment["technician"]
                    start = assignment["start"]
                    dur = assignment["duration"]
                    t_name = assignment["task_name"]

                    technician_schedules[tech_name].append((start, start + dur, t_name))
                    technician_schedules[tech_name].sort()

                    all_task_assignments_details.append(assignment)

                if result.get("incomplete_instance_id"):
                    if instance_id_str not in incomplete_tasks_instance_ids:
                        incomplete_tasks_instance_ids.append(instance_id_str)

                if instance_id_str in unassigned_tasks_reasons_dict:
                    del unassigned_tasks_reasons_dict[instance_id_str]

            else:
                unassigned_tasks_reasons_dict[instance_id_str] = result[
                    "failure_reason"
                ]
        else:
            # Fallback for unhandled types or no strategy called
            pass


def assign_tasks(
    tasks_to_assign,
    present_technicians,
    total_work_minutes,
    db_conn,
    rep_assignments,
    logger,
    technician_technology_skills=None,
):
    """Main entry point for task assignment.

    Iterates over tasks and delegates to specific strategies via
    _assign_task_definition_to_schedule.
    """
    # 1. Initialization
    all_task_assignments_details = []
    unassigned_tasks_reasons_dict = {}
    incomplete_tasks_instance_ids = []
    under_resourced_tasks = []

    technician_schedules = {tech: [] for tech in present_technicians}

    # Pre-calculate or fetch groups (if needed, though unused in strategies currently)
    technician_groups = None  # _get_technician_groups(db_conn)

    # 2. Sort tasks (PMs first usually preferred)
    # The dashboard.py does some sorting, but we can respect input order or sort again.
    # Assuming input 'tasks_to_assign' order is acceptable.

    # 3. Assign Tasks
    # We need a set for 'all_pm_task_names' just to satisfy the signature if legacy
    all_pm_task_names = set()

    for task in tasks_to_assign:
        _assign_task_definition_to_schedule(
            task,
            present_technicians,
            total_work_minutes,
            rep_assignments,
            logger,
            technician_schedules,
            all_task_assignments_details,
            unassigned_tasks_reasons_dict,
            incomplete_tasks_instance_ids,
            all_pm_task_names,  # Unused sort of
            db_conn,
            technician_technology_skills,
            under_resourced_tasks,
            technician_groups,
        )

    # 4. Workload Balancing (Optional but requested behavior)
    # Calculate available time
    available_time = {}
    for tech in present_technicians:
        scheduled_minutes = 0
        for start, end, _ in technician_schedules[tech]:
            scheduled_minutes += end - start
        available_time[tech] = total_work_minutes - scheduled_minutes

    # Call balancing (mutates structures)
    # Note: balance function expects 'assignments' list of dicts.
    # 'all_task_assignments_details' is that list.

    balance_workload_with_helpers(
        all_task_assignments_details,
        technician_schedules,
        available_time,
        present_technicians,
        total_work_minutes,
        technician_technology_skills,
        tasks_to_assign,
        rep_assignments,
        logger,
    )

    # 5. Return Results
    # Format matches dashboard.py expectation
    # (assigned_tasks, unassigned_reasons, incomplete_ids, avg_availability, ...)

    available_time_summary = available_time  # Reuse the dict

    return (
        all_task_assignments_details,
        unassigned_tasks_reasons_dict,
        incomplete_tasks_instance_ids,
        available_time_summary,
        under_resourced_tasks,
    )


def balance_workload_with_helpers(
    assignments,
    technician_schedules,
    available_time,
    present_technicians,
    total_work_minutes,
    technician_technology_skills,
    tasks,
    rep_assignments,
    logger,
):
    _log(logger, "info", "Starting workload balancing with helpers.")

    overloaded_threshold = total_work_minutes * 0.8
    idle_threshold = total_work_minutes * 0.5

    overloaded_techs = {
        tech
        for tech, time in available_time.items()
        if (total_work_minutes - time) > overloaded_threshold
    }
    idle_techs = {
        tech for tech, time in available_time.items() if time > idle_threshold
    }

    _log(
        logger,
        "info",
        f"Overloaded techs (>{overloaded_threshold / 60:.1f}h scheduled): "
        f"{overloaded_techs}",
    )
    _log(logger, "info", f"Idle techs (>{idle_threshold / 60:.1f}h free): {idle_techs}")

    if not overloaded_techs or not idle_techs:
        _log(
            logger,
            "info",
            "No overloaded or idle technicians found, skipping balancing.",
        )
        return assignments, technician_schedules, available_time

    rep_assignments_map = (
        {item["task_id"]: item for item in rep_assignments} if rep_assignments else {}
    )

    # Find tasks to help with
    for overloaded_tech in overloaded_techs:
        for task_assignment in list(assignments):
            if task_assignment["technician"] == overloaded_tech:
                # Find a helper
                for idle_tech in idle_techs:
                    if idle_tech == overloaded_tech:
                        continue

                    # Check if idle_tech has time
                    if (
                        available_time[idle_tech] < task_assignment["duration"] / 2
                    ):  # Heuristic
                        continue

                    # Check skills
                    task_id = task_assignment["instance_id"].split("_")[0]

                    original_task = next(
                        (t for t in tasks if str(t.get("id")) == task_id), None
                    )
                    if not original_task:
                        continue

                    can_help = False
                    task_type = original_task.get("task_type_upper")

                    if task_type == "REP":
                        rep_assignment_info = rep_assignments_map.get(
                            original_task.get("id")
                        )
                        if rep_assignment_info:
                            qualified_techs = {
                                tech["name"]
                                for tech in rep_assignment_info.get("technicians", [])
                            }
                            if idle_tech in qualified_techs:
                                can_help = True
                    else:  # For PM tasks
                        required_skills = original_task.get("technology_ids", [])
                        if not required_skills:
                            continue  # Cannot help if no skills are defined

                        helper_skills = technician_technology_skills.get(idle_tech, {})
                        if all(
                            skill_id in helper_skills and helper_skills[skill_id] > 0
                            for skill_id in required_skills
                        ):
                            can_help = True

                    if can_help:
                        _log(
                            logger,
                            "info",
                            f"Found helper '{idle_tech}' for task "
                            f"'{task_assignment['task_name']}' of "
                            f"technician '{overloaded_tech}'",
                        )

                        # Re-schedule the task for the group
                        original_start = task_assignment["start"]
                        original_duration = task_assignment["duration"]
                        new_duration = (
                            original_duration / 2
                        )  # Simple assumption for now

                        # Check if both are free
                        is_overloaded_tech_free = all(
                            sch_end <= original_start
                            or sch_start >= original_start + new_duration
                            for sch_start, sch_end, _ in technician_schedules[
                                overloaded_tech
                            ]
                            if _ != task_assignment["task_name"]
                        )
                        is_idle_tech_free = all(
                            sch_end <= original_start
                            or sch_start >= original_start + new_duration
                            for sch_start, sch_end, _ in technician_schedules[idle_tech]
                        )

                        if is_overloaded_tech_free and is_idle_tech_free:
                            # Remove old assignment
                            assignments.remove(task_assignment)
                            technician_schedules[overloaded_tech] = [
                                s
                                for s in technician_schedules[overloaded_tech]
                                if s[2] != task_assignment["task_name"]
                            ]

                            # Add new assignments for both
                            for tech in [overloaded_tech, idle_tech]:
                                assignments.append(
                                    {
                                        "technician": tech,
                                        "task_name": task_assignment["task_name"],
                                        "start": original_start,
                                        "duration": new_duration,
                                        "is_incomplete": task_assignment.get(
                                            "is_incomplete", False
                                        ),
                                        "original_duration": task_assignment.get(
                                            "original_duration"
                                        ),
                                        "instance_id": task_assignment["instance_id"],
                                        "technician_task_info": "Helper",
                                        "resource_mismatch_info": (
                                            "Helped by " + idle_tech
                                            if tech == overloaded_tech
                                            else "Helping " + overloaded_tech
                                        ),
                                    }
                                )
                                technician_schedules[tech].append(
                                    (
                                        original_start,
                                        original_start + new_duration,
                                        task_assignment["task_name"],
                                    )
                                )
                                technician_schedules[tech].sort()

                            # Update available time
                            available_time[overloaded_tech] += (
                                original_duration - new_duration
                            )
                            available_time[idle_tech] -= new_duration

                            _log(
                                logger,
                                "info",
                                f"Task '{task_assignment['task_name']}' "
                                f"rescheduled with helper '{idle_tech}'.",
                            )
                            # Move to next task
                            break
                else:
                    continue
                break

    _log(logger, "info", "Workload balancing finished.")

    _log(logger, "debug", "Final workload after balancing:")
    for tech in present_technicians:
        occupied_time = total_work_minutes - available_time.get(
            tech, total_work_minutes
        )
        percentage_occupied = (
            (occupied_time / total_work_minutes) * 100 if total_work_minutes > 0 else 0
        )
        _log(
            logger,
            "debug",
            f"  - {tech}: {occupied_time:.2f} minutes occupied "
            f"({percentage_occupied:.2f}%)",
        )

    return assignments, technician_schedules, available_time


def _get_technician_groups(db_conn):
    cursor = db_conn.cursor()

    # Get all groups
    cursor.execute("SELECT id, name FROM technician_groups")
    # groups = {
    #     row["id"]: {"name": row["name"], "members": []} for row in cursor.fetchall()
    # }

    # Get group members
    cursor.execute(
        "SELECT g.name as group_name, t.name as tech_name FROM "
        "technician_group_members gm JOIN technicians t ON "
        "gm.technician_id = t.id JOIN technician_groups g ON gm.group_id = g.id"
    )
    technician_to_groups = {}
    for row in cursor.fetchall():
        if row["tech_name"] not in technician_to_groups:
            technician_to_groups[row["tech_name"]] = []
        technician_to_groups[row["tech_name"]].append(row["group_name"])

    # Create a technician-centric view
    technician_groups_data = {}
    for tech_name, tech_groups in technician_to_groups.items():
        technician_groups_data[tech_name] = {"groups": tech_groups}

    return technician_groups_data
