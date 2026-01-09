"""
Tests for the Gmail Fetcher plugin system.

Tests plugin base classes, registry, and built-in plugins.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import json

from gmail_assistant.plugins.base import (
    OutputPlugin,
    OrganizationPlugin,
    FilterPlugin,
    CompositeFilter,
    PluginError,
    PluginNotFoundError,
)
from gmail_assistant.plugins.registry import (
    PluginRegistry,
    get_default_registry,
    reset_default_registry,
)
from gmail_assistant.plugins.output.eml import EmlOutputPlugin
from gmail_assistant.plugins.output.markdown import MarkdownOutputPlugin
from gmail_assistant.plugins.output.json_output import JsonOutputPlugin
from gmail_assistant.plugins.organization.by_date import ByDatePlugin
from gmail_assistant.plugins.organization.by_sender import BySenderPlugin
from gmail_assistant.plugins.organization.none import NoneOrganizationPlugin


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_registry_creation(self):
        """Test creating empty registry."""
        registry = PluginRegistry()
        assert registry.list_outputs() == []
        assert registry.list_organizations() == []
        assert registry.list_filters() == []

    def test_register_output_plugin(self):
        """Test registering output plugin."""
        registry = PluginRegistry()
        plugin = EmlOutputPlugin()
        registry.register_output(plugin)

        assert "eml" in registry.list_outputs()
        assert registry.has_output("eml")

    def test_get_output_plugin(self):
        """Test getting output plugin by name."""
        registry = PluginRegistry()
        plugin = MarkdownOutputPlugin()
        registry.register_output(plugin)

        retrieved = registry.get_output("markdown")
        assert retrieved is plugin

    def test_get_output_not_found(self):
        """Test getting non-existent output plugin raises error."""
        registry = PluginRegistry()

        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_output("unknown")

        assert "unknown" in str(exc_info.value)

    def test_register_organization_plugin(self):
        """Test registering organization plugin."""
        registry = PluginRegistry()
        plugin = ByDatePlugin()
        registry.register_organization(plugin)

        assert "date" in registry.list_organizations()
        assert registry.has_organization("date")

    def test_get_organization_plugin(self):
        """Test getting organization plugin by name."""
        registry = PluginRegistry()
        plugin = BySenderPlugin()
        registry.register_organization(plugin)

        retrieved = registry.get_organization("sender")
        assert retrieved is plugin

    def test_get_all_info(self):
        """Test getting info about all plugins."""
        registry = PluginRegistry()
        registry.register_output(EmlOutputPlugin())
        registry.register_organization(ByDatePlugin())

        info = registry.get_all_info()

        assert "output" in info
        assert "organization" in info
        assert "filter" in info
        assert len(info["output"]) == 1
        assert len(info["organization"]) == 1

    def test_clear_registry(self):
        """Test clearing all plugins from registry."""
        registry = PluginRegistry()
        registry.register_output(EmlOutputPlugin())
        registry.register_organization(ByDatePlugin())

        registry.clear()

        assert registry.list_outputs() == []
        assert registry.list_organizations() == []


class TestDefaultRegistry:
    """Tests for default registry factory."""

    def test_get_default_registry(self):
        """Test getting default registry with built-in plugins."""
        reset_default_registry()
        registry = get_default_registry()

        # Should have built-in output plugins
        assert "eml" in registry.list_outputs()
        assert "markdown" in registry.list_outputs()
        assert "json" in registry.list_outputs()

        # Should have built-in organization plugins
        assert "date" in registry.list_organizations()
        assert "sender" in registry.list_organizations()
        assert "none" in registry.list_organizations()

    def test_default_registry_singleton(self):
        """Test that default registry is cached."""
        reset_default_registry()
        registry1 = get_default_registry()
        registry2 = get_default_registry()

        assert registry1 is registry2


class TestEmlOutputPlugin:
    """Tests for EML output plugin."""

    def test_plugin_properties(self):
        """Test EML plugin properties."""
        plugin = EmlOutputPlugin()

        assert plugin.name == "eml"
        assert plugin.extension == ".eml"
        assert plugin.content_type == "message/rfc822"

    def test_generate_simple_email(self):
        """Test generating EML for simple email."""
        plugin = EmlOutputPlugin()

        email_data = {
            "headers": {
                "from": "sender@example.com",
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "date": "Mon, 8 Jan 2025 10:00:00 +0000",
            },
            "body_text": "Hello, this is a test email.",
            "body_html": "",
            "metadata": {
                "id": "msg123",
                "thread_id": "thread456",
                "labels": ["INBOX", "UNREAD"]
            }
        }

        eml = plugin.generate(email_data)

        assert "From: sender@example.com" in eml
        assert "To: recipient@example.com" in eml
        assert "Subject: Test Subject" in eml
        assert "X-Gmail-Message-ID: msg123" in eml
        assert "Hello, this is a test email." in eml

    def test_generate_multipart_email(self):
        """Test generating EML for multipart email."""
        plugin = EmlOutputPlugin()

        email_data = {
            "headers": {
                "from": "sender@example.com",
                "to": "recipient@example.com",
                "subject": "Multipart Test",
            },
            "body_text": "Plain text version",
            "body_html": "<html><body>HTML version</body></html>",
            "metadata": {"id": "msg123"}
        }

        eml = plugin.generate(email_data)

        assert "multipart/alternative" in eml
        assert "Plain text version" in eml
        assert "HTML version" in eml

    def test_save_eml(self):
        """Test saving EML to file."""
        plugin = EmlOutputPlugin()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test"
            content = "Test EML content"

            result = plugin.save(content, path)

            assert result is True
            saved_path = Path(tmpdir) / "test.eml"
            assert saved_path.exists()
            assert saved_path.read_text() == content


class TestMarkdownOutputPlugin:
    """Tests for Markdown output plugin."""

    def test_plugin_properties(self):
        """Test Markdown plugin properties."""
        plugin = MarkdownOutputPlugin()

        assert plugin.name == "markdown"
        assert plugin.extension == ".md"
        assert plugin.content_type == "text/markdown"

    def test_generate_markdown(self):
        """Test generating Markdown output."""
        plugin = MarkdownOutputPlugin()

        email_data = {
            "headers": {
                "from": "sender@example.com",
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "date": "2025-01-08",
            },
            "body_text": "Hello, this is a test.",
            "body_html": "",
            "metadata": {
                "id": "msg123",
                "thread_id": "thread456",
                "labels": ["INBOX"]
            }
        }

        md = plugin.generate(email_data)

        assert "# Test Subject" in md
        assert "| From | sender@example.com |" in md
        assert "Hello, this is a test." in md

    def test_generate_with_frontmatter(self):
        """Test Markdown includes YAML front matter."""
        plugin = MarkdownOutputPlugin(include_frontmatter=True)

        email_data = {
            "headers": {
                "subject": "Frontmatter Test",
                "from": "test@example.com",
                "to": "recipient@example.com",
                "date": "2025-01-08",
            },
            "body_text": "Content",
            "metadata": {"id": "123", "labels": ["INBOX"]}
        }

        md = plugin.generate(email_data)

        assert "---" in md
        assert "gmail_id:" in md


class TestJsonOutputPlugin:
    """Tests for JSON output plugin."""

    def test_plugin_properties(self):
        """Test JSON plugin properties."""
        plugin = JsonOutputPlugin()

        assert plugin.name == "json"
        assert plugin.extension == ".json"
        assert plugin.content_type == "application/json"

    def test_generate_json(self):
        """Test generating JSON output."""
        plugin = JsonOutputPlugin()

        email_data = {
            "headers": {
                "from": "sender@example.com",
                "to": "recipient@example.com",
                "subject": "Test Subject",
            },
            "body_text": "Test content",
            "body_html": "",
            "metadata": {
                "id": "msg123",
                "labels": ["INBOX", "UNREAD"]
            }
        }

        json_str = plugin.generate(email_data)
        data = json.loads(json_str)

        assert "schema_version" in data
        assert "message" in data
        assert data["message"]["id"] == "msg123"
        assert data["message"]["headers"]["subject"] == "Test Subject"


class TestByDateOrganization:
    """Tests for by-date organization plugin."""

    def test_plugin_properties(self):
        """Test plugin properties."""
        plugin = ByDatePlugin()

        assert plugin.name == "date"
        assert "year" in plugin.description.lower() or "date" in plugin.description.lower()

    def test_get_path_with_valid_date(self):
        """Test getting path for email with valid date."""
        plugin = ByDatePlugin()
        base_dir = Path("/backup")

        email_data = {
            "headers": {
                "date": "Mon, 8 Jan 2025 10:00:00 +0000"
            }
        }

        path = plugin.get_path(email_data, base_dir)

        assert path == Path("/backup/2025/01")

    def test_get_path_with_missing_date(self):
        """Test getting path for email with missing date."""
        plugin = ByDatePlugin()
        base_dir = Path("/backup")

        email_data = {"headers": {}}

        path = plugin.get_path(email_data, base_dir)

        assert path == Path("/backup/unknown")


class TestBySenderOrganization:
    """Tests for by-sender organization plugin."""

    def test_plugin_properties(self):
        """Test plugin properties."""
        plugin = BySenderPlugin()

        assert plugin.name == "sender"

    def test_get_path_with_email(self):
        """Test getting path for email with sender."""
        plugin = BySenderPlugin()
        base_dir = Path("/backup")

        email_data = {
            "headers": {
                "from": "John Doe <john@example.com>"
            }
        }

        path = plugin.get_path(email_data, base_dir)

        assert "john" in str(path).lower() or "doe" in str(path).lower()

    def test_get_path_sanitizes_name(self):
        """Test that sender name is sanitized."""
        plugin = BySenderPlugin()
        base_dir = Path("/backup")

        email_data = {
            "headers": {
                "from": "Test <test@example.com>"
            }
        }

        path = plugin.get_path(email_data, base_dir)

        # Should not contain invalid characters
        dir_name = path.name
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            assert char not in dir_name


class TestNoneOrganization:
    """Tests for no organization plugin."""

    def test_plugin_properties(self):
        """Test plugin properties."""
        plugin = NoneOrganizationPlugin()

        assert plugin.name == "none"

    def test_get_path_returns_base(self):
        """Test that get_path returns base directory."""
        plugin = NoneOrganizationPlugin()
        base_dir = Path("/backup")

        email_data = {
            "headers": {"from": "test@example.com"}
        }

        path = plugin.get_path(email_data, base_dir)

        assert path == base_dir


class TestCompositeFilter:
    """Tests for composite filter."""

    def test_empty_composite(self):
        """Test composite filter with no filters."""
        composite = CompositeFilter([])

        emails = [{"id": "1"}, {"id": "2"}]
        result = composite.apply(emails)

        assert result == emails

    def test_composite_with_filters(self):
        """Test composite filter with multiple filters."""

        class LabelFilter(FilterPlugin):
            def __init__(self, label: str):
                self.label = label

            @property
            def name(self) -> str:
                return f"label_{self.label}"

            def apply(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                return [e for e in emails if self.label in e.get("labels", [])]

        unread_filter = LabelFilter("UNREAD")
        inbox_filter = LabelFilter("INBOX")

        composite = CompositeFilter([unread_filter, inbox_filter])

        emails = [
            {"id": "1", "labels": ["INBOX", "UNREAD"]},
            {"id": "2", "labels": ["INBOX"]},
            {"id": "3", "labels": ["UNREAD"]},
            {"id": "4", "labels": []},
        ]

        result = composite.apply(emails)

        # Only emails with both UNREAD and INBOX should pass
        assert len(result) == 1
        assert result[0]["id"] == "1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
