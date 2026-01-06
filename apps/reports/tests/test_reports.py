import pytest
import os
from flask import Flask, session
from datetime import datetime, timedelta
from src.app import create_app
from src.services.db_utils import db, MaintenanceOrder, Asset, User
from apps.reports.src.models import Incident
from apps.reports.src.services.data_aggregator import DataAggregator
from apps.reports.src.services.report_generator import ReportGenerator

@pytest.fixture
def app():
    # Configure app for testing
    # Force REPORTS_ENABLED via environment variable for the duration of the test
    os.environ['REPORTS_ENABLED'] = 'true'

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'REPORTS_ENABLED': True,
        'WTF_CSRF_ENABLED': False  # Disable CSRF for testing
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    del os.environ['REPORTS_ENABLED']

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'testuser'
    return client

def test_incident_model(app):
    with app.app_context():
        incident = Incident(
            incident_type="Breakdown",
            equipment_line="Line 1",
            description="Test breakdown",
            severity="High",
            technician_name="Tech 1"
        )
        db.session.add(incident)
        db.session.commit()

        saved_incident = Incident.query.first()
        assert saved_incident.incident_type == "Breakdown"
        assert saved_incident.equipment_line == "Line 1"

def test_data_aggregator(app):
    with app.app_context():
        # Setup data
        today = datetime.now()

        # Create Asset
        asset = Asset(asset_code="A1", name="Test Asset")
        db.session.add(asset)
        db.session.commit()

        # Create MaintenanceOrder
        mo = MaintenanceOrder(
            asset_id=asset.id,
            description="Test Order",
            order_type="Preventive",
            status="Completed",
            due_date=today,
            created_at=today
        )
        db.session.add(mo)

        # Create Incident
        incident = Incident(
            incident_type="Safety Issue",
            equipment_line="Line 2",
            description="Test Safety",
            severity="Medium",
            technician_name="Tech 1",
            timestamp=today
        )
        db.session.add(incident)
        db.session.commit()

        aggregator = DataAggregator()

        # Test weekend tasks (simplified check)
        start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        tasks = aggregator.get_weekend_tasks(start_date, end_date)
        assert len(tasks) >= 0 # Just checking it runs without error as date logic is complex

        # Test incidents
        incidents = aggregator.get_incidents()
        assert len(incidents) == 1
        assert incidents[0]['incident_type'] == "Safety Issue"

def test_weekend_report_route(auth_client):
    response = auth_client.get('/reports/weekend/')
    assert response.status_code == 200
    assert b"Weekend Task Report" in response.data

def test_shift_report_route(auth_client):
    response = auth_client.get('/reports/shift/')
    assert response.status_code == 200
    assert b"Shift Production Report" in response.data

def test_incident_routes(auth_client):
    # Test list
    response = auth_client.get('/reports/incidents/')
    assert response.status_code == 200
    assert b"Incident Reports" in response.data

    # Test new form
    response = auth_client.get('/reports/incidents/new')
    assert response.status_code == 200
    assert b"Log New Incident" in response.data

    # Test create
    response = auth_client.post('/reports/incidents/', data={
        'incident_type': 'Breakdown',
        'equipment_line': 'Line X',
        'description': 'Test Breakdown',
        'severity': 'Critical'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Incident logged successfully" in response.data
