from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from .services.db import db # Import the db object from services/db.py

def create_app():
    app = Flask(__name__)

    # Configure the database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'mockcmms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'a_very_secret_key_for_mockcmms' # Add this line

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Ensure the instance folder exists
    instance_path = os.path.join(app.root_path, '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)

    # Register blueprints (will add later)
    from .routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all() # Create database tables for our models

    return app
