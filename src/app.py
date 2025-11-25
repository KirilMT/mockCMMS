from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv

# Correctly indented imports
from .services.db_utils import db

def create_app():
    app = Flask(__name__)
    
    # Load environment variables from .env file
    load_dotenv(dotenv_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '.env'))
    
    # Set debug flag for test database
    app.config['DEBUG_USE_TEST_DB'] = os.getenv('MOCKCMMS_DEBUG_USE_TEST_DB', '0').lower() in ('1', 'true', 'yes')

    # Configure the database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'mockcmms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'a_very_secret_key_for_mockcmms'

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Initialize CSRF protection to make csrf_token() available in templates
    csrf = CSRFProtect(app)

    # Ensure the instance folder exists
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
                app.logger.error(f"Failed to register Reports blueprint: {e}")
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
                app.logger.error(f"Failed to register Planning blueprint: {e}")
                app.logger.error(traceback.format_exc())
    else:
        if app.logger:
            app.logger.info("Planning Blueprint not enabled.")

    @app.before_request
    def redirect_legacy_urls():
        """Redirect legacy /planning-manager URLs to /planning."""
        from flask import request, redirect, url_for
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
                db_path = os.path.join(os.path.dirname(__file__), '..', 'apps', 'planning', 'instance', 'planning.db')
                g.db = sqlite3.connect(db_path)
                g.db.row_factory = sqlite3.Row  # Allow column access by name
                if app.logger:
                    app.logger.debug(f"Database connection established for planning: {db_path}")
            except Exception as e:
                if app.logger:
                    app.logger.error(f"Failed to connect to planning database: {e}")
                from flask import jsonify
                return jsonify({"error": "Database connection failed"}), 500

    @app.teardown_appcontext
    def close_db(error):
        """Close database connection at end of request"""
        from flask import g
        db = g.pop('db', None)
        if db is not None:
            db.close()

    with app.app_context():
        # Check if database exists before creating tables
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'mockcmms.db')
        db_exists = os.path.exists(db_path)
        
        db.create_all() # Create database tables for our models
        
        # Populate with dummy data if the DB was just created and we are in debug mode
        debug_use_test_db = os.getenv('MOCKCMMS_DEBUG_USE_TEST_DB', '0').lower() in ('1', 'true', 'yes')
        if not db_exists and debug_use_test_db and not app.config.get('TESTING', False):
            try:
                from .services.db_utils import populate_dummy_data
                populate_dummy_data(app.logger)
                if app.logger:
                    app.logger.info("Database automatically seeded with test data")
            except Exception as e:
                if app.logger:
                    app.logger.error(f"Failed to auto-seed database: {e}")

    @app.after_request
    def add_security_headers(response):
        """Add security headers to prevent extension interference"""
        response.headers['Permissions-Policy'] = 'unload=()'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        return response

    @app.context_processor
    def inject_config():
        return dict(
            PLANNING_ENABLED=os.getenv('PLANNING_ENABLED', 'False').lower() in ('true', '1', 't'),
            REPORTS_ENABLED=os.getenv('REPORTS_ENABLED', 'False').lower() in ('true', '1', 't')
        )

    return app
