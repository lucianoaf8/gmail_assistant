"""
Base classes for the Gmail Fetcher plugin system.

This module defines abstract base classes for all plugin types:
- OutputPlugin: Generates output in specific formats
- OrganizationPlugin: Organizes files in directory structures
- FilterPlugin: Filters and transforms email lists
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Base exception for plugin errors."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be found."""
    pass


class PluginConfigError(PluginError):
    """Raised when plugin configuration is invalid."""
    pass


class BasePlugin(ABC):
    """Base class for all plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique plugin identifier.

        Returns:
            Plugin name string (e.g., 'markdown', 'by_date')
        """
        pass

    @property
    def description(self) -> str:
        """
        Human-readable plugin description.

        Returns:
            Description string.
        """
        return ""

    @property
    def version(self) -> str:
        """
        Plugin version string.

        Returns:
            Version in semver format (e.g., '1.0.0')
        """
        return "1.0.0"

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the plugin with settings.

        Args:
            config: Configuration dictionary

        Raises:
            PluginConfigError: If configuration is invalid
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration before applying.

        Args:
            config: Configuration dictionary

        Returns:
            True if configuration is valid
        """
        return True


class OutputPlugin(BasePlugin):
    """
    Abstract base class for output format plugins.

    Output plugins convert email data to specific file formats
    like EML, Markdown, JSON, etc.

    Example:
        class MarkdownPlugin(OutputPlugin):
            @property
            def name(self) -> str:
                return "markdown"

            @property
            def extension(self) -> str:
                return ".md"

            def generate(self, email_data: Dict[str, Any]) -> str:
                # Convert email to markdown
                return markdown_content

            def save(self, content: str, path: Path) -> bool:
                path.write_text(content, encoding='utf-8')
                return True
    """

    @property
    @abstractmethod
    def extension(self) -> str:
        """
        File extension for this output format.

        Returns:
            Extension string including dot (e.g., '.md', '.eml')
        """
        pass

    @property
    def content_type(self) -> str:
        """
        MIME content type for this format.

        Returns:
            MIME type string (e.g., 'text/markdown', 'message/rfc822')
        """
        return "text/plain"

    @abstractmethod
    def generate(self, email_data: Dict[str, Any]) -> str:
        """
        Generate output content from email data.

        Args:
            email_data: Dictionary containing:
                - headers: Dict of email headers
                - body_text: Plain text body
                - body_html: HTML body
                - attachments: List of attachment info
                - metadata: Gmail-specific metadata

        Returns:
            Formatted content string.

        Raises:
            PluginError: If generation fails
        """
        pass

    @abstractmethod
    def save(self, content: str, path: Path) -> bool:
        """
        Save generated content to file.

        Args:
            content: Content to save
            path: Target file path (without extension)

        Returns:
            True if save was successful

        Raises:
            PluginError: If save fails
        """
        pass

    def get_filename(
        self,
        email_data: Dict[str, Any],
        base_name: str
    ) -> str:
        """
        Generate filename for the output file.

        Args:
            email_data: Email data dictionary
            base_name: Base filename without extension

        Returns:
            Complete filename with extension
        """
        return f"{base_name}{self.extension}"


class OrganizationPlugin(BasePlugin):
    """
    Abstract base class for file organization plugins.

    Organization plugins determine the directory structure
    for storing email files.

    Example:
        class ByDatePlugin(OrganizationPlugin):
            @property
            def name(self) -> str:
                return "by_date"

            def get_path(self, email_data: Dict, base_dir: Path) -> Path:
                date = parse_date(email_data['headers']['date'])
                return base_dir / date.strftime('%Y/%m')
    """

    @abstractmethod
    def get_path(
        self,
        email_data: Dict[str, Any],
        base_dir: Path
    ) -> Path:
        """
        Determine the output directory for an email.

        Args:
            email_data: Dictionary containing email metadata
            base_dir: Base output directory

        Returns:
            Full directory path for the email file
        """
        pass

    def create_path(
        self,
        email_data: Dict[str, Any],
        base_dir: Path
    ) -> Path:
        """
        Get path and create directories if needed.

        Args:
            email_data: Email data dictionary
            base_dir: Base output directory

        Returns:
            Created directory path
        """
        path = self.get_path(email_data, base_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


class FilterPlugin(BasePlugin):
    """
    Abstract base class for email filter plugins.

    Filter plugins can filter, sort, or transform lists of emails.

    Example:
        class UnreadFilter(FilterPlugin):
            @property
            def name(self) -> str:
                return "unread"

            def apply(self, emails: List[Dict]) -> List[Dict]:
                return [e for e in emails if 'UNREAD' in e.get('labels', [])]
    """

    @abstractmethod
    def apply(
        self,
        emails: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply filter to email list.

        Args:
            emails: List of email data dictionaries

        Returns:
            Filtered list of emails
        """
        pass

    def matches(self, email: Dict[str, Any]) -> bool:
        """
        Check if a single email matches the filter.

        Args:
            email: Email data dictionary

        Returns:
            True if email matches filter criteria
        """
        return email in self.apply([email])


class CompositeFilter(FilterPlugin):
    """
    Composite filter that combines multiple filters.

    Applies filters in sequence (AND logic).
    """

    def __init__(self, filters: List[FilterPlugin]):
        self._filters = filters

    @property
    def name(self) -> str:
        names = [f.name for f in self._filters]
        return f"composite({','.join(names)})"

    def apply(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result = emails
        for filter_plugin in self._filters:
            result = filter_plugin.apply(result)
        return result

    def add_filter(self, filter_plugin: FilterPlugin) -> None:
        """Add a filter to the composite."""
        self._filters.append(filter_plugin)


class TransformPlugin(BasePlugin):
    """
    Abstract base class for email transformation plugins.

    Transform plugins modify email data in place.
    """

    @abstractmethod
    def transform(
        self,
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform email data.

        Args:
            email_data: Original email data

        Returns:
            Transformed email data
        """
        pass

    def transform_batch(
        self,
        emails: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform a batch of emails.

        Args:
            emails: List of email data dictionaries

        Returns:
            List of transformed emails
        """
        return [self.transform(e) for e in emails]
