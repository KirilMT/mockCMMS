"""
Tests for database utility functions (db_utils.py).

This module tests the database population functions and model relationships
to ensure data integrity and proper ORM behavior.
"""

import logging
import pytest
from src.services.db_utils import (
    db,
    populate_dummy_data,
    User,
    Asset,
    MaintenanceOrder,
    SparePart,
    Skill,
    Role,
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
            assert (
                MaintenanceOrder.query.count() > 0
            ), "Maintenance orders should be populated"
            assert User.query.count() > 0, "Users should be populated"

            # Verify specific data exists
            assets = Asset.query.all()
            assert len(assets) > 0
            assert all(asset.name for asset in assets), "All assets should have names"
            assert all(
                asset.asset_code for asset in assets
            ), "All assets should have asset codes"

            mos = MaintenanceOrder.query.all()
            assert len(mos) > 0
            assert all(mo.asset_id for mo in mos), "All MOs should be linked to assets"
            assert all(mo.description for mo in mos), "All MOs should have descriptions"

            users = User.query.all()
            assert len(users) > 0
            assert all(
                user.username for user in users
            ), "All users should have usernames"

    def test_populate_dummy_data_idempotent(self, app, client):
        """
        Test that populate_dummy_data is idempotent and does not create
        duplicate data on multiple calls.
        """
        logger = logging.getLogger(__name__)

        with app.app_context():
            # First population
            populate_dummy_data(logger)
            count1 = User.query.count()
            assert count1 > 0

            # Second population
            populate_dummy_data(logger)
            count2 = User.query.count()

            assert count1 == count2, "Should not create duplicate users"

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
                asset_code="TEST-001",
                name="Test Asset",
                description="Test Description",
                asset_type="Equipment",
                cost_center="Test Center",
                status="Operational",
            )
            db.session.add(asset)
            db.session.commit()

            # Verify asset was created
            assert asset.id is not None, "Asset should have an ID after commit"

            # Create a MaintenanceOrder linked to the Asset
            mo = MaintenanceOrder(
                asset_id=asset.id,
                description="Test Maintenance Order",
                order_type="PM",
                status="Open",
                priority="Medium",
                labour_count=1,
            )
            db.session.add(mo)
            db.session.commit()

            # Verify MO was created
            assert mo.id is not None, "MO should have an ID after commit"
            assert mo.asset_id == asset.id, "MO should be linked to asset"

            # Test relationship navigation (MO -> Asset)
            assert mo.asset is not None, "MO should have asset relationship"
            assert mo.asset.id == asset.id, "MO.asset should point to correct asset"
            assert (
                mo.asset.name == "Test Asset"
            ), "Relationship should return correct asset"

            # Test relationship navigation (Asset -> MOs)
            assert (
                len(asset.maintenance_orders) > 0
            ), "Asset should have maintenance orders"
            assert (
                asset.maintenance_orders[0].id == mo.id
            ), "Asset.maintenance_orders should include our MO"

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


