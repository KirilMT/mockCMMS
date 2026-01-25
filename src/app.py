# src/app.py
"""Flask application factory for mockCMMS."""

import os
import sqlite3

import click
from dotenv import load_dotenv
from flask import Flask, g, jsonify, redirect, request, session
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
            and not os.environ.get("TESTING_PRODUCTION")
            and not os.environ.get("E2E_TEST")
        ):
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        elif os.environ.get("TESTING_PRODUCTION"):
            db_name = "mockcmms_test.db"
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{os.path.join(app.instance_path, db_name)}"
            )
        elif os.environ.get("E2E_TEST"):
            db_name = "mockcmms_e2e.db"
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{os.path.join(app.instance_path, db_name)}"
            )
        else:
            # Production/Development default
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{os.path.join(app.instance_path, 'mockcmms.db')}"
            )

    # Configure Binds for Modular Apps
    binds = app.config.get("SQLALCHEMY_BINDS", {}).copy()

    planning_enabled = os.getenv("PLANNING_ENABLED", "False").lower() in (
        "true",
        "1",
        "t",
    )

    if planning_enabled or app.testing:
        if "planning" not in binds:
            if "DATABASE_PATH" in app.config and app.testing:
                planning_db_path = app.config["DATABASE_PATH"]
                binds["planning"] = f"sqlite:///{planning_db_path}"
            elif app.testing and not os.environ.get("E2E_TEST"):
                binds["planning"] = "sqlite:///:memory:"
            else:
                planning_db_name = "planning.db"
                if os.environ.get("E2E_TEST"):
                    planning_db_name = "planning_e2e.db"

                planning_db_path = os.path.join(
                    app.root_path,
                    "..",
                    "apps",
                    "planning",
                    "instance",
                    planning_db_name,
                )
                app.config["DATABASE_PATH"] = planning_db_path
                binds["planning"] = f"sqlite:///{planning_db_path}"

    reports_enabled = os.getenv("REPORTS_ENABLED", "False").lower() in (
        "true",
        "1",
        "t",
    )
    if reports_enabled or app.testing:
        if "reports" not in binds:
            if app.testing and not os.environ.get("E2E_TEST"):
                binds["reports"] = "sqlite:///:memory:"
            else:
                reports_db_name = "reports.db"
                if os.environ.get("E2E_TEST"):
                    reports_db_name = "reports_e2e.db"

                reports_db_path = os.path.join(
                    app.root_path,
                    "..",
                    "apps",
                    "reports",
                    "instance",
                    reports_db_name,
                )
                app.config["REPORTS_DATABASE_PATH"] = reports_db_path
                binds["reports"] = f"sqlite:///{reports_db_path}"

    app.config["SQLALCHEMY_BINDS"] = binds

    # Setup Logging
    LoggingConfig.setup_logging(app)
    db.init_app(app)

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

    # Bypass mangling of "with" keyword using explicit context management
    app_ctx = app.app_context()
    app_ctx.__enter__()
    try:
        db.create_all()
        if app.config.get("AUTO_SEED_DATABASE", True):
            try:
                populate_dummy_data(app.logger)
            except Exception as e:
                app.logger.error("Database seeding failed: %s", e)

            planning_val = os.getenv("PLANNING_ENABLED", "False")
            if planning_val.lower() in ("true", "1", "t"):
                try:
                    from apps.planning.src.services.planning_db_utils import init_db

                    planning_db_path = app.config.get("DATABASE_PATH")
                    if planning_db_path and ":memory:" not in str(planning_db_path):
                        db_dir = os.path.dirname(planning_db_path)
                        if not os.path.exists(db_dir):
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

            reports_val = os.getenv("REPORTS_ENABLED", "False")
            if reports_val.lower() in ("true", "1", "t"):
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

    reports_val = os.getenv("REPORTS_ENABLED", "False")
    if reports_val.lower() in ("true", "1", "t"):
        try:
            from apps.reports.src.routes.reports import reports_bp

            app.register_blueprint(reports_bp)
            csrf.exempt(reports_bp)
            app.logger.info("Reports Blueprint registered.")
            reports_binds = app.config.get("SQLALCHEMY_BINDS", {})
            reports_db_uri = reports_binds.get("reports", "")
            if not app.testing or (
                reports_db_uri and ":memory:" not in str(reports_db_uri)
            ):
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

    planning_val = os.getenv("PLANNING_ENABLED", "False")
    if planning_val.lower() in ("true", "1", "t"):
        try:
            from apps.planning.src.routes.planning import planning_bp

            app.register_blueprint(planning_bp)
            csrf.exempt(planning_bp)
            app.logger.info("Planning Blueprint registered.")
            planning_binds = app.config.get("SQLALCHEMY_BINDS", {})
            planning_db_uri = planning_binds.get("planning", "")
            if not app.testing or (
                planning_db_uri and ":memory:" not in str(planning_db_uri)
            ):
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


def _register_request_handlers(app):
    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id is not None else None

    @app.before_request
    def redirect_legacy_urls():
        if request.path.startswith("/planning-manager"):
            new_path = request.full_path.replace("/planning-manager", "/planning", 1)
            return redirect(new_path, code=301)
        return None

    planning_val = os.getenv("PLANNING_ENABLED", "False")
    if planning_val.lower() in ("true", "1", "t") or app.testing:

        @app.before_request
        def before_planning_request():
            if request.path.startswith("/planning"):
                try:
                    binds = app.config.get("SQLALCHEMY_BINDS", {})
                    planning_uri = binds.get("planning", "")
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
                            g.db = sqlite3.connect(db_path, timeout=30)
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
        p_enabled = os.getenv("PLANNING_ENABLED", "False").lower() in ("true", "1", "t")
        r_enabled = os.getenv("REPORTS_ENABLED", "False").lower() in ("true", "1", "t")
        return {
            "PLANNING_ENABLED": p_enabled,
            "REPORTS_ENABLED": r_enabled,
        }
