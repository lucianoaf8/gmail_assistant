"""
Output format plugins for Gmail Assistant (M-1 refactoring).

This module provides a plugin architecture for email output formats,
extracting output responsibilities from GmailFetcher.

Usage:
    from gmail_assistant.core.output import OutputPluginManager, EMLPlugin, MarkdownPlugin

    manager = OutputPluginManager()
    manager.register(EMLPlugin())
    manager.register(MarkdownPlugin())

    manager.save(email_data, output_dir, format='eml')
"""

from .plugin_manager import (
    EMLPlugin,
    JSONPlugin,
    MarkdownPlugin,
    OutputPlugin,
    OutputPluginManager,
)

__all__ = [
    'EMLPlugin',
    'JSONPlugin',
    'MarkdownPlugin',
    'OutputPlugin',
    'OutputPluginManager',
]
