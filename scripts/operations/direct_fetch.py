#!/usr/bin/env python3
"""
Direct Gmail API fetch without CLI wrapper
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct Gmail API imports
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Import centralized constants
from src.core.constants import DEFAULT_DB_PATH, DEFAULT_TOKEN_PATH

def load_credentials():
    """Load OAuth credentials from token.json"""
    try:
        with open(DEFAULT_TOKEN_PATH, 'r') as f:
            token_data = json.load(f)

        creds = Credentials(
            token=token_data['token'],
            refresh_token=token_data['refresh_token'],
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )

        return creds
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        return None

def get_latest_email_date():
    """Get latest email date from database"""
    try:
        conn = sqlite3.connect(str(DEFAULT_DB_PATH))
        cursor = conn.cursor()
        cursor.execute('SELECT parsed_date FROM emails ORDER BY parsed_date DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()

        if result:
            # Convert to Gmail API format
            latest_date = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
            return latest_date.strftime('%Y/%m/%d')
        return None
    except Exception as e:
        logger.error(f"Error reading database: {e}")
        return None

def fetch_emails():
    """Fetch emails directly using Gmail API"""
    logger.info("Loading credentials...")
    creds = load_credentials()
    if not creds:
        return False

    logger.info("Building Gmail service...")
    service = build('gmail', 'v1', credentials=creds)

    logger.info("Getting latest email date...")
    latest_date = get_latest_email_date()
    if not latest_date:
        logger.error("Could not determine latest email date")
        return False

    query = f"after:{latest_date}"
    logger.info(f" Query: {query}")

    try:
        logger.info("Searching for messages...")
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=500  # Get all available emails
        ).execute()

        messages = results.get('messages', [])
        logger.info(f" Found {len(messages)} messages")

        if not messages:
            logger.info("No new messages found")
            return True

        # Create output directory
        output_dir = Path('incremental_backup')
        output_dir.mkdir(exist_ok=True)

        logger.info(f" Downloading {len(messages)} emails...")
        successful_downloads = 0

        for i, message in enumerate(messages, 1):
            try:
                # Get full message
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='raw'
                ).execute()

                # Decode the raw email
                import base64
                raw_email = base64.urlsafe_b64decode(msg['raw']).decode('utf-8')

                # Generate filename
                filename = f"email_{message['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i:03d}.eml"
                file_path = output_dir / filename

                # Save EML file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(raw_email)

                successful_downloads += 1
                logger.info(f" Downloaded {i}/{len(messages)}: {filename}")

            except Exception as e:
                logger.warning(f"Failed to download message {message['id']}: {e}")
                continue

        logger.info(f" Downloaded {successful_downloads}/{len(messages)} emails to {output_dir}")
        return True

    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return False

def main():
    logger.info("Starting direct Gmail fetch...")

    if fetch_emails():
        logger.info("Fetch completed successfully!")

        # List downloaded files
        output_dir = Path('incremental_backup')
        if output_dir.exists():
            eml_files = list(output_dir.glob('*.eml'))
            logger.info(f"Files in {output_dir}:")
            for f in sorted(eml_files):
                size_kb = f.stat().st_size / 1024
                logger.info(f"  {f.name} ({size_kb:.1f} KB)")

        return True
    else:
        logger.error("Fetch failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)