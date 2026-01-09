#!/usr/bin/env python3
"""
Fetch remaining emails after the initial batch
"""

import json
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def load_credentials():
    """Load OAuth credentials"""
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)

        return Credentials(
            token=token_data['token'],
            refresh_token=token_data['refresh_token'],
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
    except Exception as e:
        print(f"[ERROR] Failed to load credentials: {e}")
        return None

def main():
    print("[INFO] Checking for additional emails...")

    creds = load_credentials()
    if not creds:
        return False

    service = build('gmail', 'v1', credentials=creds)

    query = "after:2025/09/18"

    try:
        # Get total count
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=500  # Check up to 500
        ).execute()

        messages = results.get('messages', [])
        total_found = len(messages)

        print(f"[INFO] Total emails found with query '{query}': {total_found}")

        # Check how many we already have
        backup_dir = Path('incremental_backup')
        if backup_dir.exists():
            existing_files = list(backup_dir.glob('*.eml'))
            print(f"[INFO] Already downloaded: {len(existing_files)} files")
            remaining = total_found - len(existing_files)
            print(f"[INFO] Remaining to download: {remaining}")

            if remaining > 0:
                print(f"[ACTION] You can fetch the remaining {remaining} emails by running:")
                print(f"[ACTION] python direct_fetch.py (but modify maxResults to {total_found})")
                return True
            else:
                print("[COMPLETE] All emails have been downloaded!")
                return True
        else:
            print("[INFO] No backup directory found")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to check emails: {e}")
        return False

if __name__ == "__main__":
    main()