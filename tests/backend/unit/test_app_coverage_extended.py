import os
import sys
from unittest.mock import patch

# Ensure sys.path is correct for imports if running standalone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.app import create_app  # noqa: E402


class TestAppCoverageExtended:
    def test_ensure_main_instance_folder_error(self):
        """Test error handling when creating main instance folder fails."""

        # Use simple side effect
        def makedirs_side_effect(path, **kwargs):
            # We want to fail the main instance creation.
            # Usually create_app is called with instance_path inside root/instance
            if "instance" in str(path) and "planning" not in str(path):
                raise OSError("Permission Denied")
            return None

        # We must disable planning to stay focused on main app logic
        # or ensure side effect handles both
        with patch.dict(os.environ, {"PLANNING_ENABLED": "False"}):
            with patch("src.app.os.makedirs", side_effect=makedirs_side_effect):
                app = create_app({"TESTING": True})
                # It catches OSError and logs it, so app should return OK
                assert app is not None
