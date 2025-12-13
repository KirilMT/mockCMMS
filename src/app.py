"""Flask application factory for mockCMMS."""
import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Correctly indented imports
from .services.db_utils import db


def create_app(config=None):
    """Create and configure the Flask application.
    
    Args:
        config: Optional configuration object to override defaults
    """
    app = Flask(__name__)
    
    # Check if running in test mode FIRST (before any file operations)
    is_testing = os.environ.get('TESTING', '0') == '1'
    app.config['TESTING'] = is_testing

    # Load environment variables from .env file (skip in testing)
    if not is_testing:
        load_dotenv(dotenv_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '.env'))

    # Set debug flag for test database
    app.config['DEBUG_USE_TEST_DB'] = os.getenv(
        'MOCKCMMS_DEBUG_USE_TEST_DB', '0').lower() in (
        '1', 'true', 'yes')

    # Configure the database (use in-memory for testing, separate file for test production mode)
    if is_testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        # Check if running production tests (TESTING_PRODUCTION flag)
        if os.environ.get('TESTING_PRODUCTION', '0') == '1':
            db_name = 'mockcmms_test.db'
        else:
            db_name = 'mockcmms.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', db_name)
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv('SECRET_KEY', 'dev_key_fallback_do_not_use_in_prod')
    
    # Apply custom config if provided (for testing)
    if config:
        app.config.from_object(config)

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Initialize CSRF protection to make csrf_token() available in templates
    csrf = CSRFProtect(app)

    # Ensure the instance folder exists (skip in testing mode)
    if not is_testing:
        instance_path = os.path.join(app.root_path, '..', 'instance')
        os.makedirs(instance_path, exist_ok=True)

    # Register mockCMMS blueprints
    from .routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    # Conditionally register the reports app
    if os.getenv('REPORTS_ENABLED', 'False').lower() in ('true', '1', 't'):
        try:
            # Ensure database is initialized before importing reports blueprint
            with app.app_context():
                from apps.reports.src.routes.reports import reports_bp
                app.register_blueprint(reports_bp)
                csrf.exempt(reports_bp)
                if app.logger:
                    app.logger.info("Reports Blueprint registered at /reports")
        except Exception as e:
            if app.logger:
                app.logger.error("Failed to register Reports blueprint: %s", e)
    else:
        if app.logger:
            app.logger.info("Reports Blueprint not enabled.")

    # Conditionally register the planning_bp from the planning package
    if os.getenv('PLANNING_ENABLED', 'False').lower() in ('true', '1', 't'):
        try:
            # Import the blueprint from the planning package (installed in editable mode)
            from apps.planning.src.routes.planning import planning_bp
            app.register_blueprint(planning_bp)
            csrf.exempt(planning_bp)

            # Register the same blueprint again with /api prefix
            app.register_blueprint(planning_bp, url_prefix='/api', name='planning_api')

            if app.logger:
                app.logger.info("Planning Blueprint registered at /planning and /api")
        except Exception as e:
            if app.logger:
                import traceback
                app.logger.error("Failed to register Planning blueprint: %s", e)
                app.logger.error(traceback.format_exc())
    else:
        if app.logger:
            app.logger.info("Planning Blueprint not enabled.")

    @app.before_request
    def redirect_legacy_urls():
        """Redirect legacy /planning-manager URLs to /planning."""
        from flask import request, redirect
        if request.path.startswith('/planning-manager'):
            new_path = request.full_path.replace('/planning-manager', '/planning', 1)
            return redirect(new_path)

    # Add a before_request handler for planning routes to initialize database
    @app.before_request
    def before_planning_request():
        """Initialize database connection for planning routes"""
        from flask import g, request

        # Only initialize for planning routes
        if request.path.startswith('/planning'):
            try:
                import sqlite3
                db_path = os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    'apps',
                    'planning',
                    'instance',
                    'planning.db')
                g.db = sqlite3.connect(db_path)
                g.db.row_factory = sqlite3.Row  # Allow column access by name
                if app.logger:
                    app.logger.debug("Database connection established for planning: %s", db_path)
            except Exception as e:
                if app.logger:
                    app.logger.error("Failed to connect to planning database: %s", e)
                from flask import jsonify
                return jsonify({"error": "Database connection failed"}), 500

    @app.teardown_appcontext
    def close_db(error):  # pylint: disable=unused-argument
        """Close database connection at end of request"""
        from flask import g
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # Only initialize database file in non-testing mode
    if not is_testing:
        with app.app_context():
            # Determine which database file is being used
            if os.environ.get('TESTING_PRODUCTION', '0') == '1':
                db_filename = 'mockcmms_test.db'
            else:
                db_filename = 'mockcmms.db'
            
            # Check if database exists before creating tables
            db_path = os.path.join(
                os.path.abspath(
                    os.path.dirname(__file__)),
                '..',
                'instance',
                db_filename)
            db_exists = os.path.exists(db_path)

            db.create_all()  # Create database tables for our models

            # Populate with dummy data if the DB was just created and we are in debug mode
            debug_use_test_db = os.getenv(
                'MOCKCMMS_DEBUG_USE_TEST_DB', '0').lower() in (
                '1', 'true', 'yes')
            if not db_exists and debug_use_test_db:
                try:
                    from .services.db_utils import populate_dummy_data
                    populate_dummy_data(app.logger)
                    if app.logger:
                        app.logger.info("Database automatically seeded with test data")
                except Exception as e:
                    if app.logger:
                        app.logger.error("Failed to auto-seed database: %s", e)

    @app.after_request
    def add_security_headers(response):
        """Add security headers to prevent extension interference"""
        response.headers['Permissions-Policy'] = 'unload=()'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        return response

    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates."""
        return dict(
            PLANNING_ENABLED=os.getenv('PLANNING_ENABLED', 'False').lower() in ('true', '1', 't'),
            REPORTS_ENABLED=os.getenv('REPORTS_ENABLED', 'False').lower() in ('true', '1', 't')
        )

    return app
