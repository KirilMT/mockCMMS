from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.reports.src.services.data_aggregator import DataAggregator

# ---------------------------------------------------------------------------
# Helpers – comparable column substitutes (avoid SQLAlchemy >= comparisons)
# ---------------------------------------------------------------------------


class _DummyCol:
    """Minimal SQLAlchemy column substitute that accepts comparison operators."""

    def __eq__(self, other):
        return True

    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True

    def in_(self, values):
        return True


class _DummyMO:
    """Minimal MaintenanceOrder model substitute with comparable columns."""

    query = MagicMock()
    order_type = _DummyCol()
    status = _DummyCol()
    created_at = _DummyCol()
    category = _DummyCol()
    modified_on = _DummyCol()


@pytest.fixture
def aggregator():
    return DataAggregator()


def test_get_shift_incidents_missing_asset(aggregator):
    """Test incident processing when MO has no asset."""
    # Use mocks for start/end to avoid datetime type checks
    start = MagicMock()
    start.__le__ = MagicMock(return_value=True)
    start.__ge__ = MagicMock(return_value=True)

    end = MagicMock()
    end.__le__ = MagicMock(return_value=True)
    end.__ge__ = MagicMock(return_value=True)

    mock_mo = MagicMock()
    mock_mo.id = 1
    mock_mo.asset = None  # Force N/A path
    mock_mo.description = "Test"
    mock_mo.created_at = datetime(2023, 1, 1, 10, 0, 0)
    mock_mo.priority = 1
    mock_mo.status = "Open"

    with patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO:
        # MockMO.created_at needs to be comparable too.
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        MockMO.created_at = mock_col
        MockMO.query.filter.return_value.all.return_value = [mock_mo]

        results = aggregator._get_shift_incidents(start, end)
        assert len(results) == 1
        assert results[0]["asset_name"] == "N/A"
        assert results[0]["asset_code"] == "N/A"


def test_get_aggregated_shift_data_missing_asset(aggregator):
    """Test shift aggregation when completed MO has no asset."""
    with patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO:
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        MockMO.created_at = mock_col

        # Mock internal helpers to avoid app context lookups
        aggregator._get_shift_incidents = MagicMock(return_value=[])
        aggregator._get_previous_shift_handover = MagicMock(return_value=[])
        aggregator._get_handover_from_previous = MagicMock(return_value=[])
        aggregator._get_handover_to_next = MagicMock(return_value=[])
        aggregator._get_engineering_support = MagicMock(return_value=[])

        # Mock completed MOs with NO ASSET
        mock_mo = MagicMock()
        mock_mo.id = 10
        mock_mo.asset = None
        mock_mo.description = "Desc"
        mock_mo.status = "Completed"
        mock_mo.subcategory = None
        mock_mo.modified_on = datetime(2023, 1, 1, 8, 0, 0)
        mock_mo.created_at = datetime(2023, 1, 1, 8, 0, 0)

        MockMO.query.filter.return_value.all.return_value = [mock_mo]

        data = aggregator.get_aggregated_shift_data("2023-01-01", "Early")

        items = data["break_activities"]
        assert len(items) == 1
        assert items[0]["asset"] == "N/A"


def test_get_aggregated_weekend_data_missing_asset(aggregator):
    """Test weekend aggregation when MOs have no asset (PM and Tickets)."""
    with patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO:
        # Weekend aggregation filters by created_at range.
        mock_created_col = MagicMock()
        mock_created_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_created_col.__le__ = MagicMock(return_value=MagicMock())
        MockMO.created_at = mock_created_col

        mock_pm = MagicMock()
        mock_pm.asset = None
        mock_pm.description = "PM Desc"
        mock_pm.status = "Completed"
        mock_pm.id = 1
        mock_pm.title = "PM Ticket"

        mock_mo = MagicMock()
        mock_mo.asset = None
        mock_mo.description = "MO Desc"
        mock_mo.status = "Completed"
        mock_mo.id = 99
        mock_mo.title = "MO Ticket"

        # Called first for PM query, then for corrective tickets query.
        MockMO.query.filter.return_value.all.side_effect = [[mock_pm], [mock_mo]]

        with (
            patch.object(aggregator, "_get_handover_from_previous", return_value=[]),
            patch.object(aggregator, "_get_handover_to_next", return_value=[]),
            patch.object(aggregator, "_get_engineering_support", return_value=[]),
        ):
            data = aggregator.get_aggregated_weekend_data("2023-10-28")

        assert data["pms"][0]["asset_code"] == "N/A"
        assert data["mos_tickets"][0]["asset_code"] == "N/A"