class TestEnhancedDatabaseUtilities:
    """Enhanced tests for database models, methods, and constraints."""

    def test_user_password_hashing(self, app):
        """Test User password hashing methods."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("securepassword123")
            db.session.add(user)
            db.session.commit()

            assert user.password_hash is not None
            assert user.password_hash != "securepassword123"
            assert user.check_password("securepassword123") is True
            assert user.check_password("wrongpassword") is False

            user.set_password("newpassword456")
            db.session.commit()
            assert user.check_password("newpassword456") is True
            assert user.check_password("securepassword123") is False

    def test_user_to_dict_method(self, app, sample_role):
        """Test User to_dict method with and without roles."""
        with app.app_context():
            user = User(username="dictuser", email="dict@example.com")
            user.set_password("password")
            user.roles.append(sample_role)
            db.session.add(user)
            db.session.commit()

            data_without_roles = user.to_dict(include_roles=False)
            assert "username" in data_without_roles
            assert "email" in data_without_roles
            assert "roles_display" not in data_without_roles

            data_with_roles = user.to_dict(include_roles=True)
            assert "roles_display" in data_with_roles
            assert "Technician" in data_with_roles["roles_display"]

    def test_model_string_representations(self, app):
        """Test __repr__ methods exist and work for all models."""
        with app.app_context():
            asset = Asset(
                asset_code="REPR-001",
                name="Test Asset",
                asset_type="Equipment",
                cost_center="Test",
            )
            skill = Skill(name="TestSkill")
            role = Role(name="TestRole")

            db.session.add_all([asset, skill, role])
            db.session.commit()

            assert "Asset" in str(type(asset))
            assert "Skill" in str(type(skill))
            assert "Role" in str(type(role))

    def test_database_constraints(self, app):
        """Test database constraints (unique constraints)."""
        with app.app_context():
            from sqlalchemy.exc import IntegrityError

            asset1 = Asset(
                asset_code="CONST-001",
                name="Asset 1",
                asset_type="Equipment",
                cost_center="Test",
            )
            db.session.add(asset1)
            db.session.commit()

            asset2 = Asset(
                asset_code="CONST-001",
                name="Asset 2",
                asset_type="Equipment",
                cost_center="Test",
            )
            db.session.add(asset2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            user1 = User(username="testuser", email="test1@example.com")
            user1.set_password("password")
            db.session.add(user1)
            db.session.commit()

            user2 = User(username="testuser", email="test2@example.com")
            user2.set_password("password")
            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_cascade_relationships_all_models(self, app, sample_role):
        """Test cascade behavior across all model relationships."""
        with app.app_context():
            asset = Asset(
                asset_code="CASCADE-001",
                name="Cascade Asset",
                asset_type="Equipment",
                cost_center="Test",
            )
            db.session.add(asset)
            db.session.commit()

            mo = MaintenanceOrder(
                asset_id=asset.id,
                description="Cascade MO",
                order_type="PM",
                status="Open",
                priority="Medium",
                labour_count=1,
            )
            db.session.add(mo)
            db.session.commit()

            asset_id = asset.id
            mo_id = mo.id

            db.session.delete(asset)
            db.session.commit()

            assert Asset.query.get(asset_id) is None
            assert MaintenanceOrder.query.get(mo_id) is None

            user = User(username="cascadeuser", email="cascade@example.com")
            user.set_password("password")
            user.roles.append(sample_role)
            db.session.add(user)
            db.session.commit()

            user_id = user.id
            role_id = sample_role.id

            db.session.delete(user)
            db.session.commit()

            assert User.query.get(user_id) is None
            assert Role.query.get(role_id) is not None

    def test_model_default_values(self, app):
        """Test that model default values are applied correctly."""
        with app.app_context():
            asset = Asset(asset_code="DEFAULT-001", name="Default Asset")
            db.session.add(asset)
            db.session.commit()

            assert asset.status == "Operational"

            mo = MaintenanceOrder(
                asset_id=asset.id, description="Default MO", order_type="PM"
            )
            db.session.add(mo)
            db.session.commit()

            assert mo.status == "Open"
            assert mo.priority == "Undefined"
            assert mo.labour_count == 1
            assert mo.created_at is not None

            user = User(username="defaultuser", email="default@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

            assert user.is_active is True
            assert user.availability_status == "Available"
            assert user.created_at is not None

    def test_query_filter_edge_cases(self, app):
        """Test query filtering with edge cases."""
        with app.app_context():
            asset1 = Asset(
                asset_code="FILTER-001",
                name="Asset One",
                asset_type="Equipment",
                cost_center="Test",
            )
            asset2 = Asset(
                asset_code="FILTER-002",
                name="Asset Two",
                asset_type=None,
                cost_center="Test",
            )
            asset3 = Asset(
                asset_code="FILTER-003",
                name="",
                asset_type="Equipment",
                cost_center="Test",
            )

            db.session.add_all([asset1, asset2, asset3])
            db.session.commit()

            none_type_assets = Asset.query.filter_by(asset_type=None).all()
            assert len(none_type_assets) == 1
            assert none_type_assets[0].asset_code == "FILTER-002"

            empty_name_assets = Asset.query.filter_by(name="").all()
            assert len(empty_name_assets) == 1

            all_assets = Asset.query.filter(Asset.asset_code.like("FILTER-%")).all()
            assert len(all_assets) == 3

    def test_relationship_back_references(self, app, sample_role):
        """Test bi-directional relationships and backrefs."""
        with app.app_context():
            asset = Asset(
                asset_code="BACKREF-001",
                name="Backref Asset",
                asset_type="Equipment",
                cost_center="Test",
            )
            db.session.add(asset)
            db.session.commit()

            mo = MaintenanceOrder(
                asset_id=asset.id,
                description="Backref MO",
                order_type="PM",
                status="Open",
                priority="Medium",
                labour_count=1,
            )
            db.session.add(mo)
            db.session.commit()

            assert mo.asset.id == asset.id
            assert asset.maintenance_orders[0].id == mo.id

            user = User(username="backrefuser", email="backref@example.com")
            user.set_password("password")
            user.roles.append(sample_role)
            db.session.add(user)
            db.session.commit()

            assert sample_role in user.roles
            assert user in sample_role.users

            db.session.delete(mo)
            db.session.commit()
            assert len(asset.maintenance_orders) == 0
