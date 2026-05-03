"""Application entry point."""

import os
import sys

# =====================================================================
# SILENT MODE FOR PORTABLE DISTRIBUTION
# Must be initialized BEFORE any modules are imported to suppress all logs
# from Flask, db seeding, Werkzeug, etc.
# =====================================================================
is_portable = os.environ.get("PORTABLE_DISTRIBUTION", "").lower() in (
    "true",
    "1",
    "yes",
)
if is_portable:
    devnull = open(os.devnull, "w")
    sys.stdout = devnull
    sys.stderr = devnull

    def _portable_excepthook(exc_type, exc_value, exc_traceback):
        out = getattr(sys, "__stdout__", None)
        if out:
            out.write(f"\n\r❌ FATAL SERVER ERROR: {exc_value}\n")
            out.flush()

    sys.excepthook = _portable_excepthook


# =====================================================================
# IMMEDIATE SPINNER POLLING THREAD
# Starts right away to mask the import delay of Flask & SQLAlchemy
# =====================================================================
def _portable_startup_sequence() -> None:
    """Startup sequence for portable mode with a spinner and auto-open browser."""
    import time
    import webbrowser
    from http.client import HTTPConnection

    animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    out = getattr(sys, "__stdout__", None)

    server_ready = False
    for i in range(120):  # Spin for up to 60 seconds
        spinner = animation[i % len(animation)]
        if out:
            out.write(f"\r{spinner} ⏳ Starting background server... ")
            out.flush()

        try:
            conn = HTTPConnection("127.0.0.1", 5000, timeout=1)
            conn.request("HEAD", "/")
            conn.getresponse()
            conn.close()
            server_ready = True
            break
        except Exception as e:
            if hasattr(e, "code"):
                server_ready = True
                break
            time.sleep(0.5)

    if out and server_ready:
        # Replaces the spinner line with the target static confirmation.
        out.write("\r✅ ⏳ Background server started!       \n\n")
        out.write("🌐 Your browser will open soon to: http://127.0.0.1:5000\n")
        out.write("💻 The application will run entirely in your browser.\n\n")
        out.write("🛑 To STOP the server, press Ctrl+C\n")
        out.flush()

        try:
            time.sleep(0.5)  # Slight buffer for stability
            webbrowser.open("http://127.0.0.1:5000", new=0, autoraise=True)
        except Exception:
            pass


# =====================================================================
# IMMEDIATE SPINNER POLLING THREAD
# Starts right away to mask the import delay of Flask & SQLAlchemy
# =====================================================================
if is_portable:
    import threading

    # Note: daemon=True means this thread exits automatically if server fails
    threading.Thread(target=_portable_startup_sequence, daemon=True).start()

# =============================================================================
# Add the directory containing run.py to sys.path
# This makes "from src.app import ..." work reliably in BOTH:
#   - Normal development (your IDE)
#   - Portable distribution (embedded Python)
# =============================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Configure UTF-8 encoding for stdout/stderr to handle emojis on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


def check_setup():
    """Verify that the environment is correctly set up."""
    if os.environ.get("CI") or os.environ.get("E2E_TEST") or is_portable:
        return

    if not os.path.exists(".venv"):
        if getattr(sys, "stdout", None) and sys.stdout != sys.__stdout__:
            pass  # can't print if stdout is redirected
        else:
            print("\nERROR: Setup incomplete!")
            print("Please run the setup script first:")
            print("    .\\scripts\\setup.ps1")
            print("\nThe application cannot start without proper setup.\n")
        sys.exit(1)


check_setup()

from dotenv import load_dotenv  # noqa: E402

from src.app import create_app  # noqa: E402

load_dotenv()

_app = None


def get_app():
    """Get or create the Flask application instance."""
    global _app
    if _app is None:
        debug = True
        if (
            is_portable
            or os.getenv("FLASK_ENV") == "production"
            or os.getenv("FLASK_DEBUG") in ("0", "false", "False")
        ):
            debug = False
        _app = create_app(config_overrides={"DEBUG": debug})

        # Disable logging to console in portable mode just to be safe
        if is_portable:
            import logging

            logging.getLogger().setLevel(logging.ERROR)
            for logger_name in ["src.app", "src", "werkzeug", "flask", "sqlalchemy"]:
                logging.getLogger(logger_name).setLevel(logging.ERROR)

    return _app


if os.environ.get("TESTING") != "1":
    app = get_app()
else:
    app = None

if __name__ == "__main__":
    app = get_app()
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    is_e2e_test = os.getenv("E2E_TEST", "").lower() in ("true", "1", "yes")

    if not is_portable:
        if is_e2e_test:
            print(f"🧪 Starting mockCMMS in E2E TEST mode on port {port}...")
        else:
            print(f"Starting mockCMMS application on port {port}...")

    use_reloader = not is_e2e_test and not is_portable
    debug_mode = app.config.get("DEBUG", False)

    app.run(
        host="127.0.0.1",
        debug=debug_mode,
        port=port,
        use_reloader=use_reloader,
        threaded=True,
    )
