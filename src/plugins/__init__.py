"""
Plugin System for Gmail Fetcher.

This package provides an extensible plugin architecture for:
- Output formats (EML, Markdown, JSON)
- File organization strategies (by date, sender, none)
- Email filters (search, classification)

Usage:
    from src.plugins import PluginRegistry, get_default_registry

    # Get default registry with all plugins
    registry = get_default_registry()

    # Get specific plugin
    markdown_plugin = registry.get_output("markdown")

    # List available plugins
    outputs = registry.list_outputs()
"""

from .base import (
    OutputPlugin,
    OrganizationPlugin,
    FilterPlugin,
    PluginError,
)
from .registry import (
    PluginRegistry,
    get_default_registry,
)

__all__ = [
    # Base classes
    "OutputPlugin",
    "OrganizationPlugin",
    "FilterPlugin",
    "PluginError",
    # Registry
    "PluginRegistry",
    "get_default_registry",
]
