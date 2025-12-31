"""Application entry point."""

import os
import sys

# Configure UTF-8 encoding for stdout/stderr to handle emojis on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from dotenv import load_dotenv

from src.app import create_app

# Load environment variables
load_dotenv()

# Initialize app with DEBUG=True to ensure development logging
# (standard terminal output). This overrides any defaults from .env.
app = create_app(config_overrides={"DEBUG": True})

if __name__ == "__main__":
    # Support E2E test mode with custom port
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    is_e2e_test = os.getenv("E2E_TEST", "").lower() in ("true", "1", "yes")

    if is_e2e_test:
        print(f"🧪 Starting mockCMMS in E2E TEST mode on port {port}...")
    else:
        print(f"Starting mockCMMS application on port {port}...")

    # Note: In debug mode, Flask's reloader spawns a child process.
    # We disable it for E2E tests to ensure clean process termination (PID handling).
    app.run(debug=True, port=port, use_reloader=not is_e2e_test)
