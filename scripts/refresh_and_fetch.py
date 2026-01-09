#!/usr/bin/env python3
"""
Simple script to refresh OAuth token and fetch new emails
"""

import json
import logging
import requests
from datetime import datetime
from pathlib import Path
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import centralized constants
from src.core.constants import DEFAULT_DB_PATH, DEFAULT_TOKEN_PATH

def refresh_token():
    """Refresh the OAuth token using refresh_token"""
    try:
        with open(DEFAULT_TOKEN_PATH, 'r') as f:
            token_data = json.load(f)

        # Token refresh request
        refresh_payload = {
            'client_id': token_data['client_id'],
            'client_secret': token_data['client_secret'],
            'refresh_token': token_data['refresh_token'],
            'grant_type': 'refresh_token'
        }

        response = requests.post('https://oauth2.googleapis.com/token', data=refresh_payload)

        if response.status_code == 200:
            new_token_data = response.json()

            # Update token file
            token_data['token'] = new_token_data['access_token']
            token_data['expiry'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

            with open(DEFAULT_TOKEN_PATH, 'w') as f:
                json.dump(token_data, f)

            logger.info("Token refreshed successfully")
            return True
        else:
            logger.error(f" Token refresh failed: {response.status_code}")
            logger.error(response.text)
            return False

    except Exception as e:
        logger.error(f" refreshing token: {e}")
        return False

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
        logger.error(f" reading database: {e}")
        return None

def main():
    logger.info("Refreshing OAuth token...")
    if not refresh_token():
        return False

    logger.info("Getting latest email date from database...")
    latest_date = get_latest_email_date()
    if not latest_date:
        logger.error("Could not determine latest email date")
        return False

    print(f"[INFO] Latest email date: {latest_date}")
    query = f"after:{latest_date}"
    print(f"[INFO] Gmail query: {query}")

    # Now use the main CLI with refreshed token
    import subprocess
    import sys

    logger.info("Starting email fetch...")
    cmd = [
        sys.executable, 'main.py', 'fetch',
        '--query', query,
        '--max', '1000',
        '--output', 'incremental_backup',
        '--format', 'eml'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            logger.info("Email fetch completed successfully!")
            logger.debug(result.stdout)
            return True
        else:
            logger.error("Email fetch failed!")
            logger.debug(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        logger.error("Fetch timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error during fetch: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Incremental fetch process completed!")
    else:
        logger.error("Process failed!")