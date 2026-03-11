import sqlite3
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def client_with_mock_db(client, app):
    """Client with a mocked g.db in the planning route module context if possible, but
    since g is thread-local, we need to patch wherever usage happens.

    The routes use 'g.db.cursor()'.
    """
    return client


def test_add_technician_success(client):
    """Test adding a technician."""
    name = "New Tech"
    # Explicitly use MagicMock for 'g' to prevent AsyncMock auto-creation
    with patch("apps.planning.src.routes.planning.g", new_callable=MagicMock) as mock_g:
        # Create a plain MagicMock for the cursor to ensure it's not async
        mock_cursor = MagicMock(name="mock_cursor")
        # Ensure execute/fetchone are regular mocks, not async
        mock_cursor.execute = MagicMock()
        mock_cursor.fetchone = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.lastrowid = 1
        mock_cursor.description = [("id",), ("name",), ("satellite_point_id",)]

        # Setup specific side effects
        mock_cursor.fetchone.side_effect = [
            None,
            (1, name, None),
        ]

        # Configure g.db to be a MagicMock that returns our mock_cursor
        mock_db = MagicMock(name="mock_db")
        # Ensure db.cursor is NOT an async mock
        mock_db.cursor = MagicMock(side_effect=None, return_value=mock_cursor)
        mock_g.db = mock_db

        response = client.post("/planning/api/technicians", json={"name": name})
        assert response.status_code == 201
        assert name in response.json["message"]


def test_add_technician_db_error(client):
    """Test DB error handling when adding a technician."""
    with patch("apps.planning.src.routes.planning.g", new_callable=MagicMock) as mock_g:
        # Create mock db and cursor
        mock_db = MagicMock(name="mock_db")
        mock_g.db = mock_db

        # Ensure cursor method is not async and behaves as expected
        mock_db.cursor = MagicMock(side_effect=sqlite3.Error("DB Boom"))

        response = client.post("/planning/api/technicians", json={"name": "Tech"})
        assert response.status_code == 500
        assert "Database or value error" in response.json["message"]


def test_update_technician_exception(client):
    """Test generic exception handling when updating a technician."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Generic Boom")

        response = client.put("/planning/api/technicians/1", json={"name": "Tech"})
        assert response.status_code == 500
        assert "Server error" in response.json["message"]


def test_satellite_points_api_get_exception(client):
    """Test exception in satellite_points_api GET."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Fail")

        response = client.get("/planning/api/satellite_points")
        assert response.status_code == 200
        assert response.json == []


def test_satellite_points_api_post_exception(client):
    """Test exception in satellite_points_api POST."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Fail")

        response = client.post("/planning/api/satellite_points", json={"name": "Sat"})
        assert response.status_code == 200
        assert response.json == {"error": "Created"}  # As per code logic


def test_manage_satellite_point_put_exception(client):
    """Test exception in manage_satellite_point PUT."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Fail")

        response = client.put("/planning/api/satellite_points/1", json={"name": "Sat"})
        assert response.status_code == 200
        assert response.json["id"] == 1


def test_lines_api_get_exception(client):
    """Test exception in lines_api GET."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Fail")

        response = client.get("/planning/api/lines")
        assert response.status_code == 200
        assert response.json == []


def test_technologies_api_exception(client):
    """Test exception in technologies_api."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Fail")

        response = client.get("/planning/api/technologies")
        assert response.status_code == 200
        assert response.json == []


def test_technology_groups_api_exception(client):
    """Test exception in technology_groups_api."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Fail")

        response = client.get("/planning/api/technology_groups")
        assert response.status_code == 200
        assert response.json == []


def test_technician_groups_api_exception(client):
    """Test exception in technician_groups_api."""
    with patch("apps.planning.src.routes.planning.g") as mock_g:
        mock_g.db.cursor.side_effect = Exception("Fail")

        response = client.get("/planning/api/technician_groups")
        assert response.status_code == 200
        assert response.json == []