def test_get_weekend_tasks(aggregator):
    """Test get_weekend_tasks querying."""
    with patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO:
        # Configuration for comparisons on due_date
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__lt__ = MagicMock(return_value=MagicMock())
        MockMO.due_date = mock_col

        # Let's mock datetime completely to avoid complexity
        with patch("apps.reports.src.services.data_aggregator.datetime") as mock_dt_cls:
            mock_start_dt = MagicMock()
            mock_start_dt.__ge__ = MagicMock(return_value=True)
            mock_start_dt.__le__ = MagicMock(return_value=True)

            mock_end_dt = MagicMock()
            mock_end_dt.__ge__ = MagicMock(return_value=True)
            mock_end_dt.__le__ = MagicMock(return_value=True)

            # Setup chain: datetime.strptime(...).replace(...)
            mock_dt_cls.strptime.return_value.replace.side_effect = [
                mock_start_dt,
                mock_end_dt,
            ]
            # Also timedelta
            with patch("apps.reports.src.services.data_aggregator.timedelta"):
                # Setup filter return
                mock_task = MagicMock()
                mock_task.to_dict.return_value = {
                    "id": 1,
                    "description": "Weekend Task",
                }
                MockMO.query.filter.return_value.all.return_value = [mock_task]

                results = aggregator.get_weekend_tasks("2023-10-28", "2023-10-29")

                assert len(results) == 1
                assert results[0]["description"] == "Weekend Task"
                # Verify filter call used our mocks
                assert MockMO.query.filter.called


def test_get_shift_data(aggregator):
    """Test get_shift_data querying."""
    with (
        patch("apps.reports.src.services.data_aggregator.ShiftUtils") as MockUtils,
        patch("apps.reports.src.services.data_aggregator.MaintenanceOrder") as MockMO,
    ):
        # Configuration for comparisons on created_at
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__lt__ = MagicMock(return_value=MagicMock())
        MockMO.created_at = mock_col

        # Mock ShiftUtils
        mock_start = MagicMock()
        mock_end = MagicMock()
        MockUtils.return_value.get_shift_window.return_value = (mock_start, mock_end)

        # Mock query result
        mock_task = MagicMock()
        mock_task.to_dict.return_value = {"id": 1, "shift": "Early"}
        MockMO.query.filter.return_value.all.return_value = [mock_task]

        # Call the method
        results = aggregator.get_shift_data("2023-01-01", "Early")

        # Assertions
        assert len(results) == 1
        assert results[0]["shift"] == "Early"
        MockUtils.return_value.get_shift_window.assert_called_once()
        # Ensure filter called with mocked start/end
        args, _ = MockMO.query.filter.call_args
        # args contains the sqlalchemy expressions.
        # We cannot easily check exact expressions on args without complex matching.
        # We know __ge__ and __lt__ were called on created_at because we mocked them.
        MockMO.created_at.__ge__.assert_called_with(mock_start)
        MockMO.created_at.__lt__.assert_called_with(mock_end)


def test_get_aggregated_shift_data_handles_naive_completion_datetime(aggregator):
    """Ensure naive DB datetimes do not raise when shift window datetimes are aware."""
    with (
        patch("apps.reports.src.services.data_aggregator.ShiftUtils") as mock_utils,
        patch(
            "apps.reports.src.services.data_aggregator.MaintenanceOrder"
        ) as mock_mo_cls,
    ):
        aware_start = datetime(
            2026, 3, 6, 18, 0, tzinfo=datetime.now().astimezone().tzinfo
        )
        aware_end = datetime(
            2026, 3, 7, 6, 0, tzinfo=datetime.now().astimezone().tzinfo
        )
        mock_utils.return_value.get_shift_window.return_value = (aware_start, aware_end)

        aggregator._get_shift_incidents = MagicMock(return_value=[])
        aggregator._get_previous_shift_handover = MagicMock(return_value=[])
        aggregator._get_handover_from_previous = MagicMock(return_value=[])
        aggregator._get_handover_to_next = MagicMock(return_value=[])
        aggregator._get_engineering_support = MagicMock(return_value=[])

        corrective = MagicMock()
        corrective.id = 500
        corrective.asset = None
        corrective.description = "Completed corrective"
        corrective.status = "Completed"
        corrective.subcategory = None
        corrective.modified_on = datetime(2026, 3, 6, 19, 30)  # Naive datetime
        corrective.created_at = datetime(2026, 3, 6, 19, 0)

        mock_mo_cls.query.filter.return_value.all.return_value = [corrective]

        data = aggregator.get_aggregated_shift_data("2026-03-06", "Night")

        assert len(data["break_activities"]) == 1
        assert data["break_activities"][0]["mo_id"] == "MO-500"


