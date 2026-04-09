import atexit
import os
import shutil
import sys
import tempfile

# ============================================================================
# EARLY ISOLATION (MUST HAPPEN BEFORE TEST COLLECTION)
# ============================================================================
# Pytest imports test modules during the test collection phase, which happens
# *before* session-scoped fixtures execute. Since lock_client and watcher
# modules eagerly evaluate os.getenv("COLLAB_PID_FILE") at module load time,
# we MUST set test isolation variables at the top level of this file.

_session_temp_dir = tempfile.mkdtemp(prefix="collab_test_")

os.environ["COLLAB_PID_FILE"] = os.path.join(_session_temp_dir, "daemon.pid")
os.environ["COLLAB_TEST_MODE"] = "1"

# We intentionally mock these at the top level for tests to avoid hitting
# real endpoints if _get_create_client fallback triggers early.
os.environ.setdefault("SUPABASE_URL", "http://localhost:99999")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")


def _cleanup_session_temp():
    try:
        shutil.rmtree(_session_temp_dir)
    except Exception:
        pass


# Ensure test mode is explicitly kept, do not clear it, so late-firing
# atexit hooks attached to test processes still skip network calls.
atexit.register(_cleanup_session_temp)

# ============================================================================
# MOCKS & FIXTURES
# ============================================================================


class FakeNotification:
    def notify(self, **kwargs):
        pass


class FakePlyer:
    notification = FakeNotification()


sys.modules["plyer"] = FakePlyer()  # type: ignore[assignment]
