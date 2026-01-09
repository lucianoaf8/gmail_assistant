#!/usr/bin/env python3
"""
Gmail API Integration for AI Newsletter Cleaner
Handles actual Gmail operations via Google API
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from ..ai.newsletter_cleaner import EmailData, AINewsletterDetector
from ..constants import SCOPES_MODIFY

logger = logging.getLogger(__name__)

class GmailAPIClient:
    """Gmail API client for actual email operations"""

    SCOPES = SCOPES_MODIFY
    
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Gmail API using secure JSON token storage."""
        creds = None

        # Load existing token from JSON (secure deserialization)
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                logger.info("Loaded credentials from JSON token file")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Invalid token file, will re-authenticate: {e}")
                creds = None

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("Completed OAuth flow for new credentials")

            # Save credentials as JSON (secure serialization)
            with open(self.token_path, 'w', encoding='utf-8') as token:
                token.write(creds.to_json())
            logger.info(f"Saved credentials to {self.token_path}")

        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail API authentication successful")
    
    def fetch_unread_emails(self, max_results: int = 2938) -> List[EmailData]:
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
            
        except Exception as e:
            print(f"❌ Error fetching emails: {str(e)}")
            return []
    
    def _fetch_email_batch(self, message_ids: List[Dict]) -> List[EmailData]:
        """Fetch a batch of emails efficiently"""
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
                
            except Exception as e:
                print(f"⚠️  Warning: Failed to fetch email {msg_id['id']}: {str(e)}")
                continue
        
        return emails
    
    def delete_emails(self, email_ids: List[str]) -> Dict[str, int]:
        """Delete emails by ID"""
        deleted_count = 0
        failed_count = 0
        
        print(f"🗑️  Deleting {len(email_ids)} emails...")
        
        for i, email_id in enumerate(email_ids):
            try:
                self.service.users().messages().delete(
                    userId='me', 
                    id=email_id
                ).execute()
                deleted_count += 1
                
                if (i + 1) % 50 == 0:
                    print(f"  Deleted {i + 1}/{len(email_ids)} emails...")
                    
            except Exception as e:
                print(f"⚠️  Failed to delete email {email_id}: {str(e)}")
                failed_count += 1
        
        return {'deleted': deleted_count, 'failed': failed_count}
    
    def trash_emails(self, email_ids: List[str]) -> Dict[str, int]:
        """Move emails to trash instead of permanent deletion"""
        trashed_count = 0
        failed_count = 0
        
        print(f"🗑️  Moving {len(email_ids)} emails to trash...")
        
        for i, email_id in enumerate(email_ids):
            try:
                self.service.users().messages().trash(
                    userId='me', 
                    id=email_id
                ).execute()
                trashed_count += 1
                
                if (i + 1) % 50 == 0:
                    print(f"  Trashed {i + 1}/{len(email_ids)} emails...")
                    
            except Exception as e:
                print(f"⚠️  Failed to trash email {email_id}: {str(e)}")
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
            print(f"\n⚠️  DRY RUN MODE - No emails were actually deleted")
            print(f"🔄 Use --delete or --trash to perform actual operation")
        
        print(f"📝 Detailed log saved to: {log_file}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