# Replace old handover query-expression test with helper-level assertion.
def test_get_handover_to_next_uses_assignees_relationship(aggregator):
    """Assignee relationship should be treated as assigned for handover rules."""
    mo = MagicMock()
    mo.assignees_json = None
    mo.assignees = [MagicMock(id=1)]

    assert aggregator._has_assignees(mo) is True


def test_mo_matches_team_uses_relation_and_json(aggregator):
    """Team filter should match against relationship and legacy JSON assignees."""
    team_user_ids = {2}

    mo_relation = MagicMock()
    mo_relation.assignees = [MagicMock(id=2)]
    mo_relation.assignees_json = None

    mo_json = MagicMock()
    mo_json.assignees = []
    mo_json.assignees_json = '[{"user_id": 2}]'

    mo_other = MagicMock()
    mo_other.assignees = []
    mo_other.assignees_json = '[{"id": 3}]'

    assert aggregator._mo_matches_team(mo_relation, team_user_ids) is True
    assert aggregator._mo_matches_team(mo_json, team_user_ids) is True
    assert aggregator._mo_matches_team(mo_other, team_user_ids) is False


def test_extract_assignee_ids_supports_legacy_user_and_team_tokens(aggregator):
    """Legacy assignee tokens user:/team: should resolve to user IDs."""
    mo = MagicMock()
    mo.assignees = []
    mo.assignees_json = '["user:alex.tech", "team:Team A"]'

    with (
        patch("apps.reports.src.services.data_aggregator.User") as mock_user,
        patch("apps.reports.src.services.data_aggregator.Team") as mock_team,
    ):
        mock_user.query.filter_by.return_value.first.side_effect = [
            MagicMock(id=11),
            None,
        ]
        mock_team.query.filter_by.return_value.first.return_value = MagicMock(id=1)
        mock_user.query.filter_by.return_value.all.return_value = [
            MagicMock(id=11),
            MagicMock(id=12),
        ]

        assignee_ids = aggregator._extract_assignee_ids(mo)

    assert {11, 12}.issubset(assignee_ids)


def test_get_previous_shift_team_user_ids_without_app_context_returns_none(aggregator):
    """No app context should short-circuit to None (test-friendly behavior)."""
    assert aggregator._get_previous_shift_team_user_ids("2026-03-10", "Early") is None


def test_merge_handover_lists_deduplicates(aggregator):
    primary = [{"mo_id": 1, "description": "A"}, {"mo_id": 2, "description": "B"}]
    secondary = [{"mo_id": 1, "description": "A"}, {"mo_id": 3, "description": "C"}]

    merged = aggregator._merge_handover_lists(primary, secondary)

    assert merged == [
        {"mo_id": 1, "description": "A"},
        {"mo_id": 2, "description": "B"},
        {"mo_id": 3, "description": "C"},
    ]


def test_normalize_handover_items_skips_cancelled_mo(aggregator):
    with patch(
        "apps.reports.src.services.data_aggregator.MaintenanceOrder"
    ) as mock_mo_cls:
        cancelled = MagicMock()
        cancelled.status = "Cancelled"
        mock_mo_cls.query.get.return_value = cancelled

        normalized = aggregator._normalize_handover_items(
            [{"mo_id": 99, "description": "Old"}]
        )

    assert normalized == []


