"""
Markdown Output Plugin for Gmail Fetcher.

Generates clean, readable Markdown files with YAML front matter
for email metadata.
"""

import logging
import re
from typing import Any, Dict
from pathlib import Path

from ..base import OutputPlugin, PluginError

logger = logging.getLogger(__name__)


class MarkdownOutputPlugin(OutputPlugin):
    """
    Plugin for generating Markdown format output.

    Creates human-readable Markdown files with:
    - YAML front matter for metadata
    - Formatted headers as a table
    - HTML-to-Markdown converted body content
    """

    def __init__(self, include_frontmatter: bool = True):
        """
        Initialize the Markdown plugin.

        Args:
            include_frontmatter: Whether to include YAML front matter
        """
        self._include_frontmatter = include_frontmatter
        self._html_converter = None

    @property
    def name(self) -> str:
        return "markdown"

    @property
    def extension(self) -> str:
        return ".md"

    @property
    def content_type(self) -> str:
        return "text/markdown"

    @property
    def description(self) -> str:
        return "Human-readable Markdown with metadata"

    def _get_html_converter(self):
        """Lazy load html2text converter."""
        if self._html_converter is None:
            try:
                import html2text
                self._html_converter = html2text.HTML2Text()
                self._html_converter.ignore_links = False
                self._html_converter.ignore_images = False
                self._html_converter.body_width = 80
            except ImportError:
                logger.warning("html2text not available, HTML will not be converted")
                self._html_converter = False
        return self._html_converter

    def generate(self, email_data: Dict[str, Any]) -> str:
        """
        Generate Markdown content from email data.

        Args:
            email_data: Dictionary with email content and headers

        Returns:
            Markdown formatted string
        """
        try:
            headers = email_data.get('headers', {})
            body_text = email_data.get('body_text', '')
            body_html = email_data.get('body_html', '')
            metadata = email_data.get('metadata', {})

            md_lines = []

            # YAML Front Matter
            if self._include_frontmatter:
                md_lines.append("---")
                md_lines.append(f"gmail_id: {metadata.get('id', 'unknown')}")
                md_lines.append(f"thread_id: {metadata.get('thread_id', 'unknown')}")
                if metadata.get('labels'):
                    labels_str = ', '.join(metadata['labels'])
                    md_lines.append(f"labels: [{labels_str}]")
                md_lines.append(f"date: {headers.get('date', 'unknown')}")
                md_lines.append(f"from: {self._escape_yaml(headers.get('from', 'unknown'))}")
                md_lines.append(f"to: {self._escape_yaml(headers.get('to', 'unknown'))}")
                md_lines.append(f"subject: {self._escape_yaml(headers.get('subject', 'No Subject'))}")
                md_lines.append("---")
                md_lines.append("")

            # Title
            subject = headers.get('subject', 'No Subject')
            md_lines.append(f"# {subject}")
            md_lines.append("")

            # Metadata Table
            md_lines.append("## Email Details")
            md_lines.append("")
            md_lines.append("| Field | Value |")
            md_lines.append("|-------|-------|")

            if headers.get('from'):
                md_lines.append(f"| From | {self._escape_table(headers['from'])} |")
            if headers.get('to'):
                md_lines.append(f"| To | {self._escape_table(headers['to'])} |")
            if headers.get('cc'):
                md_lines.append(f"| CC | {self._escape_table(headers['cc'])} |")
            if headers.get('date'):
                md_lines.append(f"| Date | {self._escape_table(headers['date'])} |")
            if metadata.get('id'):
                md_lines.append(f"| Gmail ID | {metadata['id']} |")
            if metadata.get('labels'):
                labels_str = ', '.join(metadata['labels'])
                md_lines.append(f"| Labels | {labels_str} |")

            md_lines.append("")

            # Message Content
            md_lines.append("## Message Content")
            md_lines.append("")

            # Prefer HTML converted to markdown, fallback to plain text
            if body_html:
                converter = self._get_html_converter()
                if converter and converter is not False:
                    try:
                        markdown_body = converter.handle(body_html)
                        md_lines.append(markdown_body)
                    except Exception as e:
                        logger.warning(f"HTML conversion failed: {e}")
                        md_lines.append("*(HTML conversion failed)*")
                        md_lines.append("")
                        md_lines.append("```html")
                        md_lines.append(body_html[:5000])  # Truncate very long HTML
                        md_lines.append("```")
                else:
                    md_lines.append(body_text if body_text else "*(No readable content)*")
            elif body_text:
                md_lines.append(body_text)
            else:
                md_lines.append("*(No message content)*")

            return "\n".join(md_lines)

        except Exception as e:
            logger.error(f"Error generating Markdown: {e}")
            raise PluginError(f"Failed to generate Markdown content: {e}")

    def save(self, content: str, path: Path) -> bool:
        """
        Save Markdown content to file.

        Args:
            content: Markdown content string
            path: Target file path

        Returns:
            True if successful
        """
        try:
            # Ensure path has correct extension
            if not str(path).endswith(self.extension):
                path = Path(str(path) + self.extension)

            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write with UTF-8 encoding
            path.write_text(content, encoding='utf-8')
            logger.debug(f"Saved Markdown to: {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving Markdown: {e}")
            raise PluginError(f"Failed to save Markdown file: {e}")

    def _escape_yaml(self, value: str) -> str:
        """Escape special characters for YAML."""
        if not value:
            return '""'
        # Quote if contains special characters
        if any(c in value for c in [':', '#', '&', '*', '!', '|', '>', "'", '"', '%', '@', '`']):
            # Escape quotes and wrap in quotes
            value = value.replace('"', '\\"')
            return f'"{value}"'
        return value

    def _escape_table(self, value: str) -> str:
        """Escape special characters for Markdown table cells."""
        if not value:
            return ""
        # Escape pipe characters and newlines
        value = value.replace('|', '\\|')
        value = value.replace('\n', ' ')
        return value
