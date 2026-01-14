"""
UI abstraction for CLI output (H-10 fix).

Separates presentation from business logic.
Provides abstract interfaces for progress reporting and user confirmation.
"""

from abc import ABC, abstractmethod
from typing import Any


class ProgressReporter(ABC):
    """Abstract progress reporting interface."""

    @abstractmethod
    def start(self, total: int, description: str) -> None:
        """Start progress tracking."""
        pass

    @abstractmethod
    def update(self, amount: int = 1) -> None:
        """Update progress."""
        pass

    @abstractmethod
    def finish(self) -> None:
        """Complete progress tracking."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.finish()
        return False


class ClickProgressReporter(ProgressReporter):
    """Click-based progress bar implementation."""

    def __init__(self):
        self._bar = None
        self._ctx = None

    def start(self, total: int, description: str) -> None:
        import click
        self._bar = click.progressbar(
            length=total,
            label=description,
            show_eta=True,
            show_percent=True
        )
        self._ctx = self._bar.__enter__()

    def update(self, amount: int = 1) -> None:
        if self._bar:
            self._bar.update(amount)

    def finish(self) -> None:
        if self._bar:
            self._bar.__exit__(None, None, None)
            self._bar = None
            self._ctx = None


class RichProgressReporter(ProgressReporter):
    """Rich-based progress bar implementation (optional dependency)."""

    def __init__(self):
        self._progress = None
        self._task_id = None

    def start(self, total: int, description: str) -> None:
        try:
            from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            )
            self._progress.start()
            self._task_id = self._progress.add_task(description, total=total)
        except ImportError:
            # Fall back to silent if rich not available
            pass

    def update(self, amount: int = 1) -> None:
        if self._progress and self._task_id is not None:
            self._progress.update(self._task_id, advance=amount)

    def finish(self) -> None:
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._task_id = None


class SilentProgressReporter(ProgressReporter):
    """No-op progress reporter for non-interactive use."""

    def start(self, total: int, description: str) -> None:
        pass

    def update(self, amount: int = 1) -> None:
        pass

    def finish(self) -> None:
        pass


class LoggingProgressReporter(ProgressReporter):
    """Progress reporter that logs to a logger."""

    def __init__(self, logger=None):
        import logging
        self._logger = logger or logging.getLogger(__name__)
        self._total = 0
        self._current = 0
        self._description = ""

    def start(self, total: int, description: str) -> None:
        self._total = total
        self._current = 0
        self._description = description
        self._logger.info(f"Starting: {description} (total: {total})")

    def update(self, amount: int = 1) -> None:
        self._current += amount
        if self._total > 0:
            pct = (self._current / self._total) * 100
            self._logger.debug(f"{self._description}: {self._current}/{self._total} ({pct:.1f}%)")

    def finish(self) -> None:
        self._logger.info(f"Completed: {self._description} ({self._current} items)")


class UserConfirmation(ABC):
    """Abstract user confirmation interface."""

    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask user for confirmation."""
        pass

    @abstractmethod
    def prompt(self, message: str, default: str = "") -> str:
        """Prompt user for input."""
        pass


class ClickConfirmation(UserConfirmation):
    """Click-based user confirmation."""

    def confirm(self, message: str, default: bool = False) -> bool:
        import click
        return click.confirm(message, default=default)

    def prompt(self, message: str, default: str = "") -> str:
        import click
        return click.prompt(message, default=default)


class AutoConfirmation(UserConfirmation):
    """Auto-confirm for non-interactive/testing."""

    def __init__(self, confirm_response: bool = True, prompt_response: str = ""):
        self._confirm_response = confirm_response
        self._prompt_response = prompt_response

    def confirm(self, message: str, default: bool = False) -> bool:
        return self._confirm_response

    def prompt(self, message: str, default: str = "") -> str:
        return self._prompt_response or default


class MessageOutput(ABC):
    """Abstract message output interface."""

    @abstractmethod
    def info(self, message: str) -> None:
        """Display info message."""
        pass

    @abstractmethod
    def success(self, message: str) -> None:
        """Display success message."""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Display warning message."""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """Display error message."""
        pass


class ClickMessageOutput(MessageOutput):
    """Click-based message output."""

    def info(self, message: str) -> None:
        import click
        click.echo(message)

    def success(self, message: str) -> None:
        import click
        click.secho(message, fg='green')

    def warning(self, message: str) -> None:
        import click
        click.secho(f"Warning: {message}", fg='yellow', err=True)

    def error(self, message: str) -> None:
        import click
        click.secho(f"Error: {message}", fg='red', err=True)


class SilentMessageOutput(MessageOutput):
    """Silent message output for testing."""

    def __init__(self):
        self.messages: list[tuple[str, str]] = []

    def info(self, message: str) -> None:
        self.messages.append(('info', message))

    def success(self, message: str) -> None:
        self.messages.append(('success', message))

    def warning(self, message: str) -> None:
        self.messages.append(('warning', message))

    def error(self, message: str) -> None:
        self.messages.append(('error', message))


def get_progress_reporter(interactive: bool = True, use_rich: bool = False) -> ProgressReporter:
    """Factory function to get appropriate progress reporter."""
    if not interactive:
        return SilentProgressReporter()
    if use_rich:
        try:
            import rich  # noqa: F401
            return RichProgressReporter()
        except ImportError:
            pass
    return ClickProgressReporter()


def get_confirmation(interactive: bool = True) -> UserConfirmation:
    """Factory function to get appropriate confirmation handler."""
    if interactive:
        return ClickConfirmation()
    return AutoConfirmation()


def get_message_output(interactive: bool = True) -> MessageOutput:
    """Factory function to get appropriate message output."""
    if interactive:
        return ClickMessageOutput()
    return SilentMessageOutput()
