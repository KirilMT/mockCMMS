import os
import sys

from flask import Flask, current_app, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# Add project root to sys.path to allow importing config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.planning.src.config import Config  # noqa: E402
from apps.planning.src.extensions import db_manager  # noqa: E402

# Import the consolidated Blueprint
from apps.planning.src.routes.planning import planning_bp  # noqa: E402
from apps.planning.src.services.logging_config import LoggingConfig  # noqa: E402

# Import from local services package
from apps.planning.src.services.security import SecurityMiddleware  # noqa: E402
from apps.planning.src.template_filters import register_template_filters  # noqa: E402
from src.services.db_utils import db  # noqa: E402


def not_found(error):
    from flask import request

    current_app.logger.warning(
        f"404 Not Found: The requested URL '{request.path}' "
        "was not found on the server."
    )
    return f"Page not found: {request.path}", 404


def handle_400_error(error):
    response = jsonify({"message": "Bad request", "details": str(error)})
    response.status_code = 400
    return response


def handle_500_error(error):
    response = jsonify({"message": "Internal server error", "details": str(error)})
    response.status_code = 500
    return response


def create_app(config_overrides=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    if config_overrides:
        app.config.from_mapping(config_overrides)

    # Ensure TESTING is set if passed in overrides
    if app.config.get("TESTING"):
        os.environ["TESTING"] = "1"

    # Validate configuration before proceeding
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        raise

    # Setup logging first
    logger = LoggingConfig.setup_logging(app)
    app.logger = logger

    # Initialize security extensions
    csrf = CSRFProtect(app)

    Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )

    db.init_app(app)
    db_manager.init_app(app)

    with app.app_context():
        db.create_all()

    # Use DATABASE_PATH from config if needed, or rely on db_manager
    # DATABASE_PATH = app.config["DATABASE_PATH"]

    # Register template filters
    register_template_filters(app)

    # Register the consolidated Blueprint
    app.register_blueprint(planning_bp)

    # Configure CSRF exemptions after blueprint registration
    # The entire blueprint is exempted as it handles its
    # own internal CSRF logic if needed.
    csrf.exempt(planning_bp)

    # Security middleware
    @app.after_request
    def after_request(response):
        return SecurityMiddleware.add_security_headers(response)

    app.register_error_handler(404, not_found)
    app.register_error_handler(400, handle_400_error)
    app.register_error_handler(500, handle_500_error)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)  # nosec B201
