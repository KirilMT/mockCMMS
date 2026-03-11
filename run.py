"""Application entry point."""

import os
import sys

# Configure UTF-8 encoding for stdout/stderr to handle emojis on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]


def check_setup():
    """Verify that the environment is correctly set up.

    This MUST be called before importing any project modules (src.app, etc.) to ensure
    dependencies are available.
    """
    # Skip validation in CI/CD or E2E testing environments
    # These environments might install dependencies globally (no .venv needed)
    if os.environ.get("CI") or os.environ.get("E2E_TEST"):
        return

    # Setup Validation: Check if .venv exists
    if not os.path.exists(".venv"):
        print("\nERROR: Setup incomplete!")
        print("Please run the setup script first:")
        print("    .\\scripts\\setup.ps1")
        print("\nThe application cannot start without proper setup.\n")
        sys.exit(1)


# =============================================================================
# CRITICAL: Run setup check BEFORE importing any project modules!
# This ensures dependencies exist before any Flask/SQLAlchemy code runs.
# =============================================================================
check_setup()

# Now it's safe to import project modules (after setup is verified)
from dotenv import load_dotenv  # noqa: E402

from src.app import create_app  # noqa: E402

# Load environment variables
load_dotenv()

# Initialize app lazily - only create when needed (not during test imports)
# This prevents accidental DB creation during test module imports
_app = None


def get_app():
    """Get or create the Flask application instance."""
    global _app
    if _app is None:
        _app = create_app(config_overrides={"DEBUG": True})
    return _app


# For backwards compatibility with code that imports `app` from run
# Only create the app at module level if NOT in testing mode
if os.environ.get("TESTING") != "1":
    app = get_app()
else:
    app = None


if __name__ == "__main__":
    # Ensure app is created for running
    app = get_app()

    # Support E2E test mode with custom port
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    is_e2e_test = os.getenv("E2E_TEST", "").lower() in ("true", "1", "yes")

    if is_e2e_test:
        print(f"🧪 Starting mockCMMS in E2E TEST mode on port {port}...")
    else:
        print(f"Starting mockCMMS application on port {port}...")

    # Note: In debug mode, Flask's reloader spawns a child process.
    # We disable it for E2E tests to ensure clean process termination (PID handling).
    app.run(
        host="127.0.0.1",
        debug=True,
        port=port,
        use_reloader=not is_e2e_test,
        threaded=True,
    )
