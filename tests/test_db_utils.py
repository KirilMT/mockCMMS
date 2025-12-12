"""
Tests for database utility functions (db_utils.py).

This module tests the database population functions and model relationships
to ensure data integrity and proper ORM behavior.
"""
import logging
import pytest
from src.services.db_utils import (
    db, populate_dummy_data,
    User, Asset, MaintenanceOrder, SparePart, Skill, Role
)


class TestDatabaseUtilities:
    """Test database utility functions."""

    def test_populate_dummy_data(self, app, client):
        """
        Test that populate_dummy_data successfully populates the database.

        Verifies:
        - Function executes without errors
        - Database contains assets after population
        - Database contains maintenance orders after population
        - Database contains users after population
        """
        # Setup logger
        logger = logging.getLogger(__name__)

        with app.app_context():
            # Verify database is initially empty
            assert Asset.query.count() == 0
            assert MaintenanceOrder.query.count() == 0
            assert User.query.count() == 0

            # Populate database
            populate_dummy_data(logger)

            # Verify data was populated
            assert Asset.query.count() > 0, "Assets should be populated"
            assert MaintenanceOrder.query.count() > 0, "Maintenance orders should be populated"
            assert User.query.count() > 0, "Users should be populated"

            # Verify specific data exists
            assets = Asset.query.all()
            assert len(assets) > 0
            assert all(asset.name for asset in assets), "All assets should have names"
            assert all(asset.asset_code for asset in assets), "All assets should have asset codes"

            mos = MaintenanceOrder.query.all()
            assert len(mos) > 0
            assert all(mo.asset_id for mo in mos), "All MOs should be linked to assets"
            assert all(mo.description for mo in mos), "All MOs should have descriptions"

            users = User.query.all()
            assert len(users) > 0
            assert all(user.username for user in users), "All users should have usernames"

    def test_populate_dummy_data_idempotent(self, app, client):
        """
        Test that populate_dummy_data behavior with multiple calls.

        Note: The current implementation of populate_dummy_data() is NOT fully idempotent
        as it attempts to create duplicate roles/skills. This test verifies the actual
        behavior and ensures unique constraints are respected.

        Verifies:
        - First call succeeds and populates data
        - Second call raises IntegrityError due to unique constraints
        - This is expected behavior until populate_dummy_data is refactored
        """
        logger = logging.getLogger(__name__)

        with app.app_context():
            # First population should succeed
            populate_dummy_data(logger)

            # Get counts after first population
            asset_count_1 = Asset.query.count()
            mo_count_1 = MaintenanceOrder.query.count()
            user_count_1 = User.query.count()

            # Verify data was populated
            assert asset_count_1 > 0, "Assets should be populated after first call"
            assert mo_count_1 > 0, "MOs should be populated after first call"
            assert user_count_1 > 0, "Users should be populated after first call"

            # NOTE: Current implementation is NOT idempotent
            # Second call will raise IntegrityError on unique constraints
            # This is acceptable behavior for now - the function is meant to be
            # called once during initial setup, not repeatedly

            # Attempting second population will fail due to unique constraints
            from sqlalchemy.exc import IntegrityError
            with pytest.raises(IntegrityError):
                populate_dummy_data(logger)

            # After IntegrityError, we need to rollback the session
            db.session.rollback()

            # Verify original data is still intact (no partial commits)
            assert Asset.query.count() == asset_count_1, "Asset count should remain same after failed second call"

            # Verify unique constraints are enforced
            asset_codes = [asset.asset_code for asset in Asset.query.all()]
            assert len(asset_codes) == len(set(asset_codes)), "Asset codes should be unique"

            usernames = [user.username for user in User.query.all()]
            assert len(usernames) == len(set(usernames)), "Usernames should be unique"

    def test_database_models_relationships(self, app, client):
        """
        Test that model relationships work correctly.

        Verifies:
        - Asset can be created and saved
        - MaintenanceOrder can be linked to Asset
        - Relationship navigation works (asset.maintenance_orders, mo.asset)
        - Cascade behavior (if applicable)
        """
        with app.app_context():
            # Create an Asset
            asset = Asset(
                asset_code='TEST-001',
                name='Test Asset',
                description='Test Description',
                asset_type='Equipment',
                cost_center='Test Center',
                status='Operational'
            )
            db.session.add(asset)
            db.session.commit()

            # Verify asset was created
            assert asset.id is not None, "Asset should have an ID after commit"

            # Create a MaintenanceOrder linked to the Asset
            mo = MaintenanceOrder(
                asset_id=asset.id,
                description='Test Maintenance Order',
                order_type='PM',
                status='Open',
                priority='Medium',
                labour_count=1
            )
            db.session.add(mo)
            db.session.commit()

            # Verify MO was created
            assert mo.id is not None, "MO should have an ID after commit"
            assert mo.asset_id == asset.id, "MO should be linked to asset"

            # Test relationship navigation (MO -> Asset)
            assert mo.asset is not None, "MO should have asset relationship"
            assert mo.asset.id == asset.id, "MO.asset should point to correct asset"
            assert mo.asset.name == 'Test Asset', "Relationship should return correct asset"

            # Test relationship navigation (Asset -> MOs)
            assert len(asset.maintenance_orders) > 0, "Asset should have maintenance orders"
            assert asset.maintenance_orders[0].id == mo.id, "Asset.maintenance_orders should include our MO"

            # Test cascade behavior (delete asset should cascade to MOs if configured)
            asset_id = asset.id
            mo_id = mo.id

            db.session.delete(asset)
            db.session.commit()

            # Verify asset is deleted
            deleted_asset = Asset.query.get(asset_id)
            assert deleted_asset is None, "Asset should be deleted"

            # Verify cascade deletion of MO (if cascade is configured)
            deleted_mo = MaintenanceOrder.query.get(mo_id)
            assert deleted_mo is None, "MO should be cascade deleted with asset"

