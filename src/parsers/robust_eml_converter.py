#!/usr/bin/env python3
"""
Robust EML to Markdown Converter

A bulletproof converter that:
1. Properly parses Gmail API EML files
2. Uses multi-strategy content conversion
3. Extracts accurate metadata
4. Validates output quality
5. Provides fallback strategies
"""

import email
import email.policy
from email.message import EmailMessage
from pathlib import Path
import logging
import sys
import os
from typing import Dict, Optional, Tuple, Union
from datetime import datetime
import re
import html
import frontmatter

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import our advanced parser
from src.parsers.advanced_email_parser import EmailContentParser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustEMLConverter:
    """
    Robust EML to Markdown converter that handles Gmail API format correctly
    """

    def __init__(self):
        """Initialize converter with advanced parser"""
        self.advanced_parser = EmailContentParser()

    def extract_email_parts(self, eml_path: Path) -> Dict[str, Union[str, None]]:
        """
        Extract email content and metadata from EML file

        Args:
            eml_path: Path to EML file

        Returns:
            Dictionary with email parts (html, text, metadata)
        """
        try:
            # Read EML file with proper encoding
            with open(eml_path, 'rb') as f:
                email_bytes = f.read()

            # Parse with email library using default policy
            msg = email.message_from_bytes(email_bytes, policy=email.policy.default)

            # Gmail API EML files have transport headers first, then actual email headers
            # We need to find the actual email headers which might be in the message body
            actual_headers = self._find_actual_email_headers(msg)

            # Extract metadata from actual email headers
            metadata = {
                'subject': self._clean_header(actual_headers.get('Subject', '')),
                'from': self._clean_header(actual_headers.get('From', '')),
                'to': self._clean_header(actual_headers.get('To', '')),
                'date': self._parse_date(actual_headers.get('Date', '')),
                'message_id': self._clean_header(actual_headers.get('Message-ID', ''))
            }

            # Extract content parts - for Gmail API EML, parse raw file directly
            html_content = ""
            text_content = ""

            try:
                # Read the raw EML file content directly
                with open(eml_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_file_content = f.read()

                # Extract the actual email body from raw content
                body_content = self._extract_actual_body(raw_file_content)

                if body_content:
                    # Gmail API EML files usually contain MIME parts
                    # Parse the MIME structure to extract HTML and text content
                    if 'Content-Type: text/html' in body_content:
                        # Extract HTML content
                        html_content = self._extract_mime_content(body_content, 'text/html')

                    if 'Content-Type: text/plain' in body_content:
                        # Extract plain text content
                        text_content = self._extract_mime_content(body_content, 'text/plain')

                    # If no MIME parts found, treat as single content
                    if not html_content and not text_content:
                        if '<html' in body_content.lower() or '<body' in body_content.lower():
                            html_content = body_content
                        else:
                            text_content = body_content

            except Exception as e:
                logger.warning(f"Failed to extract email body: {e}")

            return {
                'html': html_content,
                'text': text_content,
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Failed to extract email parts from {eml_path}: {e}")
            return {
                'html': "",
                'text': "",
                'metadata': {}
            }

    def _clean_header(self, header_value: str) -> str:
        """Clean and decode email header values"""
        if not header_value:
            return ""

        try:
            # Decode header if needed
            from email.header import decode_header
            decoded_parts = decode_header(header_value)

            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors='ignore')
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)

            return decoded_string.strip()
        except Exception as e:
            logger.warning(f"Failed to decode header '{header_value}': {e}")
            return str(header_value).strip()

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse email date to ISO format"""
        if not date_str:
            return None

        try:
            from email.utils import parsedate_to_datetime
            parsed_date = parsedate_to_datetime(date_str)
            return parsed_date.isoformat()
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    def _find_actual_email_headers(self, msg) -> Dict[str, str]:
        """
        Find actual email headers in Gmail API EML format

        Gmail API EML files have structure:
        1. Transport headers (lines 1-159)
        2. Blank line separator (line 160)
        3. Actual email headers (lines 161-169)
        4. Blank lines
        5. MIME body content (line 173+)
        """
        # First, check if we have the headers directly (simple case)
        if msg.get('Subject') or msg.get('From') or msg.get('Message-ID'):
            headers = {}
            for key in ['Subject', 'From', 'To', 'Date', 'Message-ID']:
                value = msg.get(key)
                if value:
                    headers[key] = value
            return headers

        # Gmail API case: need to parse raw email content to find buried headers
        try:
            # Get the raw email file content directly
            import inspect

            # We need the original file path - get it from the call stack
            frame = inspect.currentframe()
            while frame:
                if 'eml_path' in frame.f_locals:
                    eml_path = frame.f_locals['eml_path']
                    break
                frame = frame.f_back

            if not eml_path:
                return {}

            # Read the raw EML file content
            with open(eml_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()

            lines = raw_content.split('\n')
            headers = {}

            # Gmail API emails have different structures - scan entire file for email headers
            # Look for all occurrences of key email headers throughout the file
            target_headers = ['Date', 'Subject', 'From', 'To', 'Message-Id', 'Message-ID']
            headers = {}

            for i, line in enumerate(lines):
                line_stripped = line.strip()

                # Check for any target header
                for header_name in target_headers:
                    if line_stripped.startswith(f'{header_name}:'):
                        header_value = line_stripped[len(header_name)+1:].strip()

                        # Handle multi-line headers (check next few lines for continuations)
                        j = i + 1
                        while j < len(lines) and j < i + 5:
                            next_line = lines[j]
                            if next_line.startswith(' ') or next_line.startswith('\t'):
                                # Continuation line
                                header_value += ' ' + next_line.strip()
                                j += 1
                            else:
                                break

                        # Normalize header names (Message-Id vs Message-ID)
                        normalized_name = 'Message-ID' if header_name in ['Message-Id', 'Message-ID'] else header_name
                        headers[normalized_name] = header_value
                        break

            # Final cleanup - remove any empty headers
            return {k: v for k, v in headers.items() if v}

        except Exception as e:
            logger.error(f"Failed to parse actual headers: {e}")
            return {}

    def _extract_actual_body(self, raw_content: str) -> str:
        """
        Extract actual email body from Gmail API EML content

        Gmail API EML structure:
        1. Transport headers (lines 1-159)
        2. Blank line (line 160)
        3. Email headers (lines 161-169)
        4. Blank lines (lines 170-172)
        5. MIME body starts (line 173+)
        """
        try:
            lines = raw_content.split('\n')

            # Find where email headers end and MIME body starts
            # Look for the MIME boundary or Content-Type indicators
            body_start = -1

            # First find where transport headers end (large blank section)
            transport_end = -1
            for i in range(50, min(200, len(lines))):
                line = lines[i].strip()
                if line == '' and i > 50:
                    # Check if next section has email headers
                    for j in range(i + 1, min(i + 15, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and ':' in next_line:
                            header_name = next_line.split(':', 1)[0]
                            if header_name in ['Message-ID', 'Subject', 'From', 'To']:
                                transport_end = i
                                break
                if transport_end > 0:
                    break

            if transport_end < 0:
                transport_end = 160  # Default fallback

            # Now find where email headers end and body starts
            # Look for MIME boundary markers or double blank lines
            header_section_start = transport_end + 1

            for i in range(header_section_start, min(header_section_start + 30, len(lines))):
                line = lines[i].strip()

                # Look for MIME boundary (starts with --)
                if line.startswith('--') and len(line) > 10:
                    body_start = i
                    break

                # Look for double empty lines after headers
                if (line == '' and i > header_section_start + 5 and
                    i < len(lines) - 2 and lines[i + 1].strip() == ''):
                    # Found double blank line, body likely starts after
                    body_start = i + 2
                    break

            # If we found body start, extract it
            if body_start > 0 and body_start < len(lines):
                body_content = '\n'.join(lines[body_start:])
                return body_content.strip()

            # Fallback: everything after transport headers
            if transport_end > 0:
                fallback_content = '\n'.join(lines[transport_end + 10:])
                return fallback_content.strip()

            # Last resort
            return raw_content

        except Exception as e:
            logger.error(f"Failed to extract actual body: {e}")
            return raw_content

    def convert_eml_to_markdown(self, eml_path: Path, output_path: Path) -> bool:
        """
        Convert single EML file to high-quality markdown

        Args:
            eml_path: Input EML file path
            output_path: Output markdown file path

        Returns:
            Success status
        """
        try:
            logger.info(f"Converting {eml_path.name} to markdown...")

            # Extract email parts
            email_parts = self.extract_email_parts(eml_path)

            if not email_parts['html'] and not email_parts['text']:
                logger.error(f"No content found in {eml_path}")
                return False

            # Use advanced parser for content conversion
            result = self.advanced_parser.parse_email_content(
                html_content=email_parts['html'],
                plain_text=email_parts['text'],
                sender=email_parts['metadata'].get('from', ''),
                subject=email_parts['metadata'].get('subject', '')
            )

            # Create YAML front matter
            front_matter = {
                'subject': email_parts['metadata'].get('subject', ''),
                'from': email_parts['metadata'].get('from', ''),
                'to': email_parts['metadata'].get('to', ''),
                'date': email_parts['metadata'].get('date'),
                'message_id': email_parts['metadata'].get('message_id', ''),
                'conversion_strategy': result.get('strategy', 'unknown'),
                'quality_score': result.get('quality', 0.0),
                'source_file': str(eml_path.name)
            }

            # Create markdown document with front matter
            post = frontmatter.Post(result['markdown'], **front_matter)
            markdown_content = frontmatter.dumps(post)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"Successfully converted to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to convert {eml_path}: {e}")
            return False

    def convert_directory(self, input_dir: Path, output_dir: Path, limit: int = 0) -> Dict[str, int]:
        """
        Convert all EML files in directory tree to markdown

        Args:
            input_dir: Input directory with EML files
            output_dir: Output directory for markdown files
            limit: Maximum files to process (0 = no limit)

        Returns:
            Conversion statistics
        """
        eml_files = list(input_dir.glob("**/*.eml"))

        if limit > 0:
            eml_files = eml_files[:limit]

        stats = {
            'total': len(eml_files),
            'success': 0,
            'failed': 0
        }

        logger.info(f"Found {stats['total']} EML files to convert")

        for eml_file in eml_files:
            # Preserve directory structure
            rel_path = eml_file.relative_to(input_dir)
            output_path = output_dir / rel_path.with_suffix('.md')

            if self.convert_eml_to_markdown(eml_file, output_path):
                stats['success'] += 1
            else:
                stats['failed'] += 1

        logger.info(f"Conversion complete: {stats['success']} success, {stats['failed']} failed")
        return stats

    def _extract_mime_content(self, mime_body: str, content_type: str) -> str:
        """
        Extract and decode MIME content from multipart body with proper encoding support

        Args:
            mime_body: Raw MIME body content
            content_type: MIME type to extract (e.g., 'text/html', 'text/plain')

        Returns:
            Decoded content string
        """
        try:
            lines = mime_body.split('\n')

            # Find the MIME section with our content type
            section_start = -1
            section_end = -1
            encoding_type = None
            actual_boundary = None

            # First, find the actual MIME boundary (long string starting with --)
            for line in lines:
                line_stripped = line.strip()
                if (line_stripped.startswith('--') and
                    len(line_stripped) > 20 and
                    '=' not in line_stripped and
                    'boundary=' not in line_stripped):
                    actual_boundary = line_stripped
                    break

            if not actual_boundary:
                return ""

            # Find our content type section between proper MIME boundaries
            for i, line in enumerate(lines):
                line_stripped = line.strip()

                # Look for the actual MIME boundary
                if line_stripped == actual_boundary and i < len(lines) - 5:
                    # Check next few lines for content type and encoding
                    content_type_found = False
                    for j in range(i + 1, min(i + 10, len(lines))):
                        check_line = lines[j].strip()
                        if f'Content-Type: {content_type}' in check_line:
                            content_type_found = True
                        elif 'Content-Transfer-Encoding: base64' in check_line:
                            encoding_type = 'base64'
                        elif 'Content-Transfer-Encoding: quoted-printable' in check_line:
                            encoding_type = 'quoted-printable'
                        elif check_line == '' and content_type_found:
                            # Found blank line after headers - content starts here
                            section_start = j + 1
                            break

                    if section_start >= 0:
                        # Find the end of this section (next occurrence of actual boundary)
                        for k in range(section_start, len(lines)):
                            if lines[k].strip() == actual_boundary:
                                section_end = k
                                break
                        break

            if section_start < 0:
                return ""

            # Extract content between proper MIME boundaries
            if section_end < 0:
                section_end = len(lines)

            content_lines = []
            for i in range(section_start, section_end):
                content_lines.append(lines[i])

            if not content_lines:
                return ""

            # Decode based on encoding type
            if encoding_type == 'base64':
                # Base64 decoding
                content = ''.join(line.strip() for line in content_lines if line.strip())
                try:
                    import base64
                    decoded = base64.b64decode(content)
                    return decoded.decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.warning(f"Failed to decode base64 content: {e}")
                    return '\n'.join(content_lines)

            elif encoding_type == 'quoted-printable':
                # Quoted-printable decoding
                try:
                    import quopri
                    raw_content = '\n'.join(content_lines)
                    decoded = quopri.decodestring(raw_content.encode('ascii'))
                    return decoded.decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.warning(f"Failed to decode quoted-printable content: {e}")
                    # Manual fallback - handle = line endings
                    result = []
                    for line in content_lines:
                        if line.rstrip().endswith('='):
                            # Soft line break - remove = and don't add newline
                            result.append(line.rstrip()[:-1])
                        else:
                            result.append(line.rstrip() + '\n')
                    return ''.join(result)

            else:
                # No encoding - return as is
                return '\n'.join(content_lines)

        except Exception as e:
            logger.error(f"Failed to extract MIME content: {e}")
            return ""

def main():
    """CLI interface for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Robust EML to Markdown Converter")
    parser.add_argument("--input", required=True, help="Input directory with EML files")
    parser.add_argument("--output", required=True, help="Output directory for markdown files")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files to process")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    converter = RobustEMLConverter()
    stats = converter.convert_directory(Path(args.input), Path(args.output), args.limit)

    print(f"\nConversion Results:")
    print(f"Total files: {stats['total']}")
    print(f"Successful: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success rate: {stats['success']/stats['total']*100:.1f}%")

if __name__ == "__main__":
    main()