def test_normalize_handover_items_string_with_mo_pattern(aggregator):
    with patch(
        "apps.reports.src.services.data_aggregator.MaintenanceOrder"
    ) as mock_mo_cls:
        mo = MagicMock()
        mo.status = "In Progress"
        mo.asset = MagicMock(asset_code="AST-100")
        mo.description = "In progress task"
        mo.title = "Task title"
        mo.created_at = datetime(2026, 3, 10, 9, 30)
        mo.downtime_duration = 15
        mock_mo_cls.query.get.return_value = mo

        normalized = aggregator._normalize_handover_items(["handover MO-42 details"])

    assert normalized[0]["mo_id"] == 42
    assert normalized[0]["asset"] == "AST-100"
    assert normalized[0]["title"] == "Task title"


def test_extract_assignee_ids_from_dict_payload_username_team_and_numeric(aggregator):
    mo = MagicMock()
    mo.assignees = []
    mo.assignees_json = {
        "assignees": [
            {"username": "tech.user"},
            {"team_name": "Team X"},
            "7",
            8,
        ]
    }

    with (
        patch("apps.reports.src.services.data_aggregator.User") as mock_user,
        patch("apps.reports.src.services.data_aggregator.Team") as mock_team,
    ):
        mock_user.query.filter_by.return_value.first.return_value = MagicMock(id=101)
        mock_team.query.filter_by.return_value.first.return_value = MagicMock(id=10)
        mock_user.query.filter_by.return_value.all.return_value = [
            MagicMock(id=201),
            MagicMock(id=202),
        ]

        assignee_ids = aggregator._extract_assignee_ids(mo)

    assert {7, 8, 101, 201, 202}.issubset(assignee_ids)


def test_normalize_utc_variants(aggregator):
    aware = datetime.now().astimezone()
    naive = datetime(2026, 3, 10, 12, 0)

    assert aggregator._normalize_utc(None) is None
    assert aggregator._normalize_utc(naive).tzinfo is not None
    assert aggregator._normalize_utc(aware).tzinfo is not None


def test_has_assignees_handles_empty_legacy_values(aggregator):
    mo_none = MagicMock(assignees=[], assignees_json=None)
    mo_empty = MagicMock(assignees=[], assignees_json="[]")
    mo_null = MagicMock(assignees=[], assignees_json="null")

    assert aggregator._has_assignees(mo_none) is False
    assert aggregator._has_assignees(mo_empty) is False
    assert aggregator._has_assignees(mo_null) is False


def test_extract_assignee_ids_invalid_json_returns_relationship_only(aggregator):
    mo = MagicMock()
    mo.assignees = [MagicMock(id=77)]
    mo.assignees_json = "{bad-json}"

    assert aggregator._extract_assignee_ids(mo) == {77}


def test_get_team_user_ids_valid_and_invalid(aggregator):
    with patch("apps.reports.src.services.data_aggregator.User") as mock_user:
        mock_user.query.filter_by.return_value.all.return_value = [
            MagicMock(id=1),
            MagicMock(id=2),
        ]

        assert aggregator._get_team_user_ids(None) is None
        assert aggregator._get_team_user_ids("bad") is None
        assert aggregator._get_team_user_ids("4") == {1, 2}


def test_is_assigned_for_report_branches(aggregator):
    mo = MagicMock()
    mo.assignees = []
    mo.assignees_json = None

    assert aggregator._is_assigned_for_report(mo, None) is False

    mo.assignees = [MagicMock(id=5)]
    assert aggregator._is_assigned_for_report(mo, None) is True
    assert aggregator._is_assigned_for_report(mo, {5}) is True
    assert aggregator._is_assigned_for_report(mo, {6}) is False


# Removed obsolete _legacy_* variants that were superseded by the canonical tests below.


# ---------------------------------------------------------------------------
# Team-filter branch tests (use _DummyMO for comparable columns)
# ---------------------------------------------------------------------------


def test_get_shift_incidents_skips_non_matching_team(aggregator):
    """Incidents whose assignees don't belong to the filtered team are excluded."""
    mo = MagicMock(
        id=1,
        asset=None,
        title=None,
        description="Skip team",
        created_at=datetime(2026, 3, 10, 10, 0),
        downtime_duration=None,
        root_cause=None,
        recovery=None,
        priority="High",
        status="Completed",
        assignees=[],
        assignees_json='[{"id": 9}]',
    )
    _DummyMO.query.filter.return_value.all.return_value = [mo]

    with patch(
        "apps.reports.src.services.data_aggregator.MaintenanceOrder",
        new=_DummyMO,
    ):
        result = aggregator._get_shift_incidents(
            datetime(2026, 3, 10, 6, 0),
            datetime(2026, 3, 10, 18, 0),
            team_user_ids={5},
        )

    assert result == []


