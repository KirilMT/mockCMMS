from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
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
    app.config['DEBUG_USE_TEST_DB'] = os.getenv('DEBUG_USE_TEST_DB', '0').lower() in ('1', 'true', 'yes')

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

    # Conditionally register the workforce_manager_bp from the workforceManager package
    if os.getenv('WORKFORCE_MANAGER_ENABLED', 'False').lower() in ('true', '1', 't'):
        try:
            # Import the blueprint from the workforceManager package (installed in editable mode)
            from apps.workforceManager.src.routes.workforce_manager import workforce_manager_bp
            app.register_blueprint(workforce_manager_bp)
            csrf.exempt(workforce_manager_bp)

            # Register the same blueprint again with /api prefix
            app.register_blueprint(workforce_manager_bp, url_prefix='/api', name='workforce_manager_api')

            if app.logger:
                app.logger.info("Workforce Manager Blueprint registered at /workforce-manager and /api")
        except Exception as e:
            if app.logger:
                app.logger.error(f"Failed to register Workforce Manager blueprint: {e}")
    else:
        if app.logger:
            app.logger.info("Workforce Manager Blueprint not enabled.")

    # Add a before_request handler for workforce_manager routes to initialize database
    @app.before_request
    def before_workforce_manager_request():
        """Initialize database connection for workforce_manager routes"""
        from flask import g, request

        # Only initialize for workforce_manager routes
        if request.path.startswith('/workforce-manager'):
            try:
                import sqlite3
                db_path = os.path.join(os.path.dirname(__file__), '..', 'apps', 'workforceManager', 'instance', 'workforce_manager.db')
                g.db = sqlite3.connect(db_path)
                g.db.row_factory = sqlite3.Row  # Allow column access by name
                if app.logger:
                    app.logger.debug(f"Database connection established for workforce_manager: {db_path}")
            except Exception as e:
                if app.logger:
                    app.logger.error(f"Failed to connect to workforce_manager database: {e}")
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
        debug_use_test_db = os.getenv('DEBUG_USE_TEST_DB', '0').lower() in ('1', 'true', 'yes')
        if not db_exists and debug_use_test_db:
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
        return dict(WORKFORCE_MANAGER_ENABLED=os.getenv('WORKFORCE_MANAGER_ENABLED', 'False').lower() in ('true', '1', 't'))

    return app