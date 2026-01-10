#!/usr/bin/env python3
"""
Incremental Gmail Fetcher

Automated script that:
1. Reads the latest email date from emails_final.db
2. Constructs incremental Gmail query with after: parameter
3. Fetches new emails as EML format only
4. Converts EML to markdown using the most accurate method available
5. Waits for user validation of markdown output

Security: Implements path validation for subprocess calls (H-2 fix)

Usage:
    python src/core/incremental_fetcher.py [--db-path path] [--max-emails n] [--output dir]
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple, List
import argparse
import logging
import subprocess

from gmail_assistant.core.fetch.gmail_assistant import GmailFetcher
from gmail_assistant.core.fetch.checkpoint import CheckpointManager, SyncCheckpoint, SyncState
from gmail_assistant.utils.input_validator import InputValidator, ValidationError

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
        # C-3: Checkpoint manager for resume capability
        self.checkpoint_manager = CheckpointManager()
        self.current_checkpoint: Optional[SyncCheckpoint] = None

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

        except sqlite3.Error as e:
            logger.error(f"Database error reading latest email: {e}")
            return None
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return None

    def fetch_incremental_emails(self,
                                max_emails: int = 1000,
                                output_dir: str = "incremental_backup",
                                resume: bool = False) -> Tuple[bool, str]:
        """
        Fetch emails since the last stored email date.

        Args:
            max_emails: Maximum number of emails to fetch
            output_dir: Directory to save EML files
            resume: Resume from last checkpoint if available (C-3 fix)

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

        # C-3: Check for resumable checkpoint
        skip_count = 0
        if resume:
            existing = self.checkpoint_manager.get_latest_checkpoint(
                query=query,
                resumable_only=True
            )
            if existing:
                logger.info(f"Found resumable checkpoint: {existing.sync_id}")
                resume_info = self.checkpoint_manager.get_resume_info(existing)
                self.current_checkpoint = existing
                skip_count = resume_info['skip_count']
                logger.info(f"Resuming from message {skip_count}")
            else:
                logger.info("No checkpoint found, starting fresh")

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

            # C-3: Create checkpoint if not resuming
            if not self.current_checkpoint:
                self.current_checkpoint = self.checkpoint_manager.create_checkpoint(
                    query=query,
                    output_directory=str(output_path),
                    total_messages=len(message_ids),
                    metadata={'max_emails': max_emails}
                )

            # Update total if resuming
            self.current_checkpoint.total_messages = len(message_ids)

            # Download emails as EML format only
            successful_downloads = 0
            for i, message_id in enumerate(message_ids, 1):
                # C-3: Skip already processed messages when resuming
                if i <= skip_count:
                    continue

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
                        except Exception:
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

                        # C-3: Update checkpoint every 25 emails
                        if successful_downloads > 0 and successful_downloads % 25 == 0:
                            self.checkpoint_manager.update_progress(
                                self.current_checkpoint,
                                processed=i,
                                last_message_id=message_id
                            )

                except Exception as e:
                    logger.error(f"Error downloading email {message_id}: {e}")

            # C-3: Mark checkpoint complete
            if self.current_checkpoint:
                self.checkpoint_manager.mark_completed(self.current_checkpoint)
                self.checkpoint_manager.cleanup_old_checkpoints()

            logger.info(f"Successfully downloaded {successful_downloads}/{len(message_ids)} emails to {output_path}")
            return True, str(output_path)

        except Exception as e:
            # C-3: Mark checkpoint interrupted on failure
            if self.current_checkpoint:
                self.checkpoint_manager.mark_interrupted(self.current_checkpoint)
            logger.error(f"Error during email fetch: {e}")
            return False, ""


    def run_incremental_fetch(self,
                             max_emails: int = 1000,
                             output_dir: str = "data/fetched_emails",
                             resume: bool = False) -> bool:
        """
        Complete incremental fetch workflow - EML files only.

        Args:
            max_emails: Maximum emails to fetch
            output_dir: Output directory for EML files
            resume: Resume from last checkpoint if available (C-3 fix)

        Returns:
            Success status
        """
        logger.info("Starting incremental Gmail fetch (EML only)...")

        # Fetch emails as EML with resume support
        success, eml_dir = self.fetch_incremental_emails(max_emails, output_dir, resume)
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

    def _validate_subprocess_path(self, path: str) -> Path:
        """
        Validate path for safe use in subprocess commands (H-2 security fix).

        Args:
            path: Path string to validate

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is invalid or unsafe
        """
        # Define allowed base directories for subprocess operations
        allowed_bases = [
            Path("data").resolve(),
            Path("backups").resolve(),
            Path.cwd(),
        ]

        # Resolve to absolute path
        resolved = Path(path).resolve()

        # Check for path traversal patterns
        if ".." in str(path):
            raise ValidationError(f"Path traversal detected in: {path}")

        # Verify path is under allowed base directory
        is_safe = any(
            str(resolved).startswith(str(base))
            for base in allowed_bases
        )

        if not is_safe:
            raise ValidationError(
                f"Path {resolved} not under allowed directories: {allowed_bases}"
            )

        # Check for shell metacharacters that could enable injection
        dangerous_chars = ['|', '&', ';', '$', '`', '>', '<', '!', '\n', '\r']
        if any(char in str(path) for char in dangerous_chars):
            raise ValidationError(f"Path contains dangerous characters: {path}")

        return resolved

    def _safe_subprocess_run(self, cmd: list, **kwargs) -> subprocess.CompletedProcess:
        """
        Execute subprocess with security hardening (H-2 security fix).

        Args:
            cmd: Command list (NOT shell string)
            **kwargs: Additional subprocess.run arguments

        Returns:
            CompletedProcess result
        """
        # Ensure shell=False (defense in depth)
        kwargs['shell'] = False

        # Set reasonable timeout (prevent hanging)
        kwargs.setdefault('timeout', 300)  # 5 minutes

        # Capture output for logging
        kwargs.setdefault('capture_output', True)
        kwargs.setdefault('text', True)

        logger.debug(f"Executing subprocess: {cmd}")

        try:
            result = subprocess.run(cmd, **kwargs)
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Subprocess timed out: {cmd}")
            raise

    def convert_eml_to_markdown(self, eml_dir: str) -> bool:
        """
        Convert all EML files in the directory to markdown using the gmail_eml_to_markdown_cleaner.

        Security: Validates paths before subprocess execution (H-2 fix)

        Args:
            eml_dir: Directory containing EML files in year/month structure

        Returns:
            Success status
        """
        try:
            # SECURITY: Validate and sanitize eml_dir before use
            try:
                validated_dir = self._validate_subprocess_path(eml_dir)
            except ValidationError as e:
                logger.error(f"Path validation failed for eml_dir: {e}")
                print(f"Security error: {e}")
                return False

            # Use validated absolute path for converter script
            converter_script = Path(__file__).parent.parent.parent / "parsers" / "gmail_eml_to_markdown_cleaner.py"
            if not converter_script.exists():
                # Fallback to relative path from project root
                converter_script = Path("src/gmail_assistant/parsers/gmail_eml_to_markdown_cleaner.py")

            output_dir = str(validated_dir) + "_markdown"

            # Build command with validated paths
            cmd = [
                sys.executable,
                str(converter_script.resolve()),
                "--base", str(validated_dir),
                "--output", output_dir
            ]

            logger.info(f"Running EML to markdown conversion: {' '.join(cmd)}")

            # Use secure subprocess runner
            result = self._safe_subprocess_run(cmd, cwd=".")

            if result.returncode == 0:
                logger.info("EML to markdown conversion completed successfully")
                print(f"Markdown files saved to: {output_dir}")
                return True
            else:
                logger.error(f"EML to markdown conversion failed: {result.stderr}")
                print(f"Conversion error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("EML to markdown conversion timed out")
            print("Conversion error: Process timed out")
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
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint if available (C-3)"
    )

    args = parser.parse_args()

    # Create fetcher
    fetcher = IncrementalGmailFetcher(args.db_path)

    # Run incremental fetch with resume support
    success = fetcher.run_incremental_fetch(
        max_emails=args.max_emails,
        output_dir=args.output,
        resume=args.resume
    )

    if success:
        print("\n[SUCCESS] Incremental fetch completed successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Incremental fetch failed!")
        sys.exit(1)


# Alias for backward compatibility
IncrementalFetcher = IncrementalGmailFetcher


if __name__ == "__main__":
    main()