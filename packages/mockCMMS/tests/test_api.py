import pytest
import json
from packages.mockCMMS.src.app import create_app
from packages.mockCMMS.src.services.db import db, Task, Skill
from packages.mockCMMS.src.services.seed import seed_data

@pytest.fixture(scope='module')
def test_client():
    """Fixture to create a test client for the mockCMMS app."""
    app = create_app()
    
    # Use an in-memory SQLite database for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
            seed_data() # Seed the in-memory database
        yield testing_client
    
    # No need to clean up, in-memory database is ephemeral

def test_get_tasks_endpoint(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/v1/tasks' endpoint is requested (GET)
    THEN check that the response is valid and contains the seeded tasks
    """
    response = test_client.get('/api/v1/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 4 # Based on the seed data
    assert data[0]['scheduler_group_task'] == 'Server Maintenance'
    assert 'Python' in data[1]['required_skills']

def test_get_single_task_endpoint(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/v1/tasks/<id>' endpoint is requested (GET)
    THEN check that the response is valid and returns the correct task
    """
    response = test_client.get('/api/v1/tasks/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == 1
    assert data['scheduler_group_task'] == 'Server Maintenance'

    # Test for a non-existent task
    response = test_client.get('/api/v1/tasks/999')
    assert response.status_code == 404

def test_post_task_endpoint(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/v1/tasks' endpoint is posted to (POST)
    THEN check that a new task is created and returned
    """
    new_task_data = {
        "scheduler_group_task": "New Test Task",
        "planning_notes": "This is a test.",
        "lines": "Test Line",
        "mitarbeiter_pro_aufgabe": 1,
        "planned_worktime_min": 30,
        "priority": "D",
        "quantity": 1,
        "task_type": "Rep",
        "ticket_mo": "TEST-001",
        "required_skills": ["Python", "New Skill"]
    }
    
    response = test_client.post('/api/v1/tasks',
                                data=json.dumps(new_task_data),
                                content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['scheduler_group_task'] == "New Test Task"
    assert data['id'] is not None
    assert "New Skill" in data['required_skills']

    # Verify the task was actually added to the database
    with test_client.application.app_context():
        task = Task.query.get(data['id'])
        assert task is not None
        assert task.priority == "D"
        
        # Verify the new skill was created
        new_skill = Skill.query.filter_by(name="New Skill").first()
        assert new_skill is not None
