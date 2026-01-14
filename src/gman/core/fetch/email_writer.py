"""
Email output writing functionality.

H-2 refactoring: Extracted from GmailFetcher to follow Single Responsibility Principle.
"""

from __future__ import annotations

import datetime
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import html2text

logger = logging.getLogger(__name__)


class EmailWriter:
    """
    Writes emails to output formats (EML, Markdown, JSON).

    Extracted from GmailFetcher to follow Single Responsibility Principle.
    This class is responsible solely for writing email content to files.
    """

    FORMAT_EML = 'eml'
    FORMAT_MARKDOWN = 'markdown'
    FORMAT_BOTH = 'both'

    def __init__(
        self,
        output_dir: Path | str,
        format_type: str = 'both',
    ) -> None:
        """
        Initialize writer.

        Args:
            output_dir: Base output directory
            format_type: Output format ('eml', 'markdown', or 'both')
        """
        self.output_dir = Path(output_dir)
        self.format_type = format_type
        self.logger = logger

        # HTML to text converter
        self._html_converter = html2text.HTML2Text()
        self._html_converter.ignore_links = False
        self._html_converter.ignore_images = False

    def write(
        self,
        email: dict[str, Any],
        target_dir: Path,
        filename: str,
    ) -> list[Path]:
        """
        Write email to configured format(s).

        Args:
            email: Parsed email data dict
            target_dir: Target directory for output
            filename: Base filename (without extension)

        Returns:
            List of paths to created files
        """
        written_files: list[Path] = []
        target_dir.mkdir(parents=True, exist_ok=True)

        if self.format_type in (self.FORMAT_EML, self.FORMAT_BOTH):
            eml_path = target_dir / f"{filename}.eml"
            if self._write_eml(email, eml_path):
                written_files.append(eml_path)

        if self.format_type in (self.FORMAT_MARKDOWN, self.FORMAT_BOTH):
            md_path = target_dir / f"{filename}.md"
            if self._write_markdown(email, md_path):
                written_files.append(md_path)

        return written_files

    def _write_eml(self, email: dict[str, Any], path: Path) -> bool:
        """
        Write email in EML format.

        Args:
            email: Parsed email data dict
            path: Output file path

        Returns:
            True if successful
        """
        try:
            eml_content = self._create_eml_content(email)
            self._atomic_write(path, eml_content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing EML to {path}: {e}")
            return False

    def _write_markdown(self, email: dict[str, Any], path: Path) -> bool:
        """
        Write email in Markdown format.

        Args:
            email: Parsed email data dict
            path: Output file path

        Returns:
            True if successful
        """
        try:
            md_content = self._create_markdown_content(email)
            self._atomic_write(path, md_content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing Markdown to {path}: {e}")
            return False

    def _create_eml_content(self, email: dict[str, Any]) -> str:
        """
        Create EML format content from email data.

        Args:
            email: Parsed email data dict

        Returns:
            EML formatted string
        """
        headers = email.get('headers', {})
        plain_text = email.get('plain_text', '')
        html_body = email.get('html_body', '')

        eml_lines: list[str] = []

        # Essential headers
        essential_headers = [
            'message-id', 'date', 'from', 'to', 'cc', 'bcc',
            'subject', 'reply-to', 'in-reply-to', 'references'
        ]

        for header_name in essential_headers:
            if header_name in headers:
                formatted_name = '-'.join(word.capitalize() for word in header_name.split('-'))
                eml_lines.append(f"{formatted_name}: {headers[header_name]}")

        # Gmail specific headers
        eml_lines.append(f"X-Gmail-Message-ID: {email['id']}")
        eml_lines.append(f"X-Gmail-Thread-ID: {email['threadId']}")

        if email.get('labelIds'):
            eml_lines.append(f"X-Gmail-Labels: {', '.join(email['labelIds'])}")

        # MIME headers
        eml_lines.append("MIME-Version: 1.0")

        if html_body and plain_text:
            # Multipart message
            boundary = f"boundary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            eml_lines.append(f'Content-Type: multipart/alternative; boundary="{boundary}"')
            eml_lines.append('')  # Empty line after headers

            # Plain text part
            eml_lines.append(f"--{boundary}")
            eml_lines.append("Content-Type: text/plain; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append('')
            eml_lines.append(plain_text)
            eml_lines.append('')

            # HTML part
            eml_lines.append(f"--{boundary}")
            eml_lines.append("Content-Type: text/html; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append('')
            eml_lines.append(html_body)
            eml_lines.append('')
            eml_lines.append(f"--{boundary}--")

        elif html_body:
            eml_lines.append("Content-Type: text/html; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append('')
            eml_lines.append(html_body)

        elif plain_text:
            eml_lines.append("Content-Type: text/plain; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append('')
            eml_lines.append(plain_text)

        return '\n'.join(eml_lines)

    def _create_markdown_content(self, email: dict[str, Any]) -> str:
        """
        Create Markdown content from email data.

        Args:
            email: Parsed email data dict

        Returns:
            Markdown formatted string
        """
        headers = email.get('headers', {})
        plain_text = email.get('plain_text', '')
        html_body = email.get('html_body', '')

        md_lines: list[str] = []
        md_lines.append("# Email Details")
        md_lines.append('')

        # Metadata table
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

        md_lines.append(f"| Gmail ID | {email['id']} |")
        md_lines.append(f"| Thread ID | {email['threadId']} |")

        if email.get('labelIds'):
            md_lines.append(f"| Labels | {', '.join(email['labelIds'])} |")

        md_lines.append('')
        md_lines.append("## Message Content")
        md_lines.append('')

        # Convert HTML to markdown if available
        if html_body:
            try:
                markdown_body = self._html_converter.handle(html_body)
                md_lines.append(markdown_body)
            except (ValueError, AttributeError, UnicodeDecodeError) as e:
                self.logger.debug(f"HTML conversion failed: {e}")
                md_lines.append("*(HTML conversion failed)*")
                md_lines.append("```html")
                md_lines.append(html_body)
                md_lines.append("```")
        elif plain_text:
            md_lines.append(plain_text)
        else:
            md_lines.append("*(No readable content found)*")

        return '\n'.join(md_lines)

    def _atomic_write(self, path: Path, content: str, encoding: str = 'utf-8') -> None:
        """
        Write file atomically using temp file + rename pattern.

        Prevents file corruption if write is interrupted.

        Args:
            path: Target file path
            content: Content to write
            encoding: File encoding (default: utf-8)
        """
        dir_path = path.parent
        dir_path.mkdir(parents=True, exist_ok=True)

        # Write to temporary file in same directory (for atomic rename)
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding=encoding) as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            # Atomic rename (on POSIX; best-effort on Windows)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


__all__ = ['EmailWriter']
