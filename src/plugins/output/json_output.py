"""
JSON Output Plugin for Gmail Fetcher.

Generates structured JSON files for programmatic processing
and integration with other tools.
"""

import json
import logging
from typing import Any, Dict
from pathlib import Path
from datetime import datetime

from ..base import OutputPlugin, PluginError

logger = logging.getLogger(__name__)


class JsonOutputPlugin(OutputPlugin):
    """
    Plugin for generating JSON format output.

    Creates structured JSON files with full email data
    for programmatic processing and analysis.
    """

    def __init__(self, pretty_print: bool = True, include_raw_html: bool = False):
        """
        Initialize the JSON plugin.

        Args:
            pretty_print: Whether to format JSON with indentation
            include_raw_html: Whether to include raw HTML body
        """
        self._pretty_print = pretty_print
        self._include_raw_html = include_raw_html

    @property
    def name(self) -> str:
        return "json"

    @property
    def extension(self) -> str:
        return ".json"

    @property
    def content_type(self) -> str:
        return "application/json"

    @property
    def description(self) -> str:
        return "Structured JSON for programmatic processing"

    def generate(self, email_data: Dict[str, Any]) -> str:
        """
        Generate JSON content from email data.

        Args:
            email_data: Dictionary with email content and headers

        Returns:
            JSON formatted string
        """
        try:
            headers = email_data.get('headers', {})
            body_text = email_data.get('body_text', '')
            body_html = email_data.get('body_html', '')
            metadata = email_data.get('metadata', {})
            attachments = email_data.get('attachments', [])

            # Structure the output
            output = {
                "schema_version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "message": {
                    "id": metadata.get('id'),
                    "thread_id": metadata.get('thread_id'),
                    "labels": metadata.get('labels', []),
                    "headers": {
                        "subject": headers.get('subject', ''),
                        "from": headers.get('from', ''),
                        "to": headers.get('to', ''),
                        "cc": headers.get('cc'),
                        "bcc": headers.get('bcc'),
                        "date": headers.get('date', ''),
                        "message_id": headers.get('message-id', ''),
                        "in_reply_to": headers.get('in-reply-to'),
                        "references": headers.get('references'),
                    },
                    "body": {
                        "plain_text": body_text,
                        "html": body_html if self._include_raw_html else None,
                        "has_html": bool(body_html),
                    },
                    "attachments": [
                        {
                            "filename": att.get('filename'),
                            "mime_type": att.get('mime_type'),
                            "size": att.get('size'),
                        }
                        for att in attachments
                    ] if attachments else [],
                    "metadata": {
                        "size_estimate": metadata.get('size_estimate'),
                        "snippet": metadata.get('snippet'),
                        "is_unread": 'UNREAD' in metadata.get('labels', []),
                        "is_starred": 'STARRED' in metadata.get('labels', []),
                        "is_important": 'IMPORTANT' in metadata.get('labels', []),
                    }
                }
            }

            # Remove None values for cleaner output
            output = self._remove_none_values(output)

            # Serialize to JSON
            if self._pretty_print:
                return json.dumps(output, indent=2, ensure_ascii=False, default=str)
            else:
                return json.dumps(output, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            raise PluginError(f"Failed to generate JSON content: {e}")

    def save(self, content: str, path: Path) -> bool:
        """
        Save JSON content to file.

        Args:
            content: JSON content string
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
            logger.debug(f"Saved JSON to: {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            raise PluginError(f"Failed to save JSON file: {e}")

    def _remove_none_values(self, d: Dict) -> Dict:
        """Recursively remove None values from dictionary."""
        if not isinstance(d, dict):
            return d

        return {
            k: self._remove_none_values(v)
            for k, v in d.items()
            if v is not None
        }
