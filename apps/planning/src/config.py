import os
import secrets

SRC_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SRC_DIR, ".."))
# PROJECT_ROOT is 3 levels up from apps/planning/src
PROJECT_ROOT = os.path.abspath(os.path.join(SRC_DIR, "..", "..", ".."))
INSTANCE_DIR = os.path.join(PROJECT_ROOT, "instance")


class Config:
    """Application configuration class with environment variable support.

    This class centralizes all configuration settings and provides secure defaults for
    development while requiring proper configuration for production.
    """

    # --- Core Secrets / Flags ---
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # Data source for task data: 'excel' (default) or 'api'
    DATA_SOURCE = os.environ.get("DATA_SOURCE", "excel").lower()

    # Global debug mode toggle (string env values '1', 'true', 'True')
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Optional separate flag just to force using test DB
    # without enabling all debug behaviors
    DEBUG_USE_TEST_DB = os.environ.get("PLANNING_DEBUG_USE_TEST_DB", "0").lower() in (
        "1",
        "true",
        "yes",
    )

    # Optional fixed date (ISO formats e.g. '2025-04-19' or '2025-04-19T16:00:00')
    # used by services when FLASK_DEBUG active
    DEBUG_FIXED_DATE = os.environ.get("DEBUG_FIXED_DATE")  # parsed lazily where needed

    # --- Flask-WTF Configuration ---
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(
        os.environ.get("CSRF_TIME_LIMIT", "3600")
    )  # 1 hour default
    WTF_CSRF_SSL_STRICT = not FLASK_DEBUG  # Disable SSL requirement in debug mode

    # --- Security Configuration ---
    PERMANENT_SESSION_LIFETIME = int(
        os.environ.get("SESSION_LIFETIME", "1800")
    )  # 30 minutes default
    SESSION_COOKIE_SECURE = (
        not FLASK_DEBUG
    )  # Only send cookies over HTTPS in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- Database Configuration ---
    # Determine the database filename based on environment settings.
    # Priority:
    # 1. DATABASE_FILENAME environment variable (for explicit override).
    # 2. 'planning_test.db' if in debug mode or if test DB is forced.
    # 3. 'planning.db' as the default production database.
    if "DATABASE_FILENAME" in os.environ:
        _db_filename = os.environ["DATABASE_FILENAME"]
    elif os.environ.get("TESTING", "0").lower() in ("1", "true", "yes"):
        # Critical: Use in-memory DB by default during testing to prevent
        # file persistence
        _db_filename = ":memory:"
    elif FLASK_DEBUG or DEBUG_USE_TEST_DB:
        _db_filename = "planning_test.db"
    else:
        _db_filename = "planning.db"

    # The database is located in the instance directory.
    # Logic for :memory: needs to handle the path join gracefully
    if _db_filename == ":memory:":
        DATABASE_PATH = ":memory:"
    else:
        DATABASE_PATH = os.path.join(INSTANCE_DIR, _db_filename)

    # --- SQLAlchemy Configuration ---
    # Planning App uses 'planning' bind for its own tables
    # and default for shared core tables.
    # NOTE: SQLALCHEMY_DATABASE_URI should be provided by the main app factory.
    # This default is only used if planning app runs standalone (which it shouldn't).
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_BINDS = {"planning": f"sqlite:///{DATABASE_PATH}"}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Paths ---
    OUTPUT_FOLDER = os.path.join(ROOT_DIR, "output")
    TEMPLATES_FOLDER = os.path.join(SRC_DIR, "templates")
    STATIC_FOLDER = os.path.join(SRC_DIR, "static")

    # File upload restrictions
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_UPLOAD_SIZE", "16777216")
    )  # 16MB default
    ALLOWED_EXTENSIONS = {"xlsx", "xls", "xlsb", "csv"}

    # NOTE: Directories are created lazily by the app factory, not at import time.
    # This prevents test imports from creating directories.
    # os.makedirs(INSTANCE_DIR, exist_ok=True)
    # os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    @classmethod
    def is_debug(cls):
        """Check if application is in debug mode."""
        return cls.FLASK_DEBUG

    @classmethod
    def get_fixed_datetime(cls):
        """Return a datetime override if FLASK_DEBUG and a fixed date is set; else None.

        If DEBUG_FIXED_DATE not set but FLASK_DEBUG is true, returns canonical test
        date.
        """
        if not cls.FLASK_DEBUG:
            return None
        from datetime import datetime

        if cls.DEBUG_FIXED_DATE:
            try:
                return datetime.fromisoformat(cls.DEBUG_FIXED_DATE)
            except ValueError:
                # Fall back to canonical date if parse fails
                pass
        # Canonical fallback debug date/time
        return datetime(2025, 4, 19, 16, 0, 0)

    @classmethod
    def validate_config(cls):
        """Validate critical configuration settings."""
        errors = []

        # Check if SECRET_KEY is properly set in production
        if not cls.FLASK_DEBUG and cls.SECRET_KEY == secrets.token_hex(32):
            errors.append("SECRET_KEY should be explicitly set in production")

        # Validate file upload size
        if cls.MAX_CONTENT_LENGTH > 50 * 1024 * 1024:  # 50MB
            errors.append("MAX_CONTENT_LENGTH seems too large (>50MB)")

        # Check database path accessibility
        # Skip this check in debug/testing mode to allow for lazy directory creation
        # or in-memory databases.
        is_testing = (
            os.environ.get("TESTING") == "1" or cls.DEBUG_USE_TEST_DB or cls.FLASK_DEBUG
        )
        if not is_testing:
            db_dir = os.path.dirname(cls.DATABASE_PATH)
            if not os.path.exists(db_dir):
                errors.append(f"Database directory does not exist: {db_dir}")

        if errors:
            raise ValueError(
                "Configuration validation failed:\n"
                + "\n".join(f"- {error}" for error in errors)
            )
