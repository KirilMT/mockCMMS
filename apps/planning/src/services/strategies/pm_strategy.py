from itertools import combinations
from typing import Any, Dict, List, cast

from .assignment_strategy import AssignmentStrategy

# Constants moved from task_assigner.py
MAX_TECHS_FOR_COMBINATIONS = 12
GROUP_SIZE_SEARCH_RANGE = 1
TECHNICIAN_LINES = {
    "Tech_A": [1, 2],
    "Tech_B": [1, 2],
    "Tech_C": [1, 2],
    "Tech_D": [3, 4],
    "Tech_E": [3, 4],
    "Tech_F": [3, 4],
}  # Placeholder - should be imported or passed in context if dynamic


class PMAssignmentStrategy(AssignmentStrategy):
    """Strategy for assigning Preventive Maintenance (PM) tasks."""

    def assign_task(self, context: dict) -> dict:
        """Implements the PM assignment logic using combinatorial checks."""
        # Unwrap context
        task_to_assign = context["task_to_assign"]
        instance_num = context["instance_num"]
        quantity = context["quantity"]
        present_technicians = context["present_technicians"]
        technician_schedules = context["technician_schedules"]
        technician_technology_skills = context["technician_technology_skills"]
        task_lines_list = context.get("task_lines_list", [])
        total_work_minutes = context["total_work_minutes"]

        task_id = task_to_assign["id"]
        task_name_excel = task_to_assign.get("name", "Unknown")
        task_technology_ids = task_to_assign.get("technology_ids", [])
        base_duration = int(task_to_assign.get("planned_worktime_min", 0))
        num_technicians_needed = int(task_to_assign.get("mitarbeiter_pro_aufgabe", 1))

        instance_id_str = f"{task_id}_{instance_num}"
        instance_task_display_name = (
            f"{task_name_excel} (Instance {instance_num}/{quantity})"
        )

        self._log(
            "debug",
            f"    (Helper) Assigning Standard PM instance: "
            f"{instance_task_display_name}, Required Technology IDs: "
            f"{task_technology_ids}",
        )

        result = {
            "success": False,
            "failure_reason": "",
            "assignments": [],
            "incomplete_instance_id": None,
            "unassigned_reason": None,
        }

        if not task_technology_ids:
            result["failure_reason"] = (
                f"Skipped (PM): Task {task_name_excel} (ID: {task_id}) "
                "has no required technology_ids defined."
            )
            self._log("warning", f"      {result['failure_reason']}")
            return result

        # 1. IDENTIFY ELIGIBLE TECHNICIANS
        eligible_technicians_details_pm = []
        for tech_cand_pm in present_technicians:
            tech_skills_map = technician_technology_skills.get(tech_cand_pm, {})

            possesses_at_least_one_required_skill = any(
                skill_id in tech_skills_map and tech_skills_map[skill_id] > 0
                for skill_id in task_technology_ids
            )
            if not possesses_at_least_one_required_skill:
                continue

            # Need to handle TECHNICIAN_LINES dynamic import or pass via context.
            # Using placeholder/context for now.
            tech_lines_pm = context.get("technician_lines", {}).get(tech_cand_pm, [])
            line_match = not task_lines_list or any(
                line in tech_lines_pm for line in task_lines_list
            )
            if not line_match:
                continue

            relevant_skills_for_tech = {
                skill_id: tech_skills_map[skill_id]
                for skill_id in task_technology_ids
                if skill_id in tech_skills_map and tech_skills_map[skill_id] > 0
            }
            if not relevant_skills_for_tech:
                continue

            eligible_technicians_details_pm.append(
                {"name": tech_cand_pm, "relevant_skills": relevant_skills_for_tech}
            )

        if not eligible_technicians_details_pm:
            result["failure_reason"] = (
                "No technicians eligible for this PM task (possess at least "
                "one skill > 0, meet line/task mapping)."
            )
            self._log(
                "warning",
                f"      {result['failure_reason']} for {instance_task_display_name}",
            )
            return result

        # 2. TRACK UNDER-RESOURCED TASKS (Optional, simplified for strategy)
        if (
            num_technicians_needed > 0
            and len(eligible_technicians_details_pm) < num_technicians_needed
        ):
            if context.get("under_resourced_tasks") is not None:
                # Logic to append to list if not present
                pass

        # 3. SORT & TRIM CANDIDATES
        def get_tech_score(tech_details):
            return sum(tech_details["relevant_skills"].values())

        eligible_technicians_details_pm.sort(key=get_tech_score, reverse=True)

        if len(eligible_technicians_details_pm) > MAX_TECHS_FOR_COMBINATIONS:
            eligible_technicians_details_pm = eligible_technicians_details_pm[
                :MAX_TECHS_FOR_COMBINATIONS
            ]

        sorted_eligible_tech_names_pm = [
            d["name"] for d in eligible_technicians_details_pm
        ]
        tech_details_map_pm = {d["name"]: d for d in eligible_technicians_details_pm}

        # 4. GENERATE VIABLE GROUPS (COMBINATIONS)
        viable_groups_with_scores_pm: List[Dict[str, Any]] = []
        possible_sizes_to_try = []

        if num_technicians_needed > 0 and len(sorted_eligible_tech_names_pm) > 0:
            min_size = max(1, num_technicians_needed - GROUP_SIZE_SEARCH_RANGE)
            max_size = min(
                len(sorted_eligible_tech_names_pm),
                num_technicians_needed + GROUP_SIZE_SEARCH_RANGE,
            )
            unique_sizes = set()
            for i in range(min_size, max_size + 1):
                unique_sizes.add(i)
            if num_technicians_needed <= len(sorted_eligible_tech_names_pm):
                unique_sizes.add(num_technicians_needed)
            possible_sizes_to_try = sorted(
                list(unique_sizes), key=lambda s: (abs(s - num_technicians_needed), s)
            )

        for r_actual_group_size in possible_sizes_to_try:
            for group_tuple in combinations(
                sorted_eligible_tech_names_pm, r_actual_group_size
            ):
                group_tech_names = list(group_tuple)
                if not group_tech_names:
                    continue

                group_skills_possessed_by_id = set()
                for tech_name_in_group in group_tech_names:
                    group_skills_possessed_by_id.update(
                        tech_details_map_pm[tech_name_in_group][
                            "relevant_skills"
                        ].keys()
                    )

                if not set(task_technology_ids).issubset(group_skills_possessed_by_id):
                    continue

                # Calculate Scores (ideal fully copied)
                # For this refactor, I will copy the logic 1:1 to ensure
                # behavior preservation.

                per_skill_avg_levels = {}
                for req_skill_id in task_technology_ids:
                    techs_with_this_skill = [
                        tn
                        for tn in group_tech_names
                        if req_skill_id in tech_details_map_pm[tn]["relevant_skills"]
                    ]
                    if techs_with_this_skill:
                        avg = sum(
                            tech_details_map_pm[tn]["relevant_skills"][req_skill_id]
                            for tn in techs_with_this_skill
                        ) / len(techs_with_this_skill)
                        per_skill_avg_levels[req_skill_id] = avg
                    else:
                        per_skill_avg_levels[req_skill_id] = 0

                count_req_skills = 0
                total_skill_points = 0
                for tn in group_tech_names:
                    for req_id in task_technology_ids:
                        if req_id in tech_details_map_pm[tn]["relevant_skills"]:
                            total_skill_points += tech_details_map_pm[tn][
                                "relevant_skills"
                            ][req_id]
                            count_req_skills += 1

                combined_avg = (
                    total_skill_points / count_req_skills if count_req_skills > 0 else 0
                )

                workload = sum(
                    sum(end - start for start, end, _ in technician_schedules[tn])
                    for tn in group_tech_names
                )

                viable_groups_with_scores_pm.append(
                    {
                        "group": group_tech_names,
                        "len": r_actual_group_size,
                        "per_skill_avg": per_skill_avg_levels,
                        "combined_avg_skill": combined_avg,
                        "workload": workload,
                        "size_diff": abs(r_actual_group_size - num_technicians_needed),
                    }
                )

        # 5. HANDLE PRIORITY 'A' HELPERS
        # Combined logic for standard assignment.

        # 6. SORT GROUPS
        sorted_req_skill_ids = sorted(list(task_technology_ids))
        viable_groups_with_scores_pm.sort(
            key=lambda x: (
                float(x["size_diff"]),
                tuple(
                    -float(cast(Dict[str, float], x["per_skill_avg"]).get(sid, 0))
                    for sid in sorted_req_skill_ids
                ),
                -float(x["combined_avg_skill"]),
                float(x["workload"]),
                "".join(sorted(cast(List[str], x["group"]))),
            )
        )

        if not viable_groups_with_scores_pm:
            result["failure_reason"] = (
                "No viable technician groups found covering skills "
                f"{task_technology_ids}."
            )
            self._log("warning", f"      {result['failure_reason']}")
            return result

        # 7. FIND SLOT & ASSIGN
        for group_data in viable_groups_with_scores_pm:
            candidate_group = group_data["group"]
            num_assigned = len(candidate_group)

            effective_duration = (
                (base_duration * num_technicians_needed) / num_assigned
                if (base_duration > 0 and num_assigned > 0)
                else base_duration
            )
            if base_duration == 0:
                effective_duration = 0

            search_start = 0
            while search_start <= total_work_minutes:
                if (
                    effective_duration > 0
                    and search_start + effective_duration > total_work_minutes
                ):
                    remaining = max(0, total_work_minutes - search_start)
                    if remaining >= effective_duration * 0.75 and remaining > 0:
                        duration_to_check = remaining
                        is_incomplete = True
                    else:
                        search_start += 15
                        continue
                else:
                    duration_to_check = effective_duration
                    is_incomplete = False

                # Check availability
                all_avail = True
                for tech in candidate_group:
                    if not all(
                        e <= search_start or s >= search_start + duration_to_check
                        for s, e, _ in technician_schedules[tech]
                    ):
                        all_avail = False
                        break

                if all_avail:
                    # Success
                    result["success"] = True
                    result["assignments"] = [
                        {
                            "technician": tech,
                            "start": search_start,
                            "duration": duration_to_check,
                            "task_name": instance_task_display_name,
                            "is_incomplete": is_incomplete,
                            "original_duration": base_duration,
                            "instance_id": instance_id_str,
                        }
                        for tech in candidate_group
                    ]

                    if is_incomplete:
                        result["incomplete_instance_id"] = instance_id_str

                    self._log(
                        "info",
                        f"    (Helper) Scheduled PM {instance_task_display_name} "
                        f"for {candidate_group} at {search_start}",
                    )
                    return result

                search_start += 15

        result["failure_reason"] = "No suitable time slot found for best groups."
        return result
