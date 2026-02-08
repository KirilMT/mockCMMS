# src/app.py
"""Flask application factory for mockCMMS."""

import os
import sqlite3
from datetime import datetime, timedelta, timezone

import click
from dotenv import load_dotenv
from flask import Flask, flash, g, jsonify, redirect, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect  # type: ignore[import-untyped]
from sqlalchemy.pool import NullPool

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


def get_env_bool(name, default="true"):
    """Get boolean value from environment variable."""
    return os.getenv(name, default).lower() in ("true", "1", "t", "yes")


def create_app(config_overrides=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    # Check if running in E2E test mode
    is_e2e = get_env_bool("E2E_TEST", "false")
    if is_e2e:
        print(f"Ÿ E2E Mode Detected. E2E_TEST={is_e2e}")
        # Use NullPool to prevent file locking issues with SQLite on Windows
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev_key_fallback_for_testing"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=get_env_bool("TESTING", "false"),
        AUTO_SEED_DATABASE=get_env_bool("AUTO_SEED_DATABASE", "true"),
        # Disable rate limiting for E2E tests to prevent timeouts/failures
        RATELIMIT_ENABLED=not is_e2e,
        RATELIMIT_STORAGE_URI="memory://",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    )

    # Determine (and verify) if we are in testing mode early.
    if config_overrides and "TESTING" in config_overrides:
        app.config["TESTING"] = bool(config_overrides["TESTING"])

    if not app.testing:
        load_dotenv(os.path.join(app.root_path, "..", ".env"))

    # Apply overrides EARLY so we can check what's configured
    if config_overrides:
        app.config.from_mapping(config_overrides)

    # Set default SQLALCHEMY_DATABASE_URI only if not already set (by overrides)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        if (
            app.testing
            and not get_env_bool("TESTING_PRODUCTION", "false")
            and not is_e2e
        ):
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        elif get_env_bool("TESTING_PRODUCTION", "false"):
            db_name = "mockcmms_test.db"
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{os.path.join(app.instance_path, db_name)}"
            )
        elif is_e2e:
            db_name = "mockcmms_e2e.db"
            db_path = os.path.join(app.instance_path, db_name)
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
            # Ensure the directory exists
            os.makedirs(app.instance_path, exist_ok=True)
            print(f"🧪 E2E Database Path: {db_path}")
        else:
            # Production/Development default
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{os.path.join(app.instance_path, 'mockcmms.db')}"
            )

    # Configure Binds for Modular Apps
    binds = app.config.get("SQLALCHEMY_BINDS", {}).copy()

    planning_enabled = get_env_bool("PLANNING_ENABLED", "true")

    # Planning module database path - MONOREPO: apps/planning/instance/
    planning_instance_dir = os.path.join(
        app.root_path, "..", "apps", "planning", "instance"
    )

    if planning_enabled or app.testing:
        if "planning" not in binds:
            # Priority 1: DATABASE_PATH in config (used by some tests)
            if "DATABASE_PATH" in app.config and app.testing:
                planning_db_path = app.config["DATABASE_PATH"]
                binds["planning"] = f"sqlite:///{planning_db_path}"
            # Priority 2: Standard Testing (In-Memory)
            elif app.testing and not is_e2e:
                binds["planning"] = "sqlite:///:memory:"
            # Priority 3: E2E Testing (File-based isolation)
            elif is_e2e:
                # Ensure the planning instance directory exists for E2E
                os.makedirs(planning_instance_dir, exist_ok=True)
                planning_db_path = os.path.join(
                    planning_instance_dir, "planning_e2e.db"
                )
                binds["planning"] = f"sqlite:///{planning_db_path}"
                # Ensure legacy code finds the correct DB
                app.config["DATABASE_PATH"] = planning_db_path
            else:
                # Priority 4: Production/Development Standard
                planning_db_path = os.path.join(planning_instance_dir, "planning.db")
                binds["planning"] = f"sqlite:///{planning_db_path}"
                # Ensure legacy code finds the correct DB
                app.config["DATABASE_PATH"] = planning_db_path

    reports_enabled = get_env_bool("REPORTS_ENABLED", "false")

    # Reports module database path - MONOREPO: apps/reports/instance/
    reports_instance_dir = os.path.join(
        app.root_path, "..", "apps", "reports", "instance"
    )

    if reports_enabled or app.testing:
        if "reports" not in binds:
            if app.testing and not is_e2e:
                binds["reports"] = "sqlite:///:memory:"
            elif is_e2e:
                # Ensure the reports instance directory exists for E2E
                os.makedirs(reports_instance_dir, exist_ok=True)
                reports_db_path = os.path.join(reports_instance_dir, "reports_e2e.db")
                binds["reports"] = f"sqlite:///{reports_db_path}"
            else:
                reports_db_path = os.path.join(reports_instance_dir, "reports.db")
                binds["reports"] = f"sqlite:///{reports_db_path}"

    app.config["SQLALCHEMY_BINDS"] = binds

    # Initialize extensions
    db.init_app(app)

    # --- Logging ---
    try:
        LoggingConfig.setup_logging(app)
    except OSError as e:
        # Fallback if log directory cannot be created
        app.logger.error("Failed to setup logging directory: %s", e)

    # Disable verbose Werkzeug request logs (GET /static/...) during E2E tests
    # This unclutters the test output so failures are easier to see.
    if is_e2e:
        import logging

        logging.getLogger("werkzeug").setLevel(logging.ERROR)

    if is_e2e:
        app.config["WTF_CSRF_ENABLED"] = False
    csrf = CSRFProtect(app)

    test_limit = app.config.get("RATELIMIT_TEST_LIMIT", "5 per minute")
    if is_e2e:
        default_limits = ["100000 per day", "10000 per hour"]
    else:
        app_testing = app.config["TESTING"]
        default_limits = [test_limit] if app_testing else ["200 per day", "50 per hour"]

    Limiter(
        get_remote_address,
        app=app,
        default_limits=default_limits,
        storage_uri="memory://",
    )

    _register_blueprints(app, csrf)

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    is_memory = db_uri and ":memory:" in str(db_uri)

    if not is_memory:
        try:
            if "sqlite:///" in str(db_uri):
                target_dir = os.path.dirname(str(db_uri).replace("sqlite:///", ""))
                if target_dir:
                    os.makedirs(target_dir, exist_ok=True)
            else:
                os.makedirs(app.instance_path, exist_ok=True)
        except OSError as e:
            app.logger.error("Failed to create instance folder: %s", e)

    # Init DB tables if enabled
    # E2E NOTE: We must ensure tables exist before requests come in.
    # The run.py starts the server, creating the app.
    # For E2E tests, we ALWAYS initialize DB unconditionally

    # Restored logic: Verify if we should init DB. Defaults to True for this mock app.
    should_init_db = app.config.get("DB_INITIALIZED", True) or is_e2e

    # CRITICAL: For E2E tests, ALWAYS initialize DB - no conditions
    if is_e2e:
        should_init_db = True

    app_ctx = app.app_context()
    app_ctx.__enter__()
    try:
        if should_init_db:
            if is_e2e:
                print("🧪 Initializing E2E Database Schema...")

            # Import models to ensure they are registered with SQLAlchemy
            # This is critical for fresh DB creation

            # Create all tables for ALL binds (main db + planning + reports)
            db.create_all()
            # Also create tables for each bind explicitly
            for bind_key in app.config.get("SQLALCHEMY_BINDS", {}).keys():
                db.create_all(bind_key=bind_key)
            app.logger.info("Database tables created successfully.")

            if is_e2e:
                # Verify User table existence
                try:
                    with db.engine.connect() as conn:
                        from sqlalchemy import text

                        result = conn.execute(
                            text(
                                "SELECT name FROM sqlite_master "
                                "WHERE type='table' AND name='user'"
                            )
                        )
                        if result.fetchone():
                            print("✅ User table verified.")
                        else:
                            print("❌ User table MISSING after create_all()!")
                except Exception as e:
                    print(f"⚠️ Verification check failed: {e}")

        should_seed = app.config.get("AUTO_SEED_DATABASE", True) and should_init_db
        if should_seed:
            try:
                # In E2E mode, we must ensure data exists immediately
                if is_e2e or get_env_bool("AUTO_SEED_DATABASE", "true"):
                    populate_dummy_data(app.logger)
                    app.logger.info("Dummy data populated successfully.")
            except Exception as e:
                app.logger.error("Database seeding failed: %s", e)

            if get_env_bool("PLANNING_ENABLED", "true"):
                try:
                    from apps.planning.src.services.planning_db_utils import init_db

                    planning_db_path = app.config.get("DATABASE_PATH")
                    # Init file-based DBs in non-testing mode OR E2E mode
                    # E2E mode uses file-based DBs for isolation
                    should_init_planning_db = (
                        planning_db_path
                        and ":memory:" not in str(planning_db_path)
                        and (not app.testing or is_e2e)
                    )
                    if should_init_planning_db:
                        db_dir = os.path.dirname(planning_db_path)
                        if db_dir and not os.path.exists(db_dir):
                            os.makedirs(db_dir, exist_ok=True)
                        init_db(
                            planning_db_path,
                            app.logger,
                            debug_use_test_db=app.config.get(
                                "AUTO_SEED_DATABASE", True
                            ),
                        )
                    from apps.planning.src.services.seeding import seed_planning_data

                    seed_planning_data(app.logger)
                except Exception as e:
                    app.logger.error("Planning App seeding failed: %s", e)

            if get_env_bool("REPORTS_ENABLED", "false"):
                try:
                    from apps.reports.src.services.seeding import seed_reports_data

                    seed_reports_data(app.logger)
                except Exception as e:
                    app.logger.error("Reports App seeding failed: %s", e)
    finally:
        app_ctx.__exit__(None, None, None)

    _register_request_handlers(app)
    _register_context_processors(app)
    _register_commands(app)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify(error="Rate limit exceeded", message=str(e.description)), 429

    return app


