import logging

from src.services.db_seeding import populate_dummy_data
from src.services.db_utils import Asset, Role, User


class TestDBSeeding:
    def test_populate_dummy_data(self, app):
        """Test full population of dummy data."""
        with app.app_context():
            # Ensure DB is empty start
            # app fixture should provide clean DB, but let's double check or clear?
            # User.query.delete() might be needed if side effects.
            # But we added cleanup in conftest.py (hopefully).

            # populate_dummy_data checks if data exists (Role/User).
            # If empty, it loads.
            logger = logging.getLogger("test_seeding")
            populate_dummy_data(logger)

            # Verify data exists
            assert Role.query.count() > 0
            assert User.query.count() > 0
            assert Asset.query.count() > 0
            # Check for dummy data specifics (optional)

    def test_populate_idempotency(self, app):
        """Test that populate doesn't duplicate if run twice."""
        with app.app_context():
            logger = logging.getLogger("test_seeding_idem")
            populate_dummy_data(logger)
            c1 = User.query.count()

            # Run again
            populate_dummy_data(logger)
            c2 = User.query.count()

            assert c1 == c2
