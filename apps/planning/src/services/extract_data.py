"""
LEGACY: Originally PlanningManager module, renamed to planning.
This file is scheduled for removal in Phase 4 cleanup (Excel workflow removal).
Do not invest in new features here - file will be deleted.
See: apps/planning/docs/roadmap/05_PHASE_4_CLEANUP.md section 6.2
"""

import pandas as pd
from datetime import datetime, timedelta
import re
import requests

# Import the main Flask Config class
from apps.planning.src.config import Config as FlaskConfig


# Define the mockCMMS API URL
MOCK_CMMS_API_URL = "http://127.0.0.1:5001/api/v1/tasks"


def _fetch_data_from_api():
    """Fetches task data from the mockCMMS API."""
    try:
        response = requests.get(MOCK_CMMS_API_URL, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        api_data = response.json()

        # The API returns data in a format that is already very close to what's needed.
        # We just need to ensure the keys match what the rest of the application expects.
        # The `to_dict()` method in the mockCMMS Task model was designed for this.
        # No complex validation is done here, assuming the API is a trusted source.

        return api_data, []  # Return data and an empty list for errors

    except requests.exceptions.RequestException as e:
        error_message = f"Could not connect to mockCMMS API at {MOCK_CMMS_API_URL}. Please ensure the mockCMMS server is running. Error: {e}"
        return [], [error_message]
    except Exception as e:
        return [], [f"An unexpected error occurred while fetching data from API: {e}"]


def _extract_data_from_excel(excel_file_object):
    """Extracts and validates data from an Excel file object."""
    try:
        error_messages = []
        sheet_name = get_current_week()[0]
        current_day = get_current_day()
        current_shift = get_current_shift()
        current_week = get_current_week_number()

        original_filename = getattr(excel_file_object, "filename", "").lower()
        engine_to_use = "pyxlsb" if original_filename.endswith(".xlsb") else "openpyxl"

        df = pd.read_excel(
            excel_file_object, sheet_name=sheet_name, engine=engine_to_use, header=None
        )

        filtered_df, target_col = find_and_filter_data(df, current_day, current_shift)

        headers = fill_merged_cells(df.iloc[1])

        required_columns = {
            "scheduler_col": "Scheduler Group /  Task",
            "planning_notes_col": "Planning notes",
            "lines_col": "Lines",
            "mitarbeiter_col": "Mitarbeiter pro Aufgabe",
            "worktime_col": "Planned Worktime in Min",
            "priority_col": "Prio",
            "task_type_col": "&",
            "ticket_mo_col": "Ticket oder MO ID",
        }

        column_indices = {}
        for col_name, header_text in required_columns.items():
            if col_name == "task_type_col":
                matching_columns = headers[
                    headers.str.contains(r"&", na=False, case=False)
                ]
                if matching_columns.empty:
                    filtered_df["task_type"] = "PM"
                    column_indices[col_name] = "task_type"
                else:
                    column_indices[col_name] = matching_columns.index[0]
            else:
                normalized_search_header = re.sub(
                    r"\\s+", " ", header_text.lower().replace("\\n", " ").strip()
                )
                normalized_search_header = re.sub(
                    r"\\s*/\\s*", "/", normalized_search_header
                )

                excel_headers_normalized = headers.str.lower().str.replace(
                    "\\n", " ", regex=False
                )
                excel_headers_normalized = excel_headers_normalized.str.replace(
                    r"\\s*/\\s*", "/", regex=True
                )
                excel_headers_normalized = excel_headers_normalized.str.replace(
                    r"\\s+", " ", regex=True
                ).str.strip()

                matching_columns = headers[
                    excel_headers_normalized.str.contains(
                        normalized_search_header, na=False, case=False
                    )
                ]

                if matching_columns.empty and col_name not in [
                    "planning_notes_col",
                    "priority_col",
                    "ticket_mo_col",
                ]:
                    raise ValueError(
                        f"Column '{header_text}' not found in Excel row 2 (index 1)."
                    )
                elif matching_columns.empty:
                    default_value = ""
                    if col_name == "priority_col":
                        default_value = "R"
                    filtered_df[col_name.replace("_col", "")] = default_value
                    column_indices[col_name] = col_name.replace("_col", "")
                else:
                    column_indices[col_name] = matching_columns.index[0]

        if column_indices["task_type_col"] != "task_type":
            filtered_df.iloc[:, column_indices["task_type_col"]] = filtered_df.iloc[
                :, column_indices["task_type_col"]
            ].apply(
                lambda x: (
                    re.match(r"^(PM|Rep)", str(x), re.IGNORECASE).group(0).upper()
                    if re.match(r"^(PM|Rep)", str(x), re.IGNORECASE)
                    else "PM"
                )
            )

        extracted_data = []
        for i in range(len(filtered_df)):
            row_data = {}
            for key, col_key in column_indices.items():
                if isinstance(col_key, str):  # Defaulted column
                    row_data[key.replace("_col", "")] = filtered_df[col_key].iloc[i]
                else:  # Column found in Excel
                    row_data[key.replace("_col", "")] = filtered_df.iloc[i, col_key]

            row_data["quantity"] = filtered_df.iloc[i, target_col]

            # --- VALIDATIONS ---
            # (Simplified for brevity, original validation logic can be retained or adapted)
            val_scheduler_group_task = str(row_data.get("scheduler", "")).strip()
            if (
                not val_scheduler_group_task
                or val_scheduler_group_task.lower() == "nan"
            ):
                error_messages.append(
                    f"Excel Row {filtered_df.index[i] + 1}: Scheduler Group / Task cannot be blank."
                )
                continue

            # ... other validations ...

            ticket_mo = str(row_data.get("ticket_mo", "")).strip()
            ticket_url = ""
            if (
                str(row_data.get("task_type", "")).upper() == "REP"
                and ticket_mo
                and ticket_mo.lower() != "nan"
            ):
                try:
                    from config import Config as ServicesConfig

                    config = ServicesConfig()
                    if len(ticket_mo) <= 6:
                        ticket_url = config.get_ticket_url(ticket_mo)
                    else:
                        ticket_url = config.get_maintenance_grid_url(ids=ticket_mo)
                except ImportError:
                    pass

            extracted_data.append(
                {
                    "scheduler_group_task": val_scheduler_group_task,
                    "planning_notes": str(row_data.get("planning_notes", "")),
                    "lines": str(row_data.get("lines", "")),
                    "mitarbeiter_pro_aufgabe": str(row_data.get("mitarbeiter", "")),
                    "planned_worktime_min": str(row_data.get("worktime", "")),
                    "priority": str(row_data.get("priority", "")),
                    "quantity": str(row_data.get("quantity", "")),
                    "task_type": str(row_data.get("task_type", "")),
                    "ticket_mo": ticket_mo,
                    "ticket_url": ticket_url,
                }
            )

        if not extracted_data and not error_messages:
            error_messages.append(
                f"No tasks found after filtering sheet '{sheet_name}'."
            )

        return extracted_data, error_messages

    except Exception as e:
        return [], [f"Critical error during Excel data extraction: {e}"]


def extract_data(excel_file_object=None):
    """Dispatcher function to extract data from the configured data source.

    If DATA_SOURCE is 'api', it fetches from the mockCMMS API. If DATA_SOURCE is
    'excel', it uses the provided excel_file_object.
    """
    if FlaskConfig and FlaskConfig.DATA_SOURCE == "api":
        return _fetch_data_from_api()
    elif excel_file_object:
        return _extract_data_from_excel(excel_file_object)
    else:
        return [], ["No data source configured or Excel file provided."]


# --- Helper functions for Excel extraction ---


def _now():
    """Return debug fixed datetime if configured, else real current datetime."""
    if FlaskConfig:
        try:
            fixed = FlaskConfig.get_fixed_datetime()
            if fixed:
                return fixed
        except Exception:
            pass
    return datetime.now()


def get_current_week():
    current_date = _now()
    return f"Summary KW{current_date.isocalendar().week:02d}", current_date


def get_current_week_number():
    return f"{_now().isocalendar().week:02d}"


def get_current_day():
    current_date = _now()
    return (
        (current_date - timedelta(days=1)).strftime("%A")
        if current_date.hour < 6
        else current_date.strftime("%A")
    )


def get_current_shift():
    return "early" if 6 <= _now().hour < 18 else "late"


def fill_merged_cells(row):
    filled_row = row.copy()
    last_value = ""
    for i in range(len(filled_row)):
        if pd.isna(filled_row.iloc[i]) or str(filled_row.iloc[i]).strip() == "":
            filled_row.iloc[i] = last_value
        else:
            last_value = str(filled_row.iloc[i]).strip()
    return filled_row


def find_and_filter_data(df, current_day, current_shift):
    day_headers_row = fill_merged_cells(df.iloc[0])
    shift_headers_row = fill_merged_cells(df.iloc[1])

    target_header = f"{current_day} CW-{get_current_week_number()}"
    matching_columns_for_day = [
        idx
        for idx, val in enumerate(day_headers_row)
        if str(val).strip() == target_header
    ]

    if not matching_columns_for_day:
        raise ValueError(f"No columns found for day header '{target_header}'.")

    target_col = next(
        (
            idx
            for idx in matching_columns_for_day
            if str(shift_headers_row.iloc[idx]).lower().strip() == current_shift
        ),
        None,
    )

    if target_col is None:
        raise ValueError(
            f"Column for {current_day} with shift '{current_shift}' not found."
        )

    df.iloc[:, target_col] = pd.to_numeric(df.iloc[:, target_col], errors="coerce")
    filtered_df = df[
        df.iloc[:, target_col].notna() & (df.iloc[:, target_col] >= 1)
    ].copy()
    filtered_df = filtered_df[filtered_df.index >= 9]

    if filtered_df.empty:
        raise ValueError(
            f"No data rows found with quantity >= 1 for the current shift."
        )

    return filtered_df, target_col
