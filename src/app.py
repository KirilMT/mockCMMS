# src/app.py
"""Flask application factory for mockCMMS."""

import os
import sqlite3
import traceback
from datetime import datetime, timedelta, timezone

import click
from dotenv import load_dotenv
from flask import Flask, flash, g, jsonify, redirect, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect  # type: ignore[import-untyped]

# Local blueprint imports
from .routes.api import api_bp
from .routes.main import main_bp
from .services.db_seeding import populate_dummy_data
from .services.db_utils import User, db
from .services.logging_config import LoggingConfig
from .services.simulation_service import DataSimulationService

# NOTE: Modular app imports (reports, planning) MUST stay inside conditional
# blocks because importing their models registers them with SQLAlchemy, causing
# UnboundExecutionError when the module is disabled. C0415 is acceptable here.


def create_app(config_overrides=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    # Check if running in E2E test mode
    is_e2e = os.environ.get("E2E_TEST", "False").lower() in ("true", "1", "t")

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev_key_fallback_for_testing"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=os.environ.get("TESTING", "0") == "1",
        AUTO_SEED_DATABASE=os.getenv("AUTO_SEED_DATABASE", "True").lower()
        in ("true", "1", "t"),
        # Disable rate limiting for E2E tests to prevent timeouts/failures
        RATELIMIT_ENABLED=not is_e2e,
        RATELIMIT_STORAGE_URI="memory://",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    )

    if not app.testing:
        load_dotenv(os.path.join(app.root_path, "..", ".env"))

    db_name = (
        "mockcmms_test.db" if os.environ.get("TESTING_PRODUCTION") else "mockcmms.db"
    )
    # E2E tests use dedicated database for isolation and consistent seeding
    if os.environ.get("E2E_TEST"):
        db_name = "mockcmms_e2e.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(app.instance_path, db_name)}"
    )

    # Configure Binds for Modular Apps (conditional to prevent db.create_all errors)
    binds = {}
    if os.getenv("PLANNING_ENABLED", "False").lower() in ("true", "1", "t"):
        planning_db_path = os.path.join(
            app.root_path, "..", "apps", "planning", "instance", "planning.db"
        )
        binds["planning"] = f"sqlite:///{planning_db_path}"
    app.config["SQLALCHEMY_BINDS"] = binds

    if config_overrides:
        app.config.from_mapping(config_overrides)

    # --- Initializations ---
    # Setup Logging
    LoggingConfig.setup_logging(app)

    db.init_app(app)
    csrf = CSRFProtect(app)

    # Setup Rate Limiting
    # Use stricter limits for testing to verify rate limiting works
    # But allow enough for performance tests via configuration
    test_limit = app.config.get("RATELIMIT_TEST_LIMIT", "5 per minute")

    if is_e2e:
        # Extremely high limits for E2E tests to ensure no blocking
        default_limits = ["100000 per day", "10000 per hour"]
    else:
        default_limits = (
            [test_limit] if app.config["TESTING"] else ["200 per day", "50 per hour"]
        )

    Limiter(
        get_remote_address,
        app=app,
        default_limits=default_limits,
        storage_uri="memory://",
    )

    # --- Blueprints ---
    _register_blueprints(app, csrf)

    # --- Instance Folder & Database Setup ---
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        app.logger.error("Failed to create instance folder.")

    with app.app_context():
        db.create_all()
        if app.config.get("AUTO_SEED_DATABASE", True):
            populate_dummy_data(app.logger)

            # Seed Planning App Data (AFTER core tables and data are created)
            planning_enabled = os.getenv("PLANNING_ENABLED", "False").lower() in (
                "true",
                "1",
                "t",
            )
            if planning_enabled:
                try:
                    # pylint: disable=import-outside-toplevel
                    from apps.planning.src.services.seeding import seed_planning_data

                    seed_planning_data(app.logger)
                except ImportError as e:
                    app.logger.error("Planning App seeding failed (import): %s", e)
                except Exception as e:  # pylint: disable=broad-except
                    app.logger.error("Planning App seeding failed: %s", e)

    # --- Request Hooks & Context Processors ---
    _register_request_handlers(app)
    _register_context_processors(app)
    _register_commands(app)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify(error="Rate limit exceeded", message=str(e.description)), 429

    return app


def _register_commands(app):
    """Register custom CLI commands."""

    @app.cli.command("simulate-data")
    @click.option("--count", default=10, help="Number of items to generate per type.")
    @click.option(
        "--type",
        type=click.Choice(["all", "assets", "technicians", "orders"]),
        default="all",
        help="Type of data to generate.",
    )
    def simulate_data_command(count, type):
        """Generate realistic mock data for stress testing."""
        app.logger.info(f"Starting simulation: generating {count} items of type {type}")

        if type in ["all", "assets"]:
            assets = DataSimulationService.generate_random_assets(count)
            print(f"Generated {len(assets)} assets.")

        if type in ["all", "technicians"]:
            techs = DataSimulationService.generate_random_users(count)
            print(f"Generated {len(techs)} technicians.")

        if type in ["all", "orders"]:
            orders = DataSimulationService.generate_random_orders(count)
            print(f"Generated {len(orders)} maintenance orders.")

        print("Data simulation complete.")


