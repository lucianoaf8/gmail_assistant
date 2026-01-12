"""Command Line Interface for Gmail Assistant."""
from __future__ import annotations

from gmail_assistant.cli.main import main

# H-10: Export UI abstraction classes
from gmail_assistant.cli.ui import (
    ProgressReporter,
    ClickProgressReporter,
    RichProgressReporter,
    SilentProgressReporter,
    LoggingProgressReporter,
    UserConfirmation,
    ClickConfirmation,
    AutoConfirmation,
    MessageOutput,
    ClickMessageOutput,
    SilentMessageOutput,
    get_progress_reporter,
    get_confirmation,
    get_message_output,
)

__all__ = [
    "main",
    # Progress reporting
    "ProgressReporter",
    "ClickProgressReporter",
    "RichProgressReporter",
    "SilentProgressReporter",
    "LoggingProgressReporter",
    # User confirmation
    "UserConfirmation",
    "ClickConfirmation",
    "AutoConfirmation",
    # Message output
    "MessageOutput",
    "ClickMessageOutput",
    "SilentMessageOutput",
    # Factory functions
    "get_progress_reporter",
    "get_confirmation",
    "get_message_output",
]
