# conftest.py
"""Root configuration for pytest - handles dynamic modular app test discovery.

Modular Isolation:
    To improve development speed, individual apps under `apps/` can be
    excluded from test collection by setting environment variables:
    - PLANNING_ENABLED=false
    - REPORTS_ENABLED=false

    By default, apps are considered enabled to ensure total project coverage
    unless explicitly set to 'false', '0', or 'f'.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file BEFORE any test collection
load_dotenv()

# Set TESTING globally for all pytest runs
os.environ["TESTING"] = "1"


def pytest_ignore_collect(collection_path, config):
    """Dynamically skip modular app tests if the app is disabled via environment
    variable."""
    path_obj = Path(str(collection_path))

    # Check if we are inside the 'apps' directory
    if "apps" in path_obj.parts:
        try:
            apps_index = path_obj.parts.index("apps")
            if len(path_obj.parts) > apps_index + 1:
                app_name = path_obj.parts[apps_index + 1]

                # Construct environment variable name (e.g., PLANNING_ENABLED)
                env_var = f"{app_name.upper()}_ENABLED"

                # Check if the app is explicitly disabled
                # Default to ENABLED if not found to ensure new apps are tested
                # unless explicitly turned off during 'incubation'
                enabled_val = os.getenv(env_var, "true").lower()

                if enabled_val not in ("true", "1", "t"):
                    return True  # Ignore this directory/file
        except (ValueError, IndexError):
            pass

    return False
