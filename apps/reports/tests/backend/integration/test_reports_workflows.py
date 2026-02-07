import os

import pytest

from apps.reports.src.models import Incident
from apps.reports.src.services.data_aggregator import DataAggregator

# Skip all tests in this file if REPORTS_ENABLED is not True
pytestmark = pytest.mark.skipif(
    os.getenv("REPORTS_ENABLED", "true").lower() not in ("true", "1", "t"),
    reason="Reports module is disabled (REPORTS_ENABLED=False)",
)


def test_incident_workflow(auth_client, app):
    """
    Integration Test:
    1. Create Incident via Route
    2. Verify in Database
    3. Verify in Aggregator Service
    4. Verify in Report Route
    """
    # 1. Create Incident via Route
    response = auth_client.post(
        "/reports/incidents/",
        data={
            "incident_type": "Safety Issue",
            "equipment_line": "Line Int",
            "description": "Integration Test",
            "severity": "Medium",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Incident logged successfully" in response.data

    with app.app_context():
        # 2. Verify in Database
        incident = Incident.query.filter_by(description="Integration Test").first()
        assert incident is not None
        assert incident.incident_type == "Safety Issue"

        # 3. Verify in Aggregator Service
        aggregator = DataAggregator()
        incidents = aggregator.get_incidents()
        # Find our incident in the list
        found = any(i["description"] == "Integration Test" for i in incidents)
        assert found

    # 4. Verify in Report Route (Incident List)
    response = auth_client.get("/reports/incidents/")
    assert b"Integration Test" in response.data