def _register_commands(app):
    @app.cli.command("simulate-data")
    @click.option("--count", default=10, help="Number of items per type.")
    @click.option(
        "--type",
        type=click.Choice(["all", "assets", "technicians", "orders"]),
        default="all",
    )
    def simulate_data_command(count, type):
        app.logger.info(f"Simulation: generating {count} items of type {type}")
        if type in ["all", "assets"]:
            assets = DataSimulationService.generate_random_assets(count)
            print(f"Generated {len(assets)} assets.")
        if type in ["all", "technicians"]:
            techs = DataSimulationService.generate_random_users(count)
            print(f"Generated {len(techs)} technicians.")
        if type in ["all", "orders"]:
            orders = DataSimulationService.generate_random_orders(count)
            print(f"Generated {len(orders)} maintenance orders.")


def _register_blueprints(app, csrf):
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(main_bp)
    from .routes.simulation import simulation_bp

    app.register_blueprint(simulation_bp)

    if get_env_bool("REPORTS_ENABLED", "false"):
        try:
            from apps.reports.src.routes.reports import reports_bp

            app.register_blueprint(reports_bp)
            csrf.exempt(reports_bp)
            app.logger.info("Reports Blueprint registered.")
            # Only create directories for NON-testing and NON-memory databases
            if not app.testing:
                reports_binds = app.config.get("SQLALCHEMY_BINDS", {})
                reports_db_uri = reports_binds.get("reports", "")
                if reports_db_uri and ":memory:" not in str(reports_db_uri):
                    try:
                        if "sqlite:///" in str(reports_db_uri):
                            r_path = os.path.dirname(
                                str(reports_db_uri).replace("sqlite:///", "")
                            )
                        else:
                            r_path = os.path.join(
                                app.root_path, "..", "apps", "reports", "instance"
                            )
                        if r_path:
                            os.makedirs(r_path, exist_ok=True)
                    except OSError as e:
                        app.logger.error("Failed to create Reports directory: %s", e)
        except ImportError as e:
            app.logger.error("Reports module not available: %s", e)

    if get_env_bool("PLANNING_ENABLED", "true"):
        try:
            from apps.planning.src.routes.planning import planning_bp

            app.register_blueprint(planning_bp)
            csrf.exempt(planning_bp)
            app.logger.info("Planning Blueprint registered.")
            # Only create directories for NON-testing and NON-memory databases
            if not app.testing:
                planning_binds = app.config.get("SQLALCHEMY_BINDS", {})
                planning_db_uri = planning_binds.get("planning", "")
                if planning_db_uri and ":memory:" not in str(planning_db_uri):
                    try:
                        if "sqlite:///" in str(planning_db_uri):
                            p_path = os.path.dirname(
                                str(planning_db_uri).replace("sqlite:///", "")
                            )
                        else:
                            p_path = os.path.join(
                                app.root_path, "..", "apps", "planning", "instance"
                            )
                        if p_path:
                            os.makedirs(p_path, exist_ok=True)
                    except OSError as e:
                        app.logger.error("Failed to create Planning directory: %s", e)
        except Exception as e:
            app.logger.error("Planning App not available: %s", e)


