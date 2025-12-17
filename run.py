"""Application entry point."""

from dotenv import load_dotenv
from src.app import create_app

# Load environment variables
load_dotenv()

app = create_app()

if __name__ == "__main__":
    print("Starting mockCMMS application...")
    # Note: In debug mode, Flask's reloader spawns a child process,
    # causing app initialization to run twice. This is normal behavior.
    # Set use_reloader=False to disable if the double output is distracting.
    app.run(debug=True, port=5000)