def _register_blueprints(app, csrf):
    """Register all application blueprints."""
    # Core blueprints (always available)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(main_bp)

    # Simulation Blueprint
    from .routes.simulation import simulation_bp

    app.register_blueprint(simulation_bp)

    # Conditionally register modular apps
    reports_enabled = os.getenv("REPORTS_ENABLED", "False").lower() in (
        "true",
        "1",
        "t",
    )
    if reports_enabled:
        try:
            # pylint: disable=import-outside-toplevel
            from apps.reports.src.routes.reports import reports_bp

            app.register_blueprint(reports_bp)
            csrf.exempt(reports_bp)
            app.logger.info("Reports Blueprint registered.")
        except ImportError as e:
            app.logger.error("Reports enabled but module not available: %s", e)
    else:
        app.logger.info("Reports module is disabled.")

    planning_enabled = os.getenv("PLANNING_ENABLED", "False").lower() in (
        "true",
        "1",
        "t",
    )
    if planning_enabled:
        try:
            # pylint: disable=import-outside-toplevel
            from apps.planning.src.routes.planning import planning_bp

            app.register_blueprint(planning_bp)
            csrf.exempt(planning_bp)
            app.logger.info("Planning Blueprint registered.")

            # Ensure Planning App Instance Directory Exists
            try:
                planning_instance_path = os.path.join(
                    app.root_path, "..", "apps", "planning", "instance"
                )
                os.makedirs(planning_instance_path, exist_ok=True)
            except OSError as e:
                app.logger.error(
                    "Failed to create Planning App instance directory: %s", e
                )
        except ImportError as e:
            app.logger.error(
                "Planning enabled but module not available: %s\n%s",
                e,
                traceback.format_exc(),
            )
    else:
        app.logger.info("Planning module is disabled.")


def _register_request_handlers(app):
    """Register before_request, after_request, and teardown_appcontext handlers."""

    @app.before_request
    def load_logged_in_user():
        """If a user id is in the session, load the user object from the database into
        g.user."""
        user_id = session.get("user_id")

        if user_id:
            # Session Timeout Logic
            last_active_ts = session.get("last_active")
            now_ts = datetime.now(timezone.utc).timestamp()

            if last_active_ts is None:
                # Force logout if no timestamp found (migrating old sessions)
                session.clear()
                # We can't use flash/redirect easily in before_request if we want to just clear user?
                # If we just clear the session, the main.login check will redirect them.
                # However, to provide feedback, we can flash.
                # But if we redirect here, we might interrupt the request.
                # Since this is a security measure, interrupting is fine.
                flash("Session invalid. Please log in again.", "warning")
                return redirect(url_for("main.login"))

            # 30 minutes in seconds = 1800 (default)
            timeout_seconds = 1800
            lifetime = app.config.get("PERMANENT_SESSION_LIFETIME")
            if isinstance(lifetime, timedelta):
                timeout_seconds = lifetime.total_seconds()

            if (now_ts - last_active_ts) > timeout_seconds:
                session.clear()
                flash("Session expired due to inactivity.", "info")
                return redirect(url_for("main.login"))

            session["last_active"] = now_ts
            g.user = User.query.get(user_id)
        else:
            g.user = None

    @app.before_request
    def redirect_legacy_urls():
        if request.path.startswith("/planning-manager"):
            new_path = request.full_path.replace("/planning-manager", "/planning", 1)
            return redirect(new_path, code=301)
        return None

    if os.getenv("PLANNING_ENABLED", "False").lower() in ("true", "1", "t"):

        @app.before_request
        def before_planning_request():
            if request.path.startswith("/planning"):
                try:
                    db_path = os.path.join(
                        app.root_path,
                        "..",
                        "apps",
                        "planning",
                        "instance",
                        "planning.db",
                    )
                    # No need to manually connect if using SQLAlchemy Binds,
                    # but keeping for legacy raw SQL access if needed.
                    g.db = sqlite3.connect(db_path)
                    g.db.row_factory = sqlite3.Row
                except sqlite3.Error as e:
                    app.logger.error(f"Failed to connect to planning database: {e}")
                    return jsonify({"error": "Database connection failed"}), 503
            return None

    @app.teardown_appcontext
    def close_db(_exception=None):
        db_conn = g.pop("db", None)
        if db_conn is not None:
            db_conn.close()

    @app.after_request
    def add_security_headers(response):
        response.headers["Permissions-Policy"] = "unload=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # CORS Headers (Basic implementation)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        # Prevent caching to ensure E2E tests see up-to-date data
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


def _register_context_processors(app):
    """Register context processors to inject variables into templates."""

    @app.context_processor
    def inject_config():
        return {
            "PLANNING_ENABLED": os.getenv("PLANNING_ENABLED", "False").lower()
            in ("true", "1", "t"),
            "REPORTS_ENABLED": os.getenv("REPORTS_ENABLED", "False").lower()
            in ("true", "1", "t"),
        }
