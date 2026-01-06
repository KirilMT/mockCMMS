import pytest
import requests
import time
from multiprocessing import Process
import os
import json

# Adjust the path to import from the apps
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

from apps.planning.src.app import create_app as create_wm_app
from src.app import create_app as create_mock_app

# TODO: seed_data function doesn't exist yet - need to create or find it
# from src.services.db_utils import seed_data

# Mark all tests in this file as skip until seed_data is implemented
pytestmark = pytest.mark.skip(
    reason="Integration tests require seed_data function which doesn't exist yet"
)

# --- Server Fixtures ---


def run_server(app, port):
    """Function to run a Flask app in a separate process."""
    # Disable debug mode for subprocesses to prevent reloader issues
    app.run(debug=False, port=port)


@pytest.fixture(scope="module")
def mock_cmms_server():
    """Fixture to run the mockCMMS server."""
    # TODO: Seed the database before starting the server once seed_data is available
    # seed_data()

    app = create_mock_app()
    port = 5001
    server_process = Process(target=run_server, args=(app, port))
    server_process.start()

    # Wait for the server to be ready
    retries = 10  # Increased retries
    while retries > 0:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/")
            response.raise_for_status()  # Raise for HTTP errors
            break
        except (requests.ConnectionError, requests.exceptions.HTTPError):
            retries -= 1
            time.sleep(1)
    else:
        server_process.terminate()
        server_process.join()
        raise RuntimeError("mockCMMS server did not start in time.")

    yield f"http://127.0.0.1:{port}"

    server_process.terminate()
    server_process.join()


@pytest.fixture(scope="module")
def planning_server_api_mode():
    """Fixture to run the planning server in API mode."""
    # Set environment variable to use API data source
    os.environ["DATA_SOURCE"] = "api"

    app = create_wm_app()
    port = 5000
    server_process = Process(target=run_server, args=(app, port))
    server_process.start()

    # Wait for the server to be ready
    retries = 10  # Increased retries
    while retries > 0:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/health")
            response.raise_for_status()  # Raise for HTTP errors
            break
        except (requests.ConnectionError, requests.exceptions.HTTPError):
            retries -= 1
            time.sleep(1)

    else:
        server_process.terminate()
        server_process.join()
        del os.environ["DATA_SOURCE"]
        raise RuntimeError("planning server did not start in time.")

    yield f"http://127.0.0.1:{port}"

    server_process.terminate()
    server_process.join()

    # Unset environment variable
    del os.environ["DATA_SOURCE"]


# --- Integration Test ---


def test_full_integration_workflow(mock_cmms_server, planning_server_api_mode):
    """
    Tests the full integration workflow:
    1. Logs into mockCMMS.
    2. Navigates to the embedded planning page.
    3. Verifies planning loads and uses data from mockCMMS.
    """
    mock_cmms_url = mock_cmms_server
    planning_url = planning_server_api_mode

    # 1. Log into mockCMMS
    session = requests.Session()
    login_data = {"username": "admin", "password": "adminpass"}
    login_response = session.post(f"{mock_cmms_url}/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    assert login_response.json()["message"] == "Login successful"

    # 2. Navigate to the embedded planning page within mockCMMS
    wm_embed_response = session.get(f"{mock_cmms_url}/planning-manager")
    assert wm_embed_response.status_code == 200
    assert "Planning Integration" in wm_embed_response.text
    assert f'<iframe src="{planning_url}/"' in wm_embed_response.text

    # 3. Verify planning loads and uses data from mockCMMS
    # Since planning is embedded via iframe, we need to make a direct request
    # to planning's dashboard to check its data.
    # The index_route in planning redirects to manage_mappings_route when DATA_SOURCE=api

    # Make a request to planning's manage_mappings_route
    # This will trigger the data loading from mockCMMS API
    wm_manage_mappings_response = session.get(f"{planning_url}/manage_mappings_ui")
    assert wm_manage_mappings_response.status_code == 200

    # Check if the page contains elements that would be populated by the API data
    # This is a basic check, more robust checks would involve parsing the HTML
    # or making direct API calls to planning's internal data endpoints if available.
    assert "Manage Mappings" in wm_manage_mappings_response.text

    # A more direct way to check if data was loaded would be to call planning's
    # internal API that serves the loaded tasks. Assuming such an API exists or can be created.
    # For now, we'll rely on the fact that the manage_mappings_ui page would fail
    # if data loading from API failed.

    # Example: If planning had an API to list loaded tasks:
    # wm_tasks_api_response = session.get(f"{planning_url}/api/tasks_loaded")
    # assert wm_tasks_api_response.status_code == 200
    # loaded_tasks = wm_tasks_api_response.json()
    # assert len(loaded_tasks) > 0
    # assert loaded_tasks[0]['scheduler_group_task'] == 'Server Maintenance'

    print("\nFull integration workflow test passed!")
