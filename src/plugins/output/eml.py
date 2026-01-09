"""
EML Output Plugin for Gmail Fetcher.

Generates standard EML (RFC 5322) format files that can be
opened by email clients like Outlook, Thunderbird, etc.
"""

import datetime
import logging
from typing import Any, Dict, List
from pathlib import Path

from ..base import OutputPlugin, PluginError

logger = logging.getLogger(__name__)


class EmlOutputPlugin(OutputPlugin):
    """
    Plugin for generating EML format output.

    EML is the native email format that preserves all headers,
    MIME structure, and formatting. Compatible with email clients.
    """

    @property
    def name(self) -> str:
        return "eml"

    @property
    def extension(self) -> str:
        return ".eml"

    @property
    def content_type(self) -> str:
        return "message/rfc822"

    @property
    def description(self) -> str:
        return "Native EML format compatible with email clients"

    def generate(self, email_data: Dict[str, Any]) -> str:
        """
        Generate EML content from email data.

        Args:
            email_data: Dictionary with email content and headers

        Returns:
            EML formatted string
        """
        try:
            headers = email_data.get('headers', {})
            body_text = email_data.get('body_text', '')
            body_html = email_data.get('body_html', '')
            metadata = email_data.get('metadata', {})

            eml_lines = []

            # Essential headers
            essential_headers = [
                'message-id', 'date', 'from', 'to', 'cc', 'bcc',
                'subject', 'reply-to', 'in-reply-to', 'references'
            ]

            for header_name in essential_headers:
                value = headers.get(header_name) or headers.get(header_name.title())
                if value:
                    formatted_name = '-'.join(
                        word.capitalize() for word in header_name.split('-')
                    )
                    eml_lines.append(f"{formatted_name}: {value}")

            # Gmail-specific headers
            if metadata.get('id'):
                eml_lines.append(f"X-Gmail-Message-ID: {metadata['id']}")
            if metadata.get('thread_id'):
                eml_lines.append(f"X-Gmail-Thread-ID: {metadata['thread_id']}")
            if metadata.get('labels'):
                labels = ', '.join(metadata['labels'])
                eml_lines.append(f"X-Gmail-Labels: {labels}")

            # MIME headers and body
            eml_lines.append("MIME-Version: 1.0")

            if body_html and body_text:
                # Multipart message
                boundary = f"boundary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                eml_lines.append(
                    f'Content-Type: multipart/alternative; boundary="{boundary}"'
                )
                eml_lines.append("")  # Empty line before body

                # Plain text part
                eml_lines.append(f"--{boundary}")
                eml_lines.append("Content-Type: text/plain; charset=UTF-8")
                eml_lines.append("Content-Transfer-Encoding: 8bit")
                eml_lines.append("")
                eml_lines.append(body_text)
                eml_lines.append("")

                # HTML part
                eml_lines.append(f"--{boundary}")
                eml_lines.append("Content-Type: text/html; charset=UTF-8")
                eml_lines.append("Content-Transfer-Encoding: 8bit")
                eml_lines.append("")
                eml_lines.append(body_html)
                eml_lines.append("")
                eml_lines.append(f"--{boundary}--")

            elif body_html:
                # HTML only
                eml_lines.append("Content-Type: text/html; charset=UTF-8")
                eml_lines.append("Content-Transfer-Encoding: 8bit")
                eml_lines.append("")
                eml_lines.append(body_html)

            elif body_text:
                # Plain text only
                eml_lines.append("Content-Type: text/plain; charset=UTF-8")
                eml_lines.append("Content-Transfer-Encoding: 8bit")
                eml_lines.append("")
                eml_lines.append(body_text)

            else:
                # No body
                eml_lines.append("Content-Type: text/plain; charset=UTF-8")
                eml_lines.append("")
                eml_lines.append("")

            return "\n".join(eml_lines)

        except Exception as e:
            logger.error(f"Error generating EML: {e}")
            raise PluginError(f"Failed to generate EML content: {e}")

    def save(self, content: str, path: Path) -> bool:
        """
        Save EML content to file.

        Args:
            content: EML content string
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
            logger.debug(f"Saved EML to: {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving EML: {e}")
            raise PluginError(f"Failed to save EML file: {e}")
