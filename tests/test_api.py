import pytest
import json
from src.app import create_app
from src.services.db_utils import db, MaintenanceOrder, Skill, Asset
@pytest.fixture(scope='function')
def test_client():
    app = create_app()
    
    # Use an in-memory SQLite database for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing API endpoints

    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
        yield testing_client

        # Clean up the database after each test
        with app.app_context():
            db.session.remove()
            db.drop_all()

def test_get_mos_endpoint(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/v1/mos' endpoint is requested (GET)
    THEN check that the response is valid and contains the seeded maintenance orders
    """
    # Create some data for the test
    with test_client.application.app_context():
        # Add an asset to satisfy the foreign key constraint
        asset = Asset(asset_code='TEST-ASSET-1', name='Test Asset 1')
        db.session.add(asset)
        db.session.commit()

        skill1 = Skill(name='Python')
        mo1 = MaintenanceOrder(description='Routine server check', order_type='PM', asset_id=asset.id)
        mo2 = MaintenanceOrder(description='Database migration', order_type='Corrective', asset_id=asset.id)
        mo2.required_skills.append(skill1)
        db.session.add_all([skill1, mo1, mo2])
        db.session.commit()

    response = test_client.get('/api/v1/mos')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Check for presence of both descriptions, regardless of order
    descriptions = [item['description'] for item in data]
    assert 'Routine server check' in descriptions
    assert 'Database migration' in descriptions

def test_get_single_mo_endpoint(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/v1/mos/<id>' endpoint is requested (GET)
    THEN check that the response is valid and returns the correct maintenance order
    """
    with test_client.application.app_context():
        asset = Asset(asset_code='TEST-ASSET-2', name='Test Asset 2')
        db.session.add(asset)
        db.session.commit()
        mo = MaintenanceOrder(description='Single MO Test', order_type='PM', asset_id=asset.id)
        db.session.add(mo)
        db.session.commit()
        mo_id = mo.id

    response = test_client.get(f'/api/v1/mos/{mo_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == mo_id
    assert data['description'] == 'Single MO Test'

    # Test for a non-existent maintenance order
    response = test_client.get('/api/v1/mos/999')
    assert response.status_code == 404

def test_post_mo_endpoint(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/v1/mos' endpoint is posted to (POST)
    THEN check that a new maintenance order is created and returned
    """
    with test_client.application.app_context():
        # Ensure the asset exists for the foreign key constraint
        asset = Asset(asset_code='TEST-ASSET', name='Test Asset')
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id

    new_mo_data = {
        "description": "New Test MO",
        "notes": "This is a test.",
        "order_type": "Corrective",
        "asset_id": asset_id,
        "priority": "High",
        "status": "Pending",
        "required_skills": ["Python", "New Skill"]
    }
    
    response = test_client.post('/api/v1/mos',
                                data=json.dumps(new_mo_data),
                                content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['description'] == "New Test MO"
    assert data['id'] is not None

    # Verify the required skills were processed
    skill_names = [s['name'] for s in data['required_skills']]
    assert "New Skill" in skill_names

    # Verify the MO was actually added to the database
    with test_client.application.app_context():
        mo = db.session.get(MaintenanceOrder, data['id'])
        assert mo is not None
        assert mo.priority == "High"

        # Verify the new skill was created
        new_skill = Skill.query.filter_by(name="New Skill").first()
        assert new_skill is not None
