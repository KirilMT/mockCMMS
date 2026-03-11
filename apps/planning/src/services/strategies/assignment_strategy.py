import logging
from abc import ABC, abstractmethod


class AssignmentStrategy(ABC):
    """Abstract base class for task assignment strategies."""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def _log(self, level, message, *args):
        """Helper to log messages."""
        if level == "info":
            self.logger.info(message, *args)
        elif level == "debug":
            self.logger.debug(message, *args)
        elif level == "warning":
            self.logger.warning(message, *args)
        elif level == "error":
            self.logger.error(message, *args)
        else:
            print(f"[{level.upper()}] {message % args if args else message}")

    @abstractmethod
    def assign_task(self, context: dict) -> dict:
        """Assigns a task based on the strategy logic.

        Args:
            context: A dictionary containing all necessary data for assignment
                     (task_definition, technicians, schedules, configuration, etc.)

        Returns:
            A dictionary containing assignment results to be merged into
            the main schedule.
        """
        pass
