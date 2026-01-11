#!/usr/bin/env python3
"""
Email Plaintext Processor

This script adds a new column 'plain_text_content' to the emails database table
and populates it with clean, readable plain text versions of the email content
by stripping all markdown formatting while preserving spacing and readability.

Usage:
    python email_plaintext_processor.py --db emails.db [--batch-size 100] [--dry-run]

Author: Gmail Fetcher System
Date: 2025-09-18
"""

import argparse
import html
import logging
import re
import sqlite3
import sys
from datetime import datetime


class EmailPlaintextProcessor:
    """Process emails to extract plain text content from markdown-formatted messages."""

    def __init__(self, db_path: str, batch_size: int = 100):
        """
        Initialize the processor.

        Args:
            db_path: Path to the SQLite database file
            batch_size: Number of emails to process in each batch
        """
        self.db_path = db_path
        self.batch_size = batch_size
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        from pathlib import Path
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'email_plaintext_processor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    def add_plaintext_column(self) -> bool:
        """
        Add the plain_text_content column to the emails table if it doesn't exist.

        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            # Use timeout and WAL mode for better concurrent access
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            cursor = conn.cursor()

            # Check if column already exists
            cursor.execute("PRAGMA table_info(emails)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'plain_text_content' not in columns:
                self.logger.info("Adding plain_text_content column to emails table...")
                cursor.execute("""
                    ALTER TABLE emails
                    ADD COLUMN plain_text_content TEXT
                """)
                conn.commit()
                self.logger.info("Column added successfully")
            else:
                self.logger.info("plain_text_content column already exists")

            return True

        except Exception as e:
            self.logger.error(f"Error adding column: {e}")
            self.logger.error(f"Database path: {self.db_path}")
            self.logger.error(f"Error type: {type(e).__name__}")
            return False
        finally:
            if conn:
                conn.close()

    def markdown_to_plaintext(self, markdown_content: str) -> str:
        """
        Convert markdown content to clean, readable plain text.

        Args:
            markdown_content: The markdown-formatted email content

        Returns:
            Clean plain text with preserved spacing and readability
        """
        if not markdown_content:
            return ""

        # Start with the original content
        text = markdown_content

        # Decode HTML entities first
        text = html.unescape(text)

        # Remove markdown table syntax but preserve content
        # Handle table rows: | cell1 | cell2 | -> cell1 cell2
        text = re.sub(r'\|\s*([^|]+?)\s*\|', r'\1', text)
        # Remove table separators: | --- | --- |
        text = re.sub(r'\|\s*-+\s*\|', '', text)
        # Remove standalone table markers
        text = re.sub(r'^\|\s*\|\s*$', '', text, flags=re.MULTILINE)

        # Remove markdown headers but keep the text
        text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)

        # Remove bold and italic formatting but keep text
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_

        # Convert links to readable format: [text](url) -> text (url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)

        # Remove inline code backticks
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove code block syntax
        text = re.sub(r'^```.*?$', '', text, flags=re.MULTILINE)

        # Remove blockquote markers but keep indentation
        text = re.sub(r'^>\s*', '  ', text, flags=re.MULTILINE)

        # Remove horizontal rules
        text = re.sub(r'^[-=]{3,}$', '', text, flags=re.MULTILINE)

        # Remove list markers but keep indentation and content
        text = re.sub(r'^\s*[-*+]\s+', '  • ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '  ', text, flags=re.MULTILINE)

        # Remove escape characters
        text = re.sub(r'\\(.)', r'\1', text)

        # Clean up excessive whitespace while preserving paragraph breaks
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        # Replace multiple newlines with double newlines (paragraph breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove leading/trailing whitespace from each line but preserve indentation
        lines = []
        for line in text.split('\n'):
            # Only strip trailing whitespace, preserve leading spaces for indentation
            lines.append(line.rstrip())

        text = '\n'.join(lines)

        # Remove leading and trailing empty lines
        text = text.strip()

        return text

    def process_emails_batch(self, offset: int, limit: int, dry_run: bool = False) -> tuple[int, int]:
        """
        Process a batch of emails to extract plain text content.

        Args:
            offset: Starting position for the batch
            limit: Number of emails to process
            dry_run: If True, don't actually update the database

        Returns:
            Tuple of (processed_count, error_count)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            cursor = conn.cursor()

            # Fetch batch of emails that need processing
            cursor.execute("""
                SELECT id, message_content, subject
                FROM emails
                WHERE plain_text_content IS NULL OR plain_text_content = ''
                LIMIT ? OFFSET ?
            """, (limit, offset))

            emails = cursor.fetchall()
            processed_count = 0
            error_count = 0

            for email_id, message_content, subject in emails:
                try:
                    # Convert to plain text
                    plain_text = self.markdown_to_plaintext(message_content or "")

                    if not dry_run:
                        # Update the database
                        cursor.execute("""
                            UPDATE emails
                            SET plain_text_content = ?
                            WHERE id = ?
                        """, (plain_text, email_id))

                    processed_count += 1

                    # Log progress for every 10th email or if subject is interesting
                    if processed_count % 10 == 0 or len(plain_text) > 1000:
                        preview = plain_text[:100].replace('\n', ' ') + '...' if len(plain_text) > 100 else plain_text
                        self.logger.debug(f"Processed email {email_id}: '{subject[:50]}...' -> '{preview}'")

                except Exception as e:
                    self.logger.error(f"Error processing email {email_id}: {e}")
                    error_count += 1

            if not dry_run:
                conn.commit()

            return processed_count, error_count

        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            return 0, 1
        finally:
            if conn:
                conn.close()

    def get_processing_stats(self) -> tuple[int, int]:
        """
        Get statistics about emails needing processing.

        Returns:
            Tuple of (total_emails, emails_needing_processing)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM emails")
            total_emails = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM emails
                WHERE plain_text_content IS NULL OR plain_text_content = ''
            """)
            emails_needing_processing = cursor.fetchone()[0]

            return total_emails, emails_needing_processing

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return 0, 0
        finally:
            if conn:
                conn.close()

    def process_all_emails(self, dry_run: bool = False) -> bool:
        """
        Process all emails in the database to extract plain text content.

        Args:
            dry_run: If True, don't actually update the database

        Returns:
            True if successful, False otherwise
        """
        try:
            total_emails, emails_needing_processing = self.get_processing_stats()

            if emails_needing_processing == 0:
                self.logger.info("All emails already have plain text content")
                return True

            self.logger.info(f"Processing {emails_needing_processing} of {total_emails} emails...")

            total_processed = 0
            total_errors = 0
            offset = 0

            while offset < emails_needing_processing:
                self.logger.info(f"Processing batch {offset // self.batch_size + 1} "
                               f"({offset + 1}-{min(offset + self.batch_size, emails_needing_processing)} "
                               f"of {emails_needing_processing})")

                processed, errors = self.process_emails_batch(offset, self.batch_size, dry_run)

                total_processed += processed
                total_errors += errors
                offset += self.batch_size

                # Break if no more emails were processed
                if processed == 0:
                    break

            self.logger.info(f"Processing complete: {total_processed} processed, {total_errors} errors")

            if not dry_run:
                # Verify final stats
                _, remaining = self.get_processing_stats()
                self.logger.info(f"Emails still needing processing: {remaining}")

            return total_errors == 0

        except Exception as e:
            self.logger.error(f"Error in process_all_emails: {e}")
            return False

    def show_sample_comparison(self, limit: int = 3) -> None:
        """
        Show sample comparison of original vs plain text content.

        Args:
            limit: Number of samples to show
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT subject, message_content, plain_text_content
                FROM emails
                WHERE plain_text_content IS NOT NULL AND plain_text_content != ''
                LIMIT ?
            """, (limit,))

            samples = cursor.fetchall()

            print("\n" + "="*80)
            print("SAMPLE COMPARISONS - Original vs Plain Text")
            print("="*80)

            for i, (subject, original, plain_text) in enumerate(samples, 1):
                print(f"\n--- Sample {i}: {subject[:60]}... ---")

                print("\nORIGINAL (first 200 chars):")
                print("-" * 40)
                print(original[:200] + "..." if len(original) > 200 else original)

                print("\nPLAIN TEXT (first 200 chars):")
                print("-" * 40)
                print(plain_text[:200] + "..." if len(plain_text) > 200 else plain_text)
                print("\n" + "-"*80)

        except Exception as e:
            self.logger.error(f"Error showing samples: {e}")
        finally:
            if conn:
                conn.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process emails to extract plain text content from markdown formatting"
    )

    parser.add_argument(
        '--db',
        required=True,
        help='Path to the SQLite database file'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of emails to process in each batch (default: 100)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without making changes'
    )

    parser.add_argument(
        '--sample',
        action='store_true',
        help='Show sample comparisons of processed content'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create processor instance
    processor = EmailPlaintextProcessor(args.db, args.batch_size)

    print("Email Plaintext Processor")
    print(f"Database: {args.db}")
    print(f"Batch size: {args.batch_size}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 50)

    # Add column if needed
    if not processor.add_plaintext_column():
        print("Failed to add column. Exiting.")
        sys.exit(1)

    # Show current stats
    total_emails, emails_needing_processing = processor.get_processing_stats()
    print(f"Total emails in database: {total_emails}")
    print(f"Emails needing processing: {emails_needing_processing}")

    if args.sample:
        processor.show_sample_comparison()
        return

    if emails_needing_processing == 0:
        print("All emails already processed!")
        processor.show_sample_comparison()
        return

    # Confirm before processing
    if not args.dry_run:
        response = input(f"\nProcess {emails_needing_processing} emails? (y/N): ")
        if response.lower() != 'y':
            print("Processing cancelled.")
            return

    # Process all emails
    start_time = datetime.now()
    success = processor.process_all_emails(args.dry_run)
    end_time = datetime.now()

    duration = end_time - start_time
    print(f"\nProcessing {'simulation' if args.dry_run else 'completed'} in {duration}")

    if success:
        print("✅ Processing completed successfully!")
        if not args.dry_run:
            processor.show_sample_comparison()
    else:
        print("❌ Processing completed with errors. Check the log file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
