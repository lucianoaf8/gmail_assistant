"""
Plugin Registry for Gmail Fetcher.

Central registry for discovering, registering, and accessing plugins.
"""

import logging
from typing import Dict, List, Optional, Type, Callable
from .base import (
    BasePlugin,
    OutputPlugin,
    OrganizationPlugin,
    FilterPlugin,
    PluginNotFoundError,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all Gmail Fetcher plugins.

    The registry manages plugin discovery, registration, and retrieval
    for output formats, organization strategies, and filters.

    Example:
        registry = PluginRegistry()

        # Register plugins
        registry.register_output(MarkdownPlugin())
        registry.register_organization(ByDatePlugin())
        registry.register_filter(UnreadFilter())

        # Get plugins
        md = registry.get_output("markdown")
        by_date = registry.get_organization("by_date")

        # List available plugins
        outputs = registry.list_outputs()
    """

    def __init__(self):
        self._output_plugins: Dict[str, OutputPlugin] = {}
        self._organization_plugins: Dict[str, OrganizationPlugin] = {}
        self._filter_plugins: Dict[str, FilterPlugin] = {}

    # =========================================================================
    # Output Plugin Management
    # =========================================================================

    def register_output(self, plugin: OutputPlugin) -> None:
        """
        Register an output format plugin.

        Args:
            plugin: OutputPlugin instance

        Raises:
            ValueError: If plugin name is already registered
        """
        if plugin.name in self._output_plugins:
            logger.warning(f"Overwriting output plugin: {plugin.name}")

        self._output_plugins[plugin.name] = plugin
        logger.debug(f"Registered output plugin: {plugin.name}")

    def get_output(self, name: str) -> OutputPlugin:
        """
        Get an output plugin by name.

        Args:
            name: Plugin name

        Returns:
            OutputPlugin instance

        Raises:
            PluginNotFoundError: If plugin not found
        """
        if name not in self._output_plugins:
            available = ", ".join(self._output_plugins.keys())
            raise PluginNotFoundError(
                f"Output plugin '{name}' not found. Available: {available}"
            )
        return self._output_plugins[name]

    def list_outputs(self) -> List[str]:
        """
        List all registered output plugin names.

        Returns:
            List of plugin names
        """
        return list(self._output_plugins.keys())

    def get_output_info(self) -> List[Dict[str, str]]:
        """
        Get information about all output plugins.

        Returns:
            List of plugin info dictionaries
        """
        return [
            {
                "name": plugin.name,
                "extension": plugin.extension,
                "description": plugin.description,
                "version": plugin.version,
            }
            for plugin in self._output_plugins.values()
        ]

    # =========================================================================
    # Organization Plugin Management
    # =========================================================================

    def register_organization(self, plugin: OrganizationPlugin) -> None:
        """
        Register an organization strategy plugin.

        Args:
            plugin: OrganizationPlugin instance
        """
        if plugin.name in self._organization_plugins:
            logger.warning(f"Overwriting organization plugin: {plugin.name}")

        self._organization_plugins[plugin.name] = plugin
        logger.debug(f"Registered organization plugin: {plugin.name}")

    def get_organization(self, name: str) -> OrganizationPlugin:
        """
        Get an organization plugin by name.

        Args:
            name: Plugin name

        Returns:
            OrganizationPlugin instance

        Raises:
            PluginNotFoundError: If plugin not found
        """
        if name not in self._organization_plugins:
            available = ", ".join(self._organization_plugins.keys())
            raise PluginNotFoundError(
                f"Organization plugin '{name}' not found. Available: {available}"
            )
        return self._organization_plugins[name]

    def list_organizations(self) -> List[str]:
        """
        List all registered organization plugin names.

        Returns:
            List of plugin names
        """
        return list(self._organization_plugins.keys())

    def get_organization_info(self) -> List[Dict[str, str]]:
        """
        Get information about all organization plugins.

        Returns:
            List of plugin info dictionaries
        """
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
            }
            for plugin in self._organization_plugins.values()
        ]

    # =========================================================================
    # Filter Plugin Management
    # =========================================================================

    def register_filter(self, plugin: FilterPlugin) -> None:
        """
        Register a filter plugin.

        Args:
            plugin: FilterPlugin instance
        """
        if plugin.name in self._filter_plugins:
            logger.warning(f"Overwriting filter plugin: {plugin.name}")

        self._filter_plugins[plugin.name] = plugin
        logger.debug(f"Registered filter plugin: {plugin.name}")

    def get_filter(self, name: str) -> FilterPlugin:
        """
        Get a filter plugin by name.

        Args:
            name: Plugin name

        Returns:
            FilterPlugin instance

        Raises:
            PluginNotFoundError: If plugin not found
        """
        if name not in self._filter_plugins:
            available = ", ".join(self._filter_plugins.keys())
            raise PluginNotFoundError(
                f"Filter plugin '{name}' not found. Available: {available}"
            )
        return self._filter_plugins[name]

    def list_filters(self) -> List[str]:
        """
        List all registered filter plugin names.

        Returns:
            List of plugin names
        """
        return list(self._filter_plugins.keys())

    def get_filter_info(self) -> List[Dict[str, str]]:
        """
        Get information about all filter plugins.

        Returns:
            List of plugin info dictionaries
        """
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
            }
            for plugin in self._filter_plugins.values()
        ]

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_all_info(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get information about all registered plugins.

        Returns:
            Dictionary with plugin category info
        """
        return {
            "output": self.get_output_info(),
            "organization": self.get_organization_info(),
            "filter": self.get_filter_info(),
        }

    def has_output(self, name: str) -> bool:
        """Check if an output plugin is registered."""
        return name in self._output_plugins

    def has_organization(self, name: str) -> bool:
        """Check if an organization plugin is registered."""
        return name in self._organization_plugins

    def has_filter(self, name: str) -> bool:
        """Check if a filter plugin is registered."""
        return name in self._filter_plugins

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._output_plugins.clear()
        self._organization_plugins.clear()
        self._filter_plugins.clear()
        logger.debug("Plugin registry cleared")


# =============================================================================
# Default Registry Factory
# =============================================================================

_default_registry: Optional[PluginRegistry] = None


def get_default_registry() -> PluginRegistry:
    """
    Get the default plugin registry with all built-in plugins.

    Returns:
        Configured PluginRegistry instance
    """
    global _default_registry

    if _default_registry is None:
        _default_registry = _create_default_registry()

    return _default_registry


def _create_default_registry() -> PluginRegistry:
    """Create and configure the default registry."""
    from .output.eml import EmlOutputPlugin
    from .output.markdown import MarkdownOutputPlugin
    from .output.json_output import JsonOutputPlugin
    from .organization.by_date import ByDatePlugin
    from .organization.by_sender import BySenderPlugin
    from .organization.none import NoneOrganizationPlugin

    registry = PluginRegistry()

    # Register output plugins
    registry.register_output(EmlOutputPlugin())
    registry.register_output(MarkdownOutputPlugin())
    registry.register_output(JsonOutputPlugin())

    # Register organization plugins
    registry.register_organization(ByDatePlugin())
    registry.register_organization(BySenderPlugin())
    registry.register_organization(NoneOrganizationPlugin())

    logger.info(
        f"Default registry created with "
        f"{len(registry.list_outputs())} output plugins, "
        f"{len(registry.list_organizations())} organization plugins"
    )

    return registry


def reset_default_registry() -> None:
    """Reset the default registry to force re-initialization."""
    global _default_registry
    _default_registry = None
