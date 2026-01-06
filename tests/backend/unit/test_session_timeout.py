from datetime import datetime, timedelta, timezone


class TestSessionTimeout:
    """Test suite for session timeout logic in app.py."""

    def test_session_valid(self, client, sample_user):
        """Test that a valid session is maintained."""
        with client.session_transaction() as sess:
            sess["user_id"] = sample_user.id
            sess["username"] = sample_user.username
            sess["last_active"] = datetime.now(timezone.utc).timestamp()

        # Access a protected route
        response = client.get("/assets")
        assert response.status_code == 200

        # Verify last_active was updated
        with client.session_transaction() as sess:
            assert sess["last_active"] is not None

    def test_session_missing_timestamp(self, client, sample_user):
        """Test that a session without last_active timestamp is invalidated."""
        with client.session_transaction() as sess:
            sess["user_id"] = sample_user.id
            sess["username"] = sample_user.username
            # Deliberately NOT setting last_active

        # Access a protected route
        response = client.get("/assets")

        # Should be redirected to login
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

        # Verify session was cleared
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_session_expired(self, client, sample_user):
        """Test that an expired session is invalidated."""
        # 31 minutes ago
        expired_time = (datetime.now(timezone.utc) - timedelta(minutes=31)).timestamp()

        with client.session_transaction() as sess:
            sess["user_id"] = sample_user.id
            sess["username"] = sample_user.username
            sess["last_active"] = expired_time

        # Access a protected route
        response = client.get("/assets")

        # Should be redirected to login
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

        # Verify session was cleared
        with client.session_transaction() as sess:
            assert "user_id" not in sess
