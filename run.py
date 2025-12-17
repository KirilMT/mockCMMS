"""Application entry point."""

import sys
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the monorepo root to sys.path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import create_app after setting up path and environment
from src.app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    print("Starting mockCMMS application...")
    # Note: In debug mode, Flask's reloader spawns a child process,
    # causing app initialization to run twice. This is normal behavior.
    # Set use_reloader=False to disable if the double output is distracting.
    app.run(debug=True, port=5000)
