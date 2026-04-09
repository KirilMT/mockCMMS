"""Centralized logging helpers for the collab utilities in `.collab/`.

This module configures a repository-scoped logs directory at `.collab/logs` and provides
an idempotent helper to wire FileHandlers and a console handler without producing
duplicate handlers when called multiple times (useful for import-time setup in CLI tools
and long-running daemons).
"""

from __future__ import annotations

import logging
import os
from typing import Optional

DEFAULT_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        # Best-effort: if we cannot create a logs directory, don't raise here
        # to avoid breaking CLI entrypoints. Upstream callers will still see
        # console output.
        pass


def setup_collab_logging(
    collab_dir: Optional[str] = None, *, level: int = logging.INFO
) -> logging.Logger:
    """Configure logging for the collab tooling.

    - collab_dir: path to the `.collab` directory. If omitted, current working
      directory is used and a `logs/` subdir is created there.
    - level: root logger level (defaults to INFO).

    The function is idempotent: calling it multiple times will not attach
    duplicate handlers.
    Returns the root logger instance.
    """
    # All logs live in the standard .collab/logs/ directory.
    # We no longer support COLLAB_LOG_DIR override for external directories
    # to maintain the standard requested by the user.
    if collab_dir:
        base = collab_dir
    else:
        # Resolve project root relative to this file
        base = os.path.dirname(os.path.abspath(__file__))

    log_dir = os.path.join(base, "logs")
    _ensure_dir(log_dir)

    root = logging.getLogger()
    root.setLevel(level)

    # Simple console handler: keep when not present on the root logger
    console_present = any(type(h).__name__ == "StreamHandler" for h in root.handlers)
    if not console_present:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATEFMT))
        root.addHandler(ch)

    # Configure a dedicated 'collab' logger for file-based logging. This
    # prevents unrelated libraries or the application root logger from
    # polluting the .collab/logs files. Handlers are attached to the
    # 'collab' logger (and not to the root logger) so only logs emitted by
    # 'collab' namespace (e.g. "collab.lock_client", "collab.pycharm_watcher")
    # are written to application.log / errors.log.
    collab_logger = logging.getLogger("collab")
    collab_logger.setLevel(level)
    # Allow records to propagate so test harnesses (caplog) and the root
    # console handler can observe collab log records. FileHandlers are
    # attached directly to the collab logger so only collab.* records are
    # written to .collab/logs; other libraries will not be recorded there.
    collab_logger.propagate = True

    # File handlers: application.log (INFO+) and errors.log (ERROR+)
    # In test mode, we use distinct filenames to avoid Windows file locks
    # if the live daemon is running concurrently.
    if os.getenv("COLLAB_TEST_MODE") == "1":
        app_name, err_name = "test_application.log", "test_errors.log"
    else:
        app_name, err_name = "application.log", "errors.log"

    app_path = os.path.join(log_dir, app_name)
    err_path = os.path.join(log_dir, err_name)

    def _has_filehandler_for(logger_obj: logging.Logger, path: str) -> bool:
        for h in getattr(logger_obj, "handlers", []):
            if getattr(h, "baseFilename", None) == os.path.abspath(path):
                return True
        return False

    # Remove stale file handlers that point to the *other* file set.
    # This can happen when setup_collab_logging is called before and after
    # COLLAB_TEST_MODE changes (e.g. module-level import then conftest).
    _stale = []
    for h in list(collab_logger.handlers):
        bf = getattr(h, "baseFilename", None)
        if bf and bf.startswith(os.path.abspath(log_dir)):
            if bf not in (os.path.abspath(app_path), os.path.abspath(err_path)):
                _stale.append(h)
    for h in _stale:
        collab_logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass

    if not _has_filehandler_for(collab_logger, app_path):
        try:
            fh = logging.FileHandler(app_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATEFMT))
            collab_logger.addHandler(fh)
        except Exception:
            # Best-effort: if file can't be opened, continue with console-only
            pass

    if not _has_filehandler_for(collab_logger, err_path):
        try:
            eh = logging.FileHandler(err_path, encoding="utf-8")
            eh.setLevel(logging.ERROR)
            eh.setFormatter(logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATEFMT))
            collab_logger.addHandler(eh)
        except Exception:
            pass

    # Return the root logger for convenience (callers typically ignore return)
    return root
