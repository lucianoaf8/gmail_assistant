#!/usr/bin/env python3
"""
Gmail Email Fetcher and Backup Tool
Downloads emails as EML files and optionally converts to markdown
"""

import os
import json
import email
import base64
import binascii
import datetime
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Iterator
import re
import html2text

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Local imports
from ..auth.base import ReadOnlyGmailAuth
from ..constants import SCOPES_READONLY as SCOPES
from ...utils.memory_manager import MemoryTracker, StreamingEmailProcessor, ProgressiveLoader

class GmailFetcher:
    def __init__(self, credentials_file: str = 'credentials.json'):
        self.auth = ReadOnlyGmailAuth(credentials_file)
        self.memory_tracker = MemoryTracker()
        self.streaming_processor = StreamingEmailProcessor()
        self.progressive_loader = ProgressiveLoader()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self):
        """Authenticate with Gmail API using secure credential storage"""
        result = self.auth.authenticate()
        if result:
            self.logger.info("Successfully authenticated with Gmail API")
        return result

    @property
    def service(self):
        """Get Gmail service, authenticating if necessary"""
        return self.auth.service
    
    def get_profile(self):
        """Get Gmail profile info"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'email': profile.get('emailAddress'),
                'total_messages': profile.get('messagesTotal'),
                'total_threads': profile.get('threadsTotal')
            }
        except HttpError as error:
            self.logger.error(f"Error getting profile: {error}")
            return None
    
    def search_messages(self, query: str = '', max_results: int = 100) -> List[str]:
        """Search for messages matching query"""
        try:
            self.logger.info(f"Searching for messages: '{query}'")
            results = self.service.users().messages().list(
                userId='me', 
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            message_ids = [msg['id'] for msg in messages]
            
            # Handle pagination if needed
            while 'nextPageToken' in results and len(message_ids) < max_results:
                page_token = results['nextPageToken']
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token,
                    maxResults=max_results - len(message_ids)
                ).execute()
                
                page_messages = results.get('messages', [])
                message_ids.extend([msg['id'] for msg in page_messages])
            
            self.logger.info(f"Found {len(message_ids)} messages")
            return message_ids

        except HttpError as error:
            self.logger.error(f"Error searching messages: {error}")
            return []
    
    def get_message_details(self, message_id: str) -> Optional[Dict]:
        """Get full message details"""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            return message
        except HttpError as error:
            self.logger.error(f"Error getting message {message_id}: {error}")
            return None
    
    def decode_base64(self, data: str) -> str:
        """Decode base64 email data"""
        try:
            # Handle URL-safe base64
            data = data.replace('-', '+').replace('_', '/')
            # Add padding if needed
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            return base64.b64decode(data).decode('utf-8')
        except (ValueError, UnicodeDecodeError, binascii.Error) as e:
            self.logger.warning(f"Base64 decode error: {e}")
            return ""
    
    def extract_headers(self, headers: List[Dict]) -> Dict[str, str]:
        """Extract important headers from email"""
        header_dict = {}
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            header_dict[name] = value
        return header_dict
    
    def get_message_body(self, payload: Dict) -> Tuple[str, str]:
        """Extract plain text and HTML body from message payload"""
        plain_text = ""
        html_body = ""
        
        def extract_parts(part):
            nonlocal plain_text, html_body
            
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_parts(subpart)
            else:
                mime_type = part.get('mimeType', '')
                body_data = part.get('body', {}).get('data', '')
                
                if body_data:
                    decoded_data = self.decode_base64(body_data)
                    
                    if mime_type == 'text/plain':
                        plain_text += decoded_data
                    elif mime_type == 'text/html':
                        html_body += decoded_data
        
        extract_parts(payload)
        return plain_text, html_body
    
    def create_eml_content(self, message_data: Dict) -> str:
        """Create EML format content from message data"""
        headers = self.extract_headers(message_data['payload'].get('headers', []))
        plain_text, html_body = self.get_message_body(message_data['payload'])
        
        # Build EML content
        eml_lines = []
        
        # Essential headers
        essential_headers = [
            'message-id', 'date', 'from', 'to', 'cc', 'bcc', 
            'subject', 'reply-to', 'in-reply-to', 'references'
        ]
        
        for header_name in essential_headers:
            if header_name in headers:
                # Capitalize header name properly
                formatted_name = '-'.join(word.capitalize() for word in header_name.split('-'))
                eml_lines.append(f"{formatted_name}: {headers[header_name]}")
        
        # Gmail specific headers
        eml_lines.append(f"X-Gmail-Message-ID: {message_data['id']}")
        eml_lines.append(f"X-Gmail-Thread-ID: {message_data['threadId']}")
        
        if 'labelIds' in message_data:
            eml_lines.append(f"X-Gmail-Labels: {', '.join(message_data['labelIds'])}")
        
        # MIME headers
        eml_lines.append("MIME-Version: 1.0")
        
        if html_body and plain_text:
            # Multipart message
            boundary = f"boundary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            eml_lines.append(f'Content-Type: multipart/alternative; boundary="{boundary}"')
            eml_lines.append("")  # Empty line after headers
            
            # Plain text part
            eml_lines.append(f"--{boundary}")
            eml_lines.append("Content-Type: text/plain; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append("")
            eml_lines.append(plain_text)
            eml_lines.append("")
            
            # HTML part
            eml_lines.append(f"--{boundary}")
            eml_lines.append("Content-Type: text/html; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append("")
            eml_lines.append(html_body)
            eml_lines.append("")
            eml_lines.append(f"--{boundary}--")
            
        elif html_body:
            # HTML only
            eml_lines.append("Content-Type: text/html; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append("")  # Empty line after headers
            eml_lines.append(html_body)
            
        elif plain_text:
            # Plain text only
            eml_lines.append("Content-Type: text/plain; charset=UTF-8")
            eml_lines.append("Content-Transfer-Encoding: 8bit")
            eml_lines.append("")  # Empty line after headers
            eml_lines.append(plain_text)
        
        return "\n".join(eml_lines)
    
    def create_markdown_content(self, message_data: Dict) -> str:
        """Create markdown content from message data"""
        headers = self.extract_headers(message_data['payload'].get('headers', []))
        plain_text, html_body = self.get_message_body(message_data['payload'])
        
        # Build markdown
        md_lines = []
        md_lines.append("# Email Details")
        md_lines.append("")
        
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
        
        md_lines.append(f"| Gmail ID | {message_data['id']} |")
        md_lines.append(f"| Thread ID | {message_data['threadId']} |")
        
        if 'labelIds' in message_data:
            md_lines.append(f"| Labels | {', '.join(message_data['labelIds'])} |")
        
        md_lines.append("")
        md_lines.append("## Message Content")
        md_lines.append("")
        
        # Convert HTML to markdown if available, otherwise use plain text
        if html_body:
            try:
                markdown_body = self.html_converter.handle(html_body)
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
        
        return "\n".join(md_lines)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        # Remove/replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)  # Remove control characters
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename.strip()

    def atomic_write(self, path: Path, content: str, encoding: str = 'utf-8') -> None:
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
                os.fsync(tmp_file.fileno())  # Ensure data written to disk
            # Atomic rename (on POSIX; best-effort on Windows)
            os.replace(tmp_path, path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def download_emails(self, 
                       query: str = '', 
                       max_emails: int = 100,
                       output_dir: str = 'gmail_backup',
                       format_type: str = 'both',  # 'eml', 'markdown', or 'both'
                       organize_by: str = 'date',  # 'date', 'sender', or 'none'
                       skip: int = 0):
        """Download emails and save as files"""
        
        if not self.service:
            self.logger.error("Not authenticated. Run authenticate() first.")
            return
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Search for messages
        message_ids = self.search_messages(query, max_emails)
        
        # Skip the first N messages if requested
        if skip:
            if skip >= len(message_ids):
                self.logger.info("No messages to download after skipping requested amount")
                return
            message_ids = message_ids[skip:]

        if not message_ids:
            self.logger.info("No messages found")
            return

        self.logger.info(f"Downloading {len(message_ids)} emails...")
        
        downloaded = 0
        errors = 0
        
        for i, message_id in enumerate(message_ids, 1):
            try:
                self.logger.debug(f"Processing {i}/{len(message_ids)}: {message_id}")

                # Get message details
                message_data = self.get_message_details(message_id)
                if not message_data:
                    self.logger.warning(f"Failed to fetch message {message_id}")
                    errors += 1
                    continue
                
                # Extract headers for filename
                headers = self.extract_headers(message_data['payload'].get('headers', []))
                
                # Create filename
                date_str = headers.get('date', 'unknown_date')
                subject = headers.get('subject', 'no_subject')
                sender = headers.get('from', 'unknown_sender')
                
                # Parse date for organization
                try:
                    from email.utils import parsedate_to_datetime
                    date_obj = parsedate_to_datetime(date_str)
                    date_prefix = date_obj.strftime('%Y-%m-%d_%H%M%S')
                    folder_date = date_obj.strftime('%Y/%m')
                except:
                    date_prefix = 'unknown_date'
                    folder_date = 'unknown'
                
                # Create subdirectory based on organization preference
                if organize_by == 'date':
                    sub_dir = Path(output_dir) / folder_date
                elif organize_by == 'sender':
                    sender_clean = self.sanitize_filename(sender.split('@')[0] if '@' in sender else sender)
                    sub_dir = Path(output_dir) / sender_clean
                else:
                    sub_dir = Path(output_dir)
                
                sub_dir.mkdir(parents=True, exist_ok=True)
                
                # Create base filename
                base_filename = f"{date_prefix}_{self.sanitize_filename(subject)}_{message_id}"
                
                # Save in requested formats
                if format_type in ['eml', 'both']:
                    eml_content = self.create_eml_content(message_data)
                    eml_path = sub_dir / f"{base_filename}.eml"
                    
                    self.atomic_write(eml_path, eml_content)
                
                if format_type in ['markdown', 'both']:
                    md_content = self.create_markdown_content(message_data)
                    md_path = sub_dir / f"{base_filename}.md"
                    
                    self.atomic_write(md_path, md_content)
                
                self.logger.debug("Email saved successfully")
                downloaded += 1

            except HttpError as e:
                self.logger.error(f"API error downloading email: {e}")
                errors += 1
            except (OSError, IOError) as e:
                self.logger.error(f"File system error: {e}")
                errors += 1
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Email parsing error: {e}")
                errors += 1
        
        self.logger.info(f"Download complete: {downloaded} successful, {errors} errors")
        self.logger.info(f"Output directory: {output_dir}")

def main():
    """Main function with CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gmail Email Fetcher and Backup Tool')
    parser.add_argument('--query', '-q', default='', help='Gmail search query (default: all emails)')
    parser.add_argument('--max', '-m', type=int, default=100, help='Maximum emails to download (default: 100)')
    parser.add_argument('--output', '-o', default='gmail_backup', help='Output directory (default: gmail_backup)')
    parser.add_argument('--format', '-f', choices=['eml', 'markdown', 'both'], default='both', 
                       help='Output format (default: both)')
    parser.add_argument('--organize', choices=['date', 'sender', 'none'], default='date',
                       help='How to organize files (default: date)')
    parser.add_argument('--auth-only', action='store_true', help='Only run authentication')
    parser.add_argument('--count-only', action='store_true', help='Only print count of matching messages (no download)')
    parser.add_argument('--skip', type=int, default=0, help='Skip first N matching messages before downloading')
    
    args = parser.parse_args()
    
    # Initialize fetcher
    fetcher = GmailFetcher()
    
    # Authenticate
    if not fetcher.authenticate():
        return 1
    
    if args.auth_only:
        profile = fetcher.get_profile()
        if profile:
            print(f"📧 Gmail account: {profile['email']}")
            print(f"📊 Total messages: {profile['total_messages']:,}")
            print(f"🧵 Total threads: {profile['total_threads']:,}")
        return 0
    
    # Count only mode
    if args.count_only:
        # Use provided --max as an upper bound; pass a large number to count more
        max_for_count = args.max if args.max else 1000000
        ids = fetcher.search_messages(args.query, max_for_count)
        print(f"Total matching messages (up to {max_for_count}): {len(ids)}")
        return 0
    
    # Download emails
    # If skipping, fetch extra and slice inside download_emails by passing adjusted max
    # We'll pass skip via a simple wrapper: expand max here and let download_emails slice.
    fetcher.download_emails(
        query=args.query,
        max_emails=args.max + (args.skip or 0),
        output_dir=args.output,
        format_type=args.format,
        organize_by=args.organize,
        skip=args.skip or 0
    )
    
    return 0

if __name__ == '__main__':
    exit(main())
