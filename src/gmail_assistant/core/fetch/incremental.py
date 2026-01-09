#!/usr/bin/env python3
"""
Incremental Gmail Fetcher

Automated script that:
1. Reads the latest email date from emails_final.db
2. Constructs incremental Gmail query with after: parameter
3. Fetches new emails as EML format only
4. Converts EML to markdown using the most accurate method available
5. Waits for user validation of markdown output

Usage:
    python src/core/incremental_fetcher.py [--db-path path] [--max-emails n] [--output dir]
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple
import argparse
import logging
import subprocess

from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IncrementalGmailFetcher:
    """Automated incremental Gmail fetcher with EML to Markdown conversion"""

    def __init__(self, db_path: str = "data/databases/emails_final.db"):
        self.db_path = Path(db_path)
        self.fetcher = None

    def get_latest_email_date(self) -> Optional[str]:
        """
        Query database for the latest email date to use as starting point.

        Returns:
            Latest email date in YYYY/MM/DD format for Gmail API, or None if no emails
        """
        if not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get the latest parsed_date from emails table
            cursor.execute("""
                SELECT parsed_date
                FROM emails
                WHERE parsed_date IS NOT NULL
                ORDER BY parsed_date DESC
                LIMIT 1
            """)

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                # Parse the ISO datetime and convert to Gmail API format
                latest_date = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                gmail_date = latest_date.strftime('%Y/%m/%d')
                logger.info(f"Latest email in database: {result[0]} -> Gmail query: after:{gmail_date}")
                return gmail_date
            else:
                logger.warning("No emails found in database")
                return None

        except Exception as e:
            logger.error(f"Error reading database: {e}")
            return None

    def fetch_incremental_emails(self,
                                max_emails: int = 1000,
                                output_dir: str = "incremental_backup") -> Tuple[bool, str]:
        """
        Fetch emails since the last stored email date.

        Args:
            max_emails: Maximum number of emails to fetch
            output_dir: Directory to save EML files

        Returns:
            Tuple of (success, output_directory_path)
        """
        latest_date = self.get_latest_email_date()
        if not latest_date:
            logger.error("Cannot determine latest email date - aborting incremental fetch")
            return False, ""

        # Construct Gmail query for emails after the latest date
        query = f"after:{latest_date}"
        logger.info(f"Fetching emails with query: {query}")

        # Initialize Gmail fetcher with correct credentials path
        credentials_path = "config/security/credentials.json"
        self.fetcher = GmailFetcher(credentials_path)
        if not self.fetcher.authenticate():
            logger.error("Gmail authentication failed")
            return False, ""

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Search for new emails
            message_ids = self.fetcher.search_messages(query=query, max_results=max_emails)

            if not message_ids:
                logger.info("No new emails found since last fetch")
                return True, str(output_path)

            logger.info(f"Found {len(message_ids)} new emails to fetch")

            # Download emails as EML format only
            successful_downloads = 0
            for i, message_id in enumerate(message_ids, 1):
                try:
                    email_data = self.fetcher.get_message_details(message_id)
                    if email_data:
                        # Generate filename from email metadata
                        received_date = email_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        try:
                            # Try to parse the received date
                            parsed_date = datetime.strptime(received_date.split(' (')[0], '%a, %d %b %Y %H:%M:%S %z')
                            date_str = parsed_date.strftime('%Y-%m-%d_%H%M%S')
                            # Create year/month folder structure
                            year_month_dir = output_path / str(parsed_date.year) / f"{parsed_date.month:02d}"
                        except:
                            # Fallback to current time
                            fallback_date = datetime.now()
                            date_str = fallback_date.strftime('%Y-%m-%d_%H%M%S')
                            year_month_dir = output_path / str(fallback_date.year) / f"{fallback_date.month:02d}"

                        # Create year/month directory
                        year_month_dir.mkdir(parents=True, exist_ok=True)

                        subject = email_data.get('subject', 'no_subject')[:50]
                        # Sanitize subject for filename
                        import re
                        subject = re.sub(r'[<>:"/\\|?*]', '_', subject)
                        filename = f"{date_str}_{subject}_{message_id[:16]}.eml"

                        # Save as EML in organized structure
                        eml_path = year_month_dir / filename
                        with open(eml_path, 'w', encoding='utf-8') as f:
                            f.write(email_data.get('raw_content', ''))

                        successful_downloads += 1
                        logger.info(f"Downloaded {i}/{len(message_ids)}: {filename}")

                except Exception as e:
                    logger.error(f"Error downloading email {message_id}: {e}")

            logger.info(f"Successfully downloaded {successful_downloads}/{len(message_ids)} emails to {output_path}")
            return True, str(output_path)

        except Exception as e:
            logger.error(f"Error during email fetch: {e}")
            return False, ""


    def run_incremental_fetch(self,
                             max_emails: int = 1000,
                             output_dir: str = "data/fetched_emails") -> bool:
        """
        Complete incremental fetch workflow - EML files only.

        Args:
            max_emails: Maximum emails to fetch
            output_dir: Output directory for EML files

        Returns:
            Success status
        """
        logger.info("Starting incremental Gmail fetch (EML only)...")

        # Fetch emails as EML
        success, eml_dir = self.fetch_incremental_emails(max_emails, output_dir)
        if not success:
            return False

        # Display results
        print(f"\n{'='*60}")
        print(f"INCREMENTAL FETCH COMPLETE")
        print(f"{'='*60}")
        print(f"EML files saved to: {eml_dir}")

        # Count files for summary (including subdirectories)
        eml_files = list(Path(eml_dir).glob("**/*.eml"))
        print(f"Total files: {len(eml_files)}")

        # Convert EML files to Markdown
        if eml_files:
            print("\nConverting EML files to Markdown...")
            self.convert_eml_to_markdown(eml_dir)

        input("\nPress Enter after you have reviewed the EML and Markdown files...")

        logger.info("Incremental fetch finished successfully.")
        return True

    def convert_eml_to_markdown(self, eml_dir: str) -> bool:
        """
        Convert all EML files in the directory to markdown using the gmail_eml_to_markdown_cleaner.

        Args:
            eml_dir: Directory containing EML files in year/month structure

        Returns:
            Success status
        """
        try:
            # Use subprocess to call the EML to markdown converter
            converter_script = "src/parsers/gmail_eml_to_markdown_cleaner.py"

            # Run the converter with the data/fetched_emails directory
            cmd = [
                sys.executable,
                converter_script,
                "--base", eml_dir,
                "--output", f"{eml_dir}_markdown"
            ]

            logger.info(f"Running EML to markdown conversion: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")

            if result.returncode == 0:
                logger.info("EML to markdown conversion completed successfully")
                print(f"Markdown files saved to: {eml_dir}_markdown")
                return True
            else:
                logger.error(f"EML to markdown conversion failed: {result.stderr}")
                print(f"Conversion error: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error during EML to markdown conversion: {e}")
            print(f"Conversion error: {e}")
            return False


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Incremental Gmail Fetcher")
    parser.add_argument(
        "--db-path",
        default="data/databases/emails_final.db",
        help="Path to emails database"
    )
    parser.add_argument(
        "--max-emails",
        type=int,
        default=1000,
        help="Maximum emails to fetch"
    )
    parser.add_argument(
        "--output",
        default="data/fetched_emails",
        help="Output directory"
    )

    args = parser.parse_args()

    # Create fetcher
    fetcher = IncrementalGmailFetcher(args.db_path)

    # Run incremental fetch
    success = fetcher.run_incremental_fetch(
        max_emails=args.max_emails,
        output_dir=args.output
    )

    if success:
        print("\n[SUCCESS] Incremental fetch completed successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Incremental fetch failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()