"""
Output Plugin Manager for Gmail Assistant (M-1 refactoring).

Implements the Strategy pattern for email output formats.
Extracts output logic from GmailFetcher to reduce its responsibilities.
"""

import datetime
import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import html2text


class OutputPlugin(ABC):
    """Abstract base class for output format plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name identifier."""
        ...

    @property
    @abstractmethod
    def extension(self) -> str:
        """File extension (e.g., '.eml', '.md')."""
        ...

    @abstractmethod
    def generate(self, email_data: dict[str, Any]) -> str:
        """Generate output content from email data."""
        ...

    def save(self, content: str, path: Path) -> bool:
        """
        Save content to file atomically.

        Args:
            content: Content to save
            path: Target file path

        Returns:
            True if successful
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write using temp file + rename
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            return True
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


class EMLPlugin(OutputPlugin):
    """EML format output plugin."""

    @property
    def name(self) -> str:
        return "eml"

    @property
    def extension(self) -> str:
        return ".eml"

    def generate(self, email_data: dict[str, Any]) -> str:
        """Generate EML content from email data."""
        headers = self._extract_headers(email_data.get('headers', []))
        payload = email_data.get('payload', {})
        plain_text, html_body = self._get_body(payload)

        eml_lines = []

        # Essential headers
        essential = ['message-id', 'date', 'from', 'to', 'cc', 'bcc',
                    'subject', 'reply-to', 'in-reply-to', 'references']

        for header_name in essential:
            if header_name in headers:
                formatted = '-'.join(w.capitalize() for w in header_name.split('-'))
                eml_lines.append(f"{formatted}: {headers[header_name]}")

        # Gmail-specific headers
        if 'id' in email_data:
            eml_lines.append(f"X-Gmail-Message-ID: {email_data['id']}")
        if 'threadId' in email_data:
            eml_lines.append(f"X-Gmail-Thread-ID: {email_data['threadId']}")
        if 'labelIds' in email_data:
            eml_lines.append(f"X-Gmail-Labels: {', '.join(email_data['labelIds'])}")

        # MIME headers and body
        eml_lines.append("MIME-Version: 1.0")

        if html_body and plain_text:
            boundary = f"boundary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            eml_lines.append(f'Content-Type: multipart/alternative; boundary="{boundary}"')
            eml_lines.append("")
            eml_lines.append(f"--{boundary}")
            eml_lines.append("Content-Type: text/plain; charset=UTF-8")
            eml_lines.append("")
            eml_lines.append(plain_text)
            eml_lines.append(f"--{boundary}")
            eml_lines.append("Content-Type: text/html; charset=UTF-8")
            eml_lines.append("")
            eml_lines.append(html_body)
            eml_lines.append(f"--{boundary}--")
        elif html_body:
            eml_lines.append("Content-Type: text/html; charset=UTF-8")
            eml_lines.append("")
            eml_lines.append(html_body)
        elif plain_text:
            eml_lines.append("Content-Type: text/plain; charset=UTF-8")
            eml_lines.append("")
            eml_lines.append(plain_text)

        return "\n".join(eml_lines)

    def _extract_headers(self, headers: list[dict]) -> dict[str, str]:
        """Extract headers from Gmail API format."""
        return {h.get('name', '').lower(): h.get('value', '') for h in headers}

    def _get_body(self, payload: dict) -> tuple:
        """Extract plain text and HTML body from payload."""
        plain_text = ""
        html_body = ""

        def extract(part):
            nonlocal plain_text, html_body
            if 'parts' in part:
                for subpart in part['parts']:
                    extract(subpart)
            else:
                mime_type = part.get('mimeType', '')
                body_data = part.get('body', {}).get('data', '')
                if body_data:
                    import base64
                    try:
                        data = body_data.replace('-', '+').replace('_', '/')
                        decoded = base64.b64decode(data + '===').decode('utf-8')
                        if mime_type == 'text/plain':
                            plain_text += decoded
                        elif mime_type == 'text/html':
                            html_body += decoded
                    except Exception:
                        pass

        extract(payload)
        return plain_text, html_body


class MarkdownPlugin(OutputPlugin):
    """Markdown format output plugin."""

    def __init__(self):
        self._html_converter = html2text.HTML2Text()
        self._html_converter.ignore_links = False
        self._html_converter.ignore_images = False

    @property
    def name(self) -> str:
        return "markdown"

    @property
    def extension(self) -> str:
        return ".md"

    def generate(self, email_data: dict[str, Any]) -> str:
        """Generate Markdown content from email data."""
        headers = self._extract_headers(email_data.get('headers', []))
        payload = email_data.get('payload', {})
        plain_text, html_body = self._get_body(payload)

        md_lines = []
        md_lines.append("# Email Details")
        md_lines.append("")
        md_lines.append("| Field | Value |")
        md_lines.append("|-------|-------|")

        if 'from' in headers:
            md_lines.append(f"| From | {headers['from']} |")
        if 'to' in headers:
            md_lines.append(f"| To | {headers['to']} |")
        if 'date' in headers:
            md_lines.append(f"| Date | {headers['date']} |")
        if 'subject' in headers:
            md_lines.append(f"| Subject | {headers['subject']} |")

        if 'id' in email_data:
            md_lines.append(f"| Gmail ID | {email_data['id']} |")
        if 'threadId' in email_data:
            md_lines.append(f"| Thread ID | {email_data['threadId']} |")
        if 'labelIds' in email_data:
            md_lines.append(f"| Labels | {', '.join(email_data['labelIds'])} |")

        md_lines.append("")
        md_lines.append("## Message Content")
        md_lines.append("")

        if html_body:
            try:
                md_lines.append(self._html_converter.handle(html_body))
            except Exception:
                md_lines.append("*(HTML conversion failed)*")
                md_lines.append("```html")
                md_lines.append(html_body)
                md_lines.append("```")
        elif plain_text:
            md_lines.append(plain_text)
        else:
            md_lines.append("*(No readable content found)*")

        return "\n".join(md_lines)

    def _extract_headers(self, headers: list[dict]) -> dict[str, str]:
        """Extract headers from Gmail API format."""
        return {h.get('name', '').lower(): h.get('value', '') for h in headers}

    def _get_body(self, payload: dict) -> tuple:
        """Extract plain text and HTML body from payload."""
        return EMLPlugin()._get_body(payload)


class JSONPlugin(OutputPlugin):
    """JSON format output plugin."""

    @property
    def name(self) -> str:
        return "json"

    @property
    def extension(self) -> str:
        return ".json"

    def generate(self, email_data: dict[str, Any]) -> str:
        """Generate JSON content from email data."""
        return json.dumps(email_data, indent=2, default=str)


class OutputPluginManager:
    """
    Manages output format plugins.

    Implements plugin registration and format selection.
    """

    def __init__(self):
        self._plugins: dict[str, OutputPlugin] = {}
        # Register default plugins
        self.register(EMLPlugin())
        self.register(MarkdownPlugin())
        self.register(JSONPlugin())

    def register(self, plugin: OutputPlugin) -> None:
        """Register an output plugin."""
        self._plugins[plugin.name] = plugin

    def get_plugin(self, name: str) -> OutputPlugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_available_formats(self) -> list[str]:
        """Get list of available format names."""
        return list(self._plugins.keys())

    def generate(self, email_data: dict[str, Any], format_name: str) -> str:
        """Generate output content using specified format."""
        plugin = self._plugins.get(format_name)
        if not plugin:
            raise ValueError(f"Unknown format: {format_name}. Available: {self.get_available_formats()}")
        return plugin.generate(email_data)

    def save(
        self,
        email_data: dict[str, Any],
        output_dir: Path,
        format_name: str,
        filename_base: str
    ) -> Path:
        """
        Generate and save email in specified format.

        Args:
            email_data: Email data dictionary
            output_dir: Output directory
            format_name: Format name ('eml', 'markdown', 'json')
            filename_base: Base filename without extension

        Returns:
            Path to saved file
        """
        plugin = self._plugins.get(format_name)
        if not plugin:
            raise ValueError(f"Unknown format: {format_name}")

        content = plugin.generate(email_data)
        filepath = output_dir / f"{filename_base}{plugin.extension}"
        plugin.save(content, filepath)
        return filepath

    def save_all(
        self,
        email_data: dict[str, Any],
        output_dir: Path,
        filename_base: str,
        formats: list[str] | None = None
    ) -> list[Path]:
        """
        Save email in multiple formats.

        Args:
            email_data: Email data dictionary
            output_dir: Output directory
            filename_base: Base filename without extension
            formats: List of format names (default: all)

        Returns:
            List of paths to saved files
        """
        if formats is None:
            formats = list(self._plugins.keys())

        paths = []
        for fmt in formats:
            paths.append(self.save(email_data, output_dir, fmt, filename_base))
        return paths
