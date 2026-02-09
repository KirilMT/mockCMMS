from unittest.mock import MagicMock, patch


def test_reports_list_generated_by_resolution(auth_client, app):
    """Test that generated_by user resolution works in reports list."""
    # auth_client already has session set up with a valid user

    # Mock DB query for Report
    with patch("apps.reports.src.models.Report.query") as mock_report_query:
        # Mock Reports
        mock_report = MagicMock()
        mock_report.generated_by = 1
        mock_report.to_dict.return_value = {"id": 1, "title": "Test Report"}
        mock_report.generated_on.desc.return_value = "desc_obj"

        mock_report_query.order_by.return_value.all.return_value = [mock_report]

        # Mock User query - since User is imported inside, we patch where it is defined
        with patch("src.services.db_utils.User.query") as mock_user_query:
            mock_user = MagicMock()
            mock_user.username = "TestUser"
            # filter_by(id=1).first()
            mock_user_query.filter_by.return_value.first.return_value = mock_user

            resp = auth_client.get("/reports/")
            assert (
                resp.status_code == 200
            ), f"Status: {resp.status_code}, Location: {resp.headers.get('Location')}"


def test_reports_list_generated_by_exception(auth_client, app):
    """Test exception handling during user resolution."""
    # auth_client already has session set up

    with patch("apps.reports.src.models.Report.query") as mock_report_query:
        mock_report = MagicMock()
        mock_report.generated_by = 1
        mock_report.to_dict.return_value = {"id": 1}
        mock_report_query.order_by.return_value.all.return_value = [mock_report]

        # Patch User query to raise exception
        with patch("src.services.db_utils.User.query") as mock_user_query:
            mock_user_query.filter_by.side_effect = Exception("User DB Error")

            resp = auth_client.get("/reports/")
            assert resp.status_code == 200


def test_generate_shift_report_missing_shift_info(auth_client, app):
    """Test generating shift report when data aggregator returns data without
    shift_info."""
    with patch("apps.reports.src.services.data_aggregator.DataAggregator") as MockAgg:
        # return empty dict (no shift_info)
        MockAgg.return_value.get_aggregated_shift_data.return_value = {}

        with patch("apps.reports.src.models.Report") as MockReportModel:
            # Just mock the model instantiation to verify call args or avoid crashes.

            # Mock db.session.add/commit to avoid detached instance errors.
            with patch("src.services.db_utils.db.session"):
                resp = auth_client.post(
                    "/reports/generate",
                    data={
                        "title": "Test Report",
                        "report_type": "shift_report",
                        "shift_date": "2023-01-01",
                        "shift_name": "Early",
                        "handover_from_previous": "Note 1",
                        "handover_to_next": "Note 2",
                    },
                )

                assert resp.status_code == 302
                # Handovers should be stored in root data when shift_info is missing.
                # Call args can be inspected if needed.
                call_args = MockReportModel.call_args[1]
                data = call_args["data"]
                assert data["handover_from_previous"] == ["Note 1"]
                assert data["handover_to_next"] == ["Note 2"]


