#!/usr/bin/env python3
"""
Gmail API Integration for AI Newsletter Cleaner
Handles actual Gmail operations via Google API

Security: Uses SecureCredentialManager for OS keyring storage (H-1 fix)
"""

import json
import logging
import os
from datetime import datetime

from googleapiclient.errors import HttpError

from gmail_assistant.core.ai.newsletter_cleaner import AINewsletterDetector, EmailData
from gmail_assistant.core.auth.credential_manager import SecureCredentialManager
from gmail_assistant.core.constants import SCOPES_MODIFY
from gmail_assistant.core.exceptions import AuthError

from .batch_api import BatchAPIError, GmailBatchClient

logger = logging.getLogger(__name__)


class GmailAPIClient:
    """Gmail API client for actual email operations with secure credential storage"""

    SCOPES = SCOPES_MODIFY

    def __init__(self, credentials_path: str = 'credentials.json'):
        """
        Initialize Gmail API client with secure credential management.

        Args:
            credentials_path: Path to OAuth client credentials file
        """
        self.credentials_path = credentials_path
        # Use SecureCredentialManager for keyring-based storage (H-1 security fix)
        self.credential_manager = SecureCredentialManager(credentials_path)
        self.service = None
        self.batch_client = None  # C-1: Batch API client
        self._authenticate()
        self._migrate_legacy_tokens()

    def _authenticate(self):
        """Authenticate with Gmail API using secure keyring storage."""
        try:
            if self.credential_manager.authenticate():
                self.service = self.credential_manager.get_service()
                # C-1: Initialize batch client for efficient bulk operations
                if self.service:
                    self.batch_client = GmailBatchClient(self.service)
                logger.info("Gmail API authentication successful via SecureCredentialManager")
                print("Gmail API authentication successful")
            else:
                logger.error("Gmail API authentication failed")
                raise AuthError("Failed to authenticate with Gmail API")
        except AuthError:
            raise
        except OSError as e:
            logger.error(f"Credential file error: {e}")
            raise AuthError(f"Credential file error: {e}") from e
        except HttpError as e:
            logger.error(f"Google API auth error: {e}")
            raise AuthError(f"Google API auth error: {e}") from e

    def _migrate_legacy_tokens(self):
        """One-time migration notice for legacy plaintext tokens."""
        legacy_token_paths = ['token.json', 'config/token.json', 'config/security/token.json']
        for legacy_path in legacy_token_paths:
            if os.path.exists(legacy_path):
                logger.warning(f"Found legacy token file: {legacy_path}")
                logger.info("Credentials are now stored securely in OS keyring")
                logger.info(f"You may safely delete the legacy token file: {legacy_path}")
                print(f"Note: Legacy token file found at {legacy_path} - credentials now use secure keyring storage")

    def fetch_unread_emails(self, max_results: int = 2938) -> list[EmailData]:
        """Fetch unread emails from Gmail"""
        print(f"📥 Fetching up to {max_results} unread emails...")

        try:
            # Get unread email IDs
            query = 'is:unread'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            print(f"Found {len(messages)} unread emails")

            emails = []
            batch_size = 100

            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                batch_emails = self._fetch_email_batch(batch)
                emails.extend(batch_emails)
                print(f"  Loaded {min(i + batch_size, len(messages))}/{len(messages)} emails...")

            return emails

        except HttpError as e:
            logger.error(f"Gmail API error fetching emails: {e}")
            print(f"❌ Gmail API error: {e!s}")
            return []
        except (OSError, ConnectionError) as e:
            logger.error(f"Network/IO error fetching emails: {e}")
            print(f"❌ Network error: {e!s}")
            return []

    def _fetch_email_batch(self, message_ids: list[dict]) -> list[EmailData]:
        """Fetch a batch of emails using Batch API (C-1 fix)."""
        if not self.batch_client:
            logger.warning("Batch client not initialized, falling back to sequential")
            return self._fetch_email_batch_sequential(message_ids)

        try:
            # Extract IDs from dicts
            ids = [msg['id'] for msg in message_ids]

            # Use batch API for 80-90% performance improvement
            emails = self.batch_client.batch_get_messages(
                ids,
                format='metadata',
                metadata_headers=['From', 'Subject', 'Date']
            )

            # Convert Email objects to EmailData for backward compatibility
            return [
                EmailData(
                    id=email.gmail_id,
                    subject=email.subject,
                    sender=email.sender,
                    date=email.date.isoformat() if email.date else '',
                    thread_id=email.thread_id,
                    labels=email.labels,
                    body_snippet=email.snippet
                )
                for email in emails
            ]
        except (BatchAPIError, HttpError) as e:
            logger.warning(f"Batch API failed, using sequential: {e}")
            return self._fetch_email_batch_sequential(message_ids)

    def _fetch_email_batch_sequential(self, message_ids: list[dict]) -> list[EmailData]:
        """Fetch emails sequentially (fallback for batch API failure)."""
        emails = []

        for msg_id in message_ids:
            try:
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_id['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in message['payload']['headers']}

                emails.append(EmailData(
                    id=message['id'],
                    subject=headers.get('Subject', ''),
                    sender=headers.get('From', ''),
                    date=headers.get('Date', ''),
                    thread_id=message.get('threadId', ''),
                    labels=message.get('labelIds', []),
                    body_snippet=message.get('snippet', '')
                ))

            except HttpError as e:
                logger.warning(f"API error fetching email {msg_id['id']}: {e}")
                print(f"⚠️  Warning: API error for email {msg_id['id']}: {e!s}")
                continue
            except KeyError as e:
                logger.warning(f"Missing data in email {msg_id['id']}: {e}")
                continue

        return emails

    def delete_emails(self, email_ids: list[str]) -> dict[str, int]:
        """Delete emails by ID using batch API (C-1 fix)."""
        print(f"🗑️  Deleting {len(email_ids)} emails...")

        # Use batch API if available
        if self.batch_client:
            try:
                def progress_callback(current: int, total: int):
                    if current % 50 == 0 or current == total:
                        print(f"  Deleted {current}/{total} emails...")

                result = self.batch_client.batch_delete_messages(
                    email_ids,
                    progress_callback=progress_callback
                )
                return {'deleted': result.successful, 'failed': result.failed}
            except (BatchAPIError, HttpError) as e:
                logger.warning(f"Batch delete failed, using sequential: {e}")

        # Fallback to sequential deletion
        return self._delete_emails_sequential(email_ids)

    def _delete_emails_sequential(self, email_ids: list[str]) -> dict[str, int]:
        """Delete emails sequentially (fallback)."""
        deleted_count = 0
        failed_count = 0

        for i, email_id in enumerate(email_ids):
            try:
                self.service.users().messages().delete(
                    userId='me',
                    id=email_id
                ).execute()
                deleted_count += 1

                if (i + 1) % 50 == 0:
                    print(f"  Deleted {i + 1}/{len(email_ids)} emails...")

            except HttpError as e:
                logger.warning(f"API error deleting email {email_id}: {e}")
                print(f"⚠️  Failed to delete email {email_id}: {e!s}")
                failed_count += 1

        return {'deleted': deleted_count, 'failed': failed_count}

    def trash_emails(self, email_ids: list[str]) -> dict[str, int]:
        """Move emails to trash using batch API (C-1 fix)."""
        print(f"🗑️  Moving {len(email_ids)} emails to trash...")

        # Use batch API if available
        if self.batch_client:
            try:
                def progress_callback(current: int, total: int):
                    if current % 50 == 0 or current == total:
                        print(f"  Trashed {current}/{total} emails...")

                result = self.batch_client.batch_trash_messages(
                    email_ids,
                    progress_callback=progress_callback
                )
                return {'trashed': result.successful, 'failed': result.failed}
            except (BatchAPIError, HttpError) as e:
                logger.warning(f"Batch trash failed, using sequential: {e}")

        # Fallback to sequential
        return self._trash_emails_sequential(email_ids)

    def _trash_emails_sequential(self, email_ids: list[str]) -> dict[str, int]:
        """Trash emails sequentially (fallback)."""
        trashed_count = 0
        failed_count = 0

        for i, email_id in enumerate(email_ids):
            try:
                self.service.users().messages().trash(
                    userId='me',
                    id=email_id
                ).execute()
                trashed_count += 1

                if (i + 1) % 50 == 0:
                    print(f"  Trashed {i + 1}/{len(email_ids)} emails...")

            except HttpError as e:
                logger.warning(f"API error trashing email {email_id}: {e}")
                print(f"⚠️  Failed to trash email {email_id}: {e!s}")
                failed_count += 1

        return {'trashed': trashed_count, 'failed': failed_count}

def main():
    """Main execution function for Gmail API operations"""
    import argparse

    parser = argparse.ArgumentParser(description='Gmail AI Newsletter Cleaner with API')
    parser.add_argument('--credentials', default='credentials.json',
                       help='Path to Gmail API credentials file')
    parser.add_argument('--max-emails', type=int, default=2938,
                       help='Maximum number of emails to process')
    parser.add_argument('--delete', action='store_true',
                       help='Actually delete emails (default: dry run)')
    parser.add_argument('--trash', action='store_true',
                       help='Move to trash instead of permanent deletion')
    parser.add_argument('--save-data', action='store_true',
                       help='Save fetched email data to JSON file')

    args = parser.parse_args()

    # Check credentials file
    if not os.path.exists(args.credentials):
        print(f"❌ Credentials file not found: {args.credentials}")
        print("📋 To set up Gmail API access:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Create a new project or select existing one")
        print("   3. Enable Gmail API")
        print("   4. Create credentials (OAuth 2.0)")
        print("   5. Download and save as 'credentials.json'")
        return

    try:
        # Initialize Gmail client
        gmail_client = GmailAPIClient(args.credentials)

        # Fetch emails
        emails = gmail_client.fetch_unread_emails(args.max_emails)

        if not emails:
            print("No emails found to process")
            return

        # Save data if requested
        if args.save_data:
            data_file = f"gmail_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump([{
                    'id': email.id,
                    'subject': email.subject,
                    'sender': email.sender,
                    'date': email.date,
                    'labels': email.labels,
                    'thread_id': email.thread_id,
                    'snippet': email.body_snippet
                } for email in emails], f, indent=2)
            print(f"📁 Email data saved to: {data_file}")

        # Analyze emails
        detector = AINewsletterDetector()
        ai_newsletters = []

        print(f"\n🔍 Analyzing {len(emails)} emails for AI newsletters...")

        for email in emails:
            result = detector.is_ai_newsletter(email)
            if result['is_ai_newsletter']:
                ai_newsletters.append({
                    'email': email,
                    'analysis': result
                })

        print(f"✅ Found {len(ai_newsletters)} AI newsletters")

        if not ai_newsletters:
            print("No AI newsletters found to delete")
            return

        # Generate log
        log_file = f"gmail_api_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write(f"Gmail API AI Newsletter Cleanup - {datetime.now()}\n")
            log.write(f"Mode: {'TRASH' if args.trash else 'DELETE' if args.delete else 'DRY RUN'}\n\n")

            for item in ai_newsletters:
                email = item['email']
                analysis = item['analysis']

                log.write(f"ID: {email.id}\n")
                log.write(f"Subject: {email.subject}\n")
                log.write(f"From: {email.sender}\n")
                log.write(f"Confidence: {analysis['confidence']}\n")
                log.write(f"Reasons: {', '.join(analysis['reasons'])}\n")
                log.write("-" * 80 + "\n\n")

        # Perform deletion/trashing
        if args.delete or args.trash:
            email_ids = [item['email'].id for item in ai_newsletters]

            if args.trash:
                result = gmail_client.trash_emails(email_ids)
                print(f"✅ Moved {result['trashed']} emails to trash")
            else:
                result = gmail_client.delete_emails(email_ids)
                print(f"✅ Permanently deleted {result['deleted']} emails")

            if result.get('failed', 0) > 0:
                print(f"⚠️  {result['failed']} emails failed to process")
        else:
            print("\n⚠️  DRY RUN MODE - No emails were actually deleted")
            print("🔄 Use --delete or --trash to perform actual operation")

        print(f"📝 Detailed log saved to: {log_file}")

    except AuthError as e:
        print(f"❌ Authentication error: {e!s}")
    except HttpError as e:
        print(f"❌ Gmail API error: {e!s}")
    except OSError as e:
        print(f"❌ File/IO error: {e!s}")

if __name__ == "__main__":
    main()