def close_db(_exception=None):
    """Gracefully close the database connection."""
    db_conn = g.pop("db", None)
    if db_conn is not None:
        db_conn.close()


def _register_request_handlers(app):
    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        if user_id:
            # Session Timeout Logic
            last_active_ts = session.get("last_active")
            now_ts = datetime.now(timezone.utc).timestamp()

            if last_active_ts is None:
                # Force logout if no timestamp found (migrating old sessions)
                session.clear()
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
            g.user = db.session.get(User, user_id)
        else:
            g.user = None

    @app.before_request
    def redirect_legacy_urls():
        if request.path.startswith("/planning-manager"):
            new_path = request.full_path.replace("/planning-manager", "/planning", 1)
            return redirect(new_path, code=301)
        return None

    planning_val = os.getenv("PLANNING_ENABLED", "True")
    if planning_val.lower() in ("true", "1", "t") or app.testing:

        @app.before_request
        def before_planning_request():
            if request.path.startswith("/planning"):
                # Avoid opening manual SQLite connection if SQLAlchemy is sufficient.
                # Only use g.db if strictly necessary for legacy code not using ORM.
                try:
                    binds = app.config.get("SQLALCHEMY_BINDS", {})
                    planning_uri = binds.get("planning", "")

                    # If we use SQLAlchemy, we might not need this manual connection
                    # anymore.
                    # But if legacy code relies on g.db, we must ensure it doesn't
                    # conflict.

                    db_path = app.config.get("DATABASE_PATH")
                    if ":memory:" in str(planning_uri):
                        return None
                    if not db_path:
                        if planning_uri and "sqlite:///" in str(planning_uri):
                            db_path = str(planning_uri).replace("sqlite:///", "")
                        else:
                            db_name = (
                                "planning_test.db" if app.testing else "planning.db"
                            )
                            db_path = os.path.join(
                                app.root_path,
                                "..",
                                "apps",
                                "planning",
                                "instance",
                                db_name,
                            )
                    if db_path and ":memory:" not in str(db_path):
                        if not os.path.exists(os.path.dirname(db_path)):
                            if not app.testing:
                                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                        if os.path.exists(os.path.dirname(db_path)):
                            # Use check_same_thread=False since the
                            # reloader/threaded=True might be used.
                            # However, better is to avoid this if possible.
                            g.db = sqlite3.connect(
                                db_path, timeout=30, check_same_thread=False
                            )
                except sqlite3.Error as e:
                    app.logger.error(f"Failed to connect to planning database: {e}")
                    return jsonify({"error": "Database connection failed"}), 503
            return None

    app.teardown_request(close_db)

    @app.after_request
    def add_security_headers(response):
        response.headers["Permissions-Policy"] = "unload=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


def _register_context_processors(app):
    @app.context_processor
    def inject_config():
        return {
            "PLANNING_ENABLED": get_env_bool("PLANNING_ENABLED", "true"),
            "REPORTS_ENABLED": get_env_bool("REPORTS_ENABLED", "false"),
        }
