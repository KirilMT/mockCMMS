# src/config_manager.py
import json
import os
import sqlite3
import traceback

from .planning_db_utils import (
    get_db_connection,
    get_technician_lines_via_satellite_point,
)

# --- Configuration Store ---

TECHNICIAN_LINES: dict[str, list[str]] = {}
TECHNICIANS: list[str] = []
TECHNICIAN_GROUPS: dict[str, list[str]] = {}


# Load task name mapping from external config
def _load_task_name_mapping():
    try:
        from ..config import Config

        config = Config()
        return config._config.get("task_name_mapping", {})
    except Exception:
        return {}


TASK_NAME_MAPPING = _load_task_name_mapping()


def load_app_config(database_path, logger=None):  # Added logger argument
    TECHNICIAN_LINES.clear()
    TECHNICIAN_LINES.clear()
    TECHNICIANS.clear()
    TECHNICIAN_GROUPS.clear()
    # Initialize default groups. Satellite points will be dynamic from DB.
    # The concept of TECHNICIAN_GROUPS might align with satellite points now.
    # It populated based on technician's satellite point name.
    # We will fetch all satellite points and use their names as keys if needed.

    def _log(message, level="info"):
        if logger:
            if level == "info":
                logger.info(message)
            elif level == "warning":
                logger.warning(message)
            elif level == "error":
                logger.error(message)
            # Removed explicit debug level handling here to reduce verbosity
            # If a message was intended for debug, it won't be printed
            # unless logger's global level is DEBUG
            # and the call to _log specifies 'debug'.
            # For very detailed debugging, direct logger.debug() calls can be used.
        else:
            print(f"{level.upper()}: {message}")  # Fallback

    if not database_path:
        _log("  Database path not provided. Skipping config load.", "warning")
        return

    _log(
        f"Attempting to load configuration from database: "
        f"{os.path.abspath(database_path)}"
    )
    conn = None
    try:
        conn = get_db_connection(database_path)
        if not conn:
            _log("  Failed to get database connection for config load.", "error")
            return
        _log("  Successfully connected to the database for config load.")
        cursor = conn.cursor()

        # Fetch all satellite points to map their IDs to names for
        # TECHNICIAN_GROUPS population
        cursor.execute("SELECT id, name FROM satellite_points")
        satellite_points_map = {sp["id"]: sp["name"] for sp in cursor.fetchall()}
        # Initialize TECHNICIAN_GROUPS with names from satellite_points table
        for sp_name in satellite_points_map.values():
            if sp_name not in TECHNICIAN_GROUPS:
                TECHNICIAN_GROUPS[sp_name] = []

        # Updated query to fetch satellite_point_id
        sql_query = "SELECT id, name, satellite_point_id FROM technicians ORDER BY name"
        cursor.execute(sql_query)
        db_technicians = cursor.fetchall()
        _log(
            f"  Query executed. Rows fetched from 'technicians' table: "
            f"{len(db_technicians)}"
        )

        if not db_technicians:
            _log(
                "  'technicians' table appears empty or query returned no results.",
                "warning",
            )

        for row_idx, row in enumerate(db_technicians):
            tech_id = row["id"]
            tech_name = row["name"]
            tech_satellite_point_id = row["satellite_point_id"]

            # Determine satellite point name for grouping, with a fallback
            tech_satellite_point_name = satellite_points_map.get(
                tech_satellite_point_id, "Unassigned"
            )

            if not tech_name:
                _log(
                    f"      SKIPPING row {row_idx + 1} (ID {tech_id}) "
                    "due to missing name.",
                    "warning",
                )
                continue

            TECHNICIANS.append(tech_name)

            # Add technician to the correct group (satellite point)
            if tech_satellite_point_name not in TECHNICIAN_GROUPS:
                TECHNICIAN_GROUPS[tech_satellite_point_name] = []
            TECHNICIAN_GROUPS[tech_satellite_point_name].append(tech_name)

            # Fetch lines for the technician using their satellite_point_id
            # via the new db_utils function.
            # technician_actual_lines returns a list of line names.
            # Assumes line *names* are now expected in TECHNICIAN_LINES.
            # If line IDs were expected, the function would need adjustment.
            # For now, proceeding with line names as strings.
            technician_actual_lines = get_technician_lines_via_satellite_point(
                conn, tech_id
            )
            TECHNICIAN_LINES[tech_name] = technician_actual_lines

        _log(
            f"Successfully loaded configuration for {len(TECHNICIANS)} "
            "technicians via config_manager."
        )

    except sqlite3.Error as e:
        _log(f"SQLite error during config load in config_manager: {e}", "error")
        _log(traceback.format_exc(), "error")
    except Exception as e:
        _log(
            f"General error loading configuration from database in config_manager: {e}",
            "error",
        )
        _log(traceback.format_exc(), "error")
    finally:
        if conn:
            conn.close()
        else:
            _log(
                "  No active database connection to close in config_manager.", "warning"
            )


def load_shift_config():
    """Loads shift duration configuration from config.json or config.example.json."""
    # current file is apps/planning/src/services/config_manager.py
    # config files are in apps/planning/config/

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "config"))

    config_path = os.path.join(config_dir, "config.json")
    example_config_path = os.path.join(config_dir, "config.example.json")

    default_config = {"shift_durations": {"shift_break": 30, "weekend": 720}}

    loaded_config = {}

    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                loaded_config = json.load(f)
        elif os.path.exists(example_config_path):
            with open(example_config_path, "r") as f:
                loaded_config = json.load(f)
        else:
            return default_config

        # Merge with defaults to ensure keys exist
        if "shift_durations" not in loaded_config:
            loaded_config["shift_durations"] = default_config["shift_durations"]
        else:
            # Ensure both keys exist in sub-dictionary
            if "shift_break" not in loaded_config["shift_durations"]:
                loaded_config["shift_durations"]["shift_break"] = default_config[
                    "shift_durations"
                ]["shift_break"]
            if "weekend" not in loaded_config["shift_durations"]:
                loaded_config["shift_durations"]["weekend"] = default_config[
                    "shift_durations"
                ]["weekend"]

        return loaded_config

    except Exception as e:
        print(f"Error loading config: {e}")
        return default_config
