"""Tests for AssignmentStrategy._log method edge cases.

Covers the uncovered print branch (lines 19-22) and other edge cases in
assignment_strategy.py.
"""

from unittest.mock import MagicMock

from apps.planning.src.services.strategies.assignment_strategy import AssignmentStrategy


class ConcreteStrategy(AssignmentStrategy):
    """Concrete implementation for testing the abstract base class."""

    def assign_task(self, context: dict) -> dict:
        return {}


class TestAssignmentStrategyLog:
    """Tests for _log method in AssignmentStrategy."""

    def test_log_info(self):
        """Test _log with info level."""
        logger = MagicMock()
        strategy = ConcreteStrategy(logger=logger)
        strategy._log("info", "test message")
        logger.info.assert_called_once_with("test message")

    def test_log_debug(self):
        """Test _log with debug level."""
        logger = MagicMock()
        strategy = ConcreteStrategy(logger=logger)
        strategy._log("debug", "debug msg")
        logger.debug.assert_called_once_with("debug msg")

    def test_log_warning(self):
        """Test _log with warning level."""
        logger = MagicMock()
        strategy = ConcreteStrategy(logger=logger)
        strategy._log("warning", "warning msg")
        logger.warning.assert_called_once_with("warning msg")

    def test_log_error(self):
        """Test _log with error level."""
        logger = MagicMock()
        strategy = ConcreteStrategy(logger=logger)
        strategy._log("error", "error msg")
        logger.error.assert_called_once_with("error msg")

    def test_log_unknown_level_falls_to_print(self, capsys):
        """Test _log with unknown level falls through to print (line 22)."""
        logger = MagicMock()
        strategy = ConcreteStrategy(logger=logger)
        strategy._log("critical", "critical msg")
        captured = capsys.readouterr()
        assert "[CRITICAL] critical msg" in captured.out

    def test_log_unknown_level_with_args(self, capsys):
        """Test _log with unknown level and format args."""
        logger = MagicMock()
        strategy = ConcreteStrategy(logger=logger)
        strategy._log("trace", "msg %s %d", "hello", 42)
        captured = capsys.readouterr()
        assert "[TRACE] msg hello 42" in captured.out

    def test_default_logger(self):
        """Test that default logger is created when none provided."""
        strategy = ConcreteStrategy()
        assert strategy.logger is not None
        strategy._log("info", "using default logger")
