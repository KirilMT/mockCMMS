# src/app.py

"""Flask application factory for mockCMMS."""

import os
import sqlite3
import traceback
from flask import Flask, g, request, redirect, jsonify, session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from .services.db_utils import db, User
from .services.db_seeding import populate_dummy_data

def create_app(config_overrides=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev_key_fallback_for_testing'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=os.environ.get('TESTING', '0') == '1'
    )

    if not app.config['TESTING']:
        load_dotenv(os.path.join(app.root_path, '..', '.env'))

    db_name = 'mockcmms_test.db' if os.environ.get('TESTING_PRODUCTION') else 'mockcmms.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, db_name)}"

    if config_overrides:
        app.config.from_mapping(config_overrides)

    # --- Initializations ---
    db.init_app(app)
    csrf = CSRFProtect(app)

    # --- Instance Folder & Database Setup ---
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        app.logger.error("Failed to create instance folder.")

    with app.app_context():
        db.create_all()
        if app.config.get('AUTO_SEED_DATABASE', True):
            populate_dummy_data(app.logger)

    # --- Blueprints ---
    _register_blueprints(app, csrf)

    # --- Request Hooks & Context Processors ---
    _register_request_handlers(app)
    _register_context_processors(app)

    return app

def _register_blueprints(app, csrf):
    """Register all application blueprints."""
    from .routes.api import api_bp
    from .routes.main import main_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(main_bp)

    # Conditionally register modular apps
    if os.getenv('REPORTS_ENABLED', 'False').lower() in ('true', '1', 't'):
        try:
            from apps.reports.src.routes.reports import reports_bp
            app.register_blueprint(reports_bp)
            csrf.exempt(reports_bp)
            app.logger.info("Reports Blueprint registered.")
        except ImportError as e:
            app.logger.error(f"Failed to register Reports blueprint: {e}")

    if os.getenv('PLANNING_ENABLED', 'False').lower() in ('true', '1', 't'):
        try:
            from apps.planning.src.routes.planning import planning_bp
            app.register_blueprint(planning_bp)
            csrf.exempt(planning_bp)
            app.logger.info("Planning Blueprint registered.")
        except ImportError as e:
            app.logger.error(f"Failed to register Planning blueprint: {e}\n{traceback.format_exc()}")

def _register_request_handlers(app):
    """Register before_request, after_request, and teardown_appcontext handlers."""
    @app.before_request
    def load_logged_in_user():
        """If a user id is in the session, load the user object from the database into g.user."""
        user_id = session.get('user_id')
        g.user = User.query.get(user_id) if user_id is not None else None

    @app.before_request
    def redirect_legacy_urls():
        if request.path.startswith('/planning-manager'):
            new_path = request.full_path.replace('/planning-manager', '/planning', 1)
            return redirect(new_path, code=301)

    if os.getenv('PLANNING_ENABLED', 'False').lower() in ('true', '1', 't'):
        @app.before_request
        def before_planning_request():
            if request.path.startswith('/planning'):
                try:
                    db_path = os.path.join(app.root_path, '..', 'apps', 'planning', 'instance', 'planning.db')
                    g.db = sqlite3.connect(db_path)
                    g.db.row_factory = sqlite3.Row
                except sqlite3.Error as e:
                    app.logger.error(f"Failed to connect to planning database: {e}")
                    return jsonify({"error": "Database connection failed"}), 503

    @app.teardown_appcontext
    def close_db(exception=None):
        db_conn = g.pop('db', None)
        if db_conn is not None:
            db_conn.close()

    @app.after_request
    def add_security_headers(response):
        response.headers['Permissions-Policy'] = 'unload=()'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        return response

def _register_context_processors(app):
    """Register context processors to inject variables into templates."""
    @app.context_processor
    def inject_config():
        return {
            'PLANNING_ENABLED': os.getenv('PLANNING_ENABLED', 'False').lower() in ('true', '1', 't'),
            'REPORTS_ENABLED': os.getenv('REPORTS_ENABLED', 'False').lower() in ('true', '1', 't')
        }