def test_report_detail_exceptions(auth_client, app):
    """Test exceptions in report_detail fetch logic."""
    # Mock Report.query.get_or_404
    with patch("apps.reports.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.report_type = "shift_report"
        mock_report.data = {"team_name": "Team A"}
        mock_query.get_or_404.return_value = mock_report

        # 1. Test Team query exception
        with patch("src.services.db_utils.db.session.query") as mock_db_query:
            mock_db_query.side_effect = Exception("Team Query Fail")

            # 2. Test Asset query exception
            with patch("src.services.db_utils.Asset.query") as mock_asset_query:
                # Asset query is a property on model usually, but if it is query object
                # Asset.query.with_entities...
                mock_asset_query.with_entities.side_effect = Exception("Asset Fail")

                # 3. Test config load exception is hard to trigger unless file missing
                # or invalid json.
                # We can patch open

                resp = auth_client.get("/reports/1")
                assert resp.status_code == 200


def test_update_report_data_header(auth_client, app):
    """Test updating header section."""
    with patch("apps.reports.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.data = {"shift_info": {}}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            resp = auth_client.post(
                "/reports/1/update",
                json={
                    "section": "header",
                    "date": "2023-01-01",
                    "shift": "Early",
                    "team_name": "Team New",
                    "team_color": "#ffffff",
                },
            )
            assert resp.status_code == 200
            assert mock_report.data["shift_info"]["team_name"] == "Team New"
            assert mock_report.data["team_color"] == "#ffffff"


def test_update_report_data_metadata(auth_client, app):
    """Test updating metadata section."""
    with patch("apps.reports.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.data = {}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            resp = auth_client.post(
                "/reports/1/update",
                json={
                    "section": "metadata",
                    "key": "some_key",
                    "value": "some_value",
                },
            )
            assert resp.status_code == 200
            assert mock_report.data["some_key"] == "some_value"


def test_update_report_handover_initialization(auth_client, app):
    """Test handover list initialization when missing."""
    with patch("apps.reports.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        # Data has no shift_info
        mock_report.data = {}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            # Add item to handover_from, trigger init of shift_info and list
            resp = auth_client.post(
                "/reports/1/update",
                json={
                    "section": "handover_from",
                    "action": "add",
                    "description": "New Item",
                },
            )
            assert resp.status_code == 200
            assert "shift_info" in mock_report.data
            assert "handover_from_previous" in mock_report.data["shift_info"]
            assert len(mock_report.data["shift_info"]["handover_from_previous"]) == 1

            # Now test handover_to
            mock_report.data = {}  # Reset
            resp = auth_client.post(
                "/reports/1/update",
                json={
                    "section": "handover_to",
                    "action": "add",
                    "description": "New Item",
                },
            )
            assert resp.status_code == 200
            assert "handover_to_next" in mock_report.data["shift_info"]


def test_update_report_activities_add(auth_client, app):
    """Test adding activities (Engineering Support vs Flux)."""
    with patch("apps.reports.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.data = {}
        mock_query.get_or_404.return_value = mock_report

        with patch("src.services.db_utils.db.session.commit"):
            # Add Engineering Support
            resp = auth_client.post(
                "/reports/1/update",
                json={
                    "section": "activities",
                    "action": "add",
                    "type": "engineering_support",  # Trigger target_key value.
                    "description": "Eng Item",
                },
            )
            assert resp.status_code == 200
            assert "engineering_support" in mock_report.data
            assert len(mock_report.data["engineering_support"]) == 1

            # Delete item
            resp = auth_client.post(
                "/reports/1/update",
                json={
                    "section": "engineering_support",
                    "action": "delete",
                    "index": 0,
                },
            )
            assert resp.status_code == 200
            assert len(mock_report.data["engineering_support"]) == 0


def test_report_detail_technician_count_logic(auth_client, app):
    """Test technician count logic branches."""
    # Mock Report.query.get_or_404
    with patch("apps.reports.src.models.Report.query") as mock_query:
        mock_report = MagicMock()
        mock_report.report_type = "shift_report"
        # Case 1: attendance_total is in data
        mock_report.data = {"attendance_total": 5}
        mock_query.get_or_404.return_value = mock_report

        auth_client.get("/reports/1")
        # We can check context but that's harder without capture_templates
        # We assume it runs without error covering the lines

        # Case 2: No attendance_total, but team_name in shift_info
        mock_report.data = {"shift_info": {"team_name": "Team A"}}

        with patch("src.services.db_utils.Team.query") as mock_team_q:
            mock_team = MagicMock()
            mock_team_q.filter_by.return_value.first.return_value = mock_team

            with patch("src.services.db_utils.User.query") as mock_user_q:
                mock_user_q.filter_by.return_value.count.return_value = 10

                resp = auth_client.get("/reports/1")
                assert resp.status_code == 200