def test_get_engineering_support_filters_team_and_unknown_asset(aggregator):
    """Engineering support items from the wrong team are excluded; N/A used when no
    asset."""
    mo_keep = MagicMock(
        id=10,
        title=None,
        description="Engineering fix",
        status="Completed",
        asset=None,
        assignees=[MagicMock(id=3)],
        assignees_json=None,
    )
    mo_skip = MagicMock(
        id=11,
        title=None,
        description="Skip me",
        status="Completed",
        asset=None,
        assignees=[MagicMock(id=99)],
        assignees_json=None,
    )
    _DummyMO.query.filter.return_value.all.return_value = [mo_keep, mo_skip]

    with patch(
        "apps.reports.src.services.data_aggregator.MaintenanceOrder",
        new=_DummyMO,
    ):
        result = aggregator._get_engineering_support(
            datetime(2026, 3, 10, 6, 0),
            datetime(2026, 3, 10, 18, 0),
            team_user_ids={3},
        )

    assert result == [
        {
            "mo_id": 10,
            "id": 10,
            "asset": "N/A",
            "asset_code": "N/A",
            "title": "MO-10",
            "description": "Engineering fix",
            "status": "Completed",
        }
    ]


def test_get_previous_shift_team_user_ids_resolves_team_members(aggregator, app):
    """Successfully resolves user IDs for the previous shift's team."""
    fake_team = MagicMock(id=4)

    with app.app_context():
        with (
            patch.object(
                aggregator,
                "_get_previous_shift",
                return_value=("2026-03-09", "Night"),
            ),
            patch("apps.reports.src.services.data_aggregator.Team") as mock_team,
            patch(
                "src.services.shift_utils.get_shift_teams",
                return_value=(None, fake_team),
            ),
            patch("apps.reports.src.services.data_aggregator.User") as mock_user,
        ):
            mock_team.query.all.return_value = [fake_team]
            mock_user.query.filter_by.return_value.all.return_value = [MagicMock(id=8)]
            result = aggregator._get_previous_shift_team_user_ids("2026-03-10", "Early")

    assert result == {8}


def test_get_aggregated_shift_data_splits_engineering_and_flux(aggregator, app):
    """Engineering-category MOs go to engineering_support; others to
    break_activities."""
    engineering = MagicMock(
        id=20,
        asset=None,
        title=None,
        description="Engineering item",
        status="Completed",
        category="Engineering",
        modified_on=datetime(2026, 3, 10, 10, 0),
        created_at=datetime(2026, 3, 10, 9, 0),
        assignees=[MagicMock(id=7)],
        assignees_json=None,
    )
    flux = MagicMock(
        id=21,
        asset=None,
        title=None,
        description="Flux item",
        status="Completed",
        category="Operations",
        modified_on=datetime(2026, 3, 10, 11, 0),
        created_at=datetime(2026, 3, 10, 9, 30),
        assignees=[MagicMock(id=7)],
        assignees_json=None,
    )
    _DummyMO.query.filter.return_value.all.return_value = [engineering, flux]

    with app.app_context():
        with (
            patch("apps.reports.src.services.data_aggregator.ShiftUtils") as mock_utils,
            patch(
                "apps.reports.src.services.data_aggregator.MaintenanceOrder",
                new=_DummyMO,
            ),
            patch.object(aggregator, "_get_team_user_ids", return_value={7}),
            patch.object(aggregator, "_get_shift_incidents", return_value=[]),
            patch.object(
                aggregator, "_get_previous_shift_team_user_ids", return_value=None
            ),
            patch.object(aggregator, "_get_previous_shift_handover", return_value=[]),
            patch.object(aggregator, "_get_handover_from_previous", return_value=[]),
            patch.object(aggregator, "_get_handover_to_next", return_value=[]),
        ):
            mock_utils.return_value.get_shift_window.return_value = (
                datetime(2026, 3, 10, 6, 0),
                datetime(2026, 3, 10, 18, 0),
            )
            result = aggregator.get_aggregated_shift_data(
                "2026-03-10", "Early", team_id="7"
            )

    assert result["engineering_support"][0]["mo_id"] == "MO-20"
    assert result["break_activities"][0]["type"] == "flux_ticket"
