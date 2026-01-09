#!/usr/bin/env python3
"""
Email Data Converter
Converts EML and Markdown email files to Parquet format for daily analysis.
"""

import os
import json
import email
import email.parser
import re
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import email.utils
import argparse
import logging

class EmailDataConverter:
    """Convert email files (EML/Markdown) to Parquet format for analysis"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('EmailDataConverter')
        logger.setLevel(logging.INFO if self.verbose else logging.WARNING)

        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def extract_from_eml(self, eml_path: Path) -> Optional[Dict]:
        """Extract data from EML file"""
        try:
            with open(eml_path, 'rb') as f:
                parser = email.parser.BytesParser()
                msg = parser.parsebytes(f.read())

            # Extract basic metadata
            gmail_id = self._extract_gmail_id(eml_path.name)
            subject = msg.get('subject', '')
            sender = msg.get('from', '')
            date_str = msg.get('date', '')

            # Parse date
            date_received = self._parse_email_date(date_str)

            # Extract plain text content
            plain_text_content = self._extract_plain_text(msg)

            return {
                'gmail_id': gmail_id,
                'subject': subject,
                'sender': sender,
                'date_received': date_received,
                'plain_text_content': plain_text_content,
                'source_file': str(eml_path),
                'source_type': 'eml'
            }

        except Exception as e:
            self.logger.error(f"Error processing EML {eml_path}: {e}")
            return None

    def extract_from_markdown(self, md_path: Path) -> Optional[Dict]:
        """Extract data from Markdown file"""
        try:
            with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract Gmail ID from filename
            gmail_id = self._extract_gmail_id(md_path.name)

            # Parse metadata table
            metadata = self._parse_markdown_metadata(content)

            # Extract plain text content (everything after metadata table)
            plain_text_content = self._extract_markdown_content(content)

            return {
                'gmail_id': gmail_id,
                'subject': metadata.get('subject', ''),
                'sender': metadata.get('from', ''),
                'date_received': self._parse_email_date(metadata.get('date', '')),
                'plain_text_content': plain_text_content,
                'source_file': str(md_path),
                'source_type': 'markdown'
            }

        except Exception as e:
            self.logger.error(f"Error processing Markdown {md_path}: {e}")
            return None

    def _extract_gmail_id(self, filename: str) -> str:
        """Extract Gmail ID from filename"""
        # Pattern: YYYY-MM-DD_HHMMSS_subject_GMAILID.ext
        match = re.search(r'_([a-f0-9]{16})\.', filename)
        if match:
            return match.group(1)

        # Fallback: use filename without extension
        return Path(filename).stem

    def _parse_email_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date string to datetime"""
        if not date_str:
            return None

        try:
            # Parse RFC 2822 date format
            parsed_tuple = email.utils.parsedate_tz(date_str)
            if parsed_tuple:
                timestamp = email.utils.mktime_tz(parsed_tuple)
                return datetime.fromtimestamp(timestamp)
        except:
            pass

        # Try common date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%a, %d %b %Y %H:%M:%S %z'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue

        self.logger.warning(f"Could not parse date: {date_str}")
        return None

    def _extract_plain_text(self, msg) -> str:
        """Extract plain text content from email message"""
        plain_text_parts = []

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            text = payload.decode('utf-8', errors='ignore')
                            plain_text_parts.append(text)
                        except:
                            continue
        else:
            if msg.get_content_type() == 'text/plain':
                payload = msg.get_payload(decode=True)
                if payload:
                    try:
                        text = payload.decode('utf-8', errors='ignore')
                        plain_text_parts.append(text)
                    except:
                        pass

        return '\n'.join(plain_text_parts)

    def _parse_markdown_metadata(self, content: str) -> Dict[str, str]:
        """Parse metadata from markdown table format"""
        metadata = {}

        # Look for metadata table
        table_pattern = r'\| Field \| Value \|.*?\n\| --- \| --- \|(.*?)(?=\n##|\n\n|\Z)'
        table_match = re.search(table_pattern, content, re.DOTALL)

        if table_match:
            table_content = table_match.group(1)

            # Parse each row
            for line in table_content.split('\n'):
                line = line.strip()
                if '|' in line and line.startswith('|'):
                    parts = [p.strip() for p in line.split('|')[1:-1]]
                    if len(parts) >= 2:
                        field = parts[0].lower().replace(' ', '_')
                        value = parts[1]
                        metadata[field] = value

        return metadata

    def _extract_markdown_content(self, content: str) -> str:
        """Extract main content from markdown (after metadata table)"""
        # Find the end of metadata table
        table_end = content.find('## Email Content')
        if table_end != -1:
            content_start = table_end + len('## Email Content')
            return content[content_start:].strip()

        # Fallback: take everything after first ## heading
        heading_match = re.search(r'\n## .+?\n', content)
        if heading_match:
            return content[heading_match.end():].strip()

        return content

    def convert_directory(self, input_dir: Path, output_file: Path,
                         date_filter: Optional[str] = None) -> int:
        """
        Convert all email files in directory to Parquet format

        Args:
            input_dir: Directory containing EML/Markdown files
            output_file: Output Parquet file path
            date_filter: Optional date filter (YYYY-MM-DD)

        Returns:
            Number of emails processed
        """
        self.logger.info(f"Converting emails from {input_dir} to {output_file}")

        email_data = []
        processed_count = 0

        # Find all email files
        eml_files = list(input_dir.rglob('*.eml'))
        md_files = list(input_dir.rglob('*.md'))

        all_files = eml_files + md_files
        self.logger.info(f"Found {len(all_files)} files ({len(eml_files)} EML, {len(md_files)} MD)")

        for file_path in all_files:
            # Extract email data based on file type
            if file_path.suffix == '.eml':
                email_record = self.extract_from_eml(file_path)
            elif file_path.suffix == '.md':
                email_record = self.extract_from_markdown(file_path)
            else:
                continue

            if email_record is None:
                continue

            # Apply date filter if specified
            if date_filter and email_record.get('date_received'):
                email_date = email_record['date_received'].date()
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                if email_date != filter_date:
                    continue

            email_data.append(email_record)
            processed_count += 1

            if processed_count % 100 == 0:
                self.logger.info(f"Processed {processed_count} emails...")

        if not email_data:
            self.logger.warning("No email data to convert")
            return 0

        # Create DataFrame and save as Parquet
        df = pd.DataFrame(email_data)

        # Ensure proper data types
        df['date_received'] = pd.to_datetime(df['date_received'])
        df['gmail_id'] = df['gmail_id'].astype(str)
        df['subject'] = df['subject'].astype(str)
        df['sender'] = df['sender'].astype(str)
        df['plain_text_content'] = df['plain_text_content'].astype(str)

        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save as Parquet
        df.to_parquet(output_file, index=False, compression='snappy')

        self.logger.info(f"Saved {len(df)} emails to {output_file}")
        return processed_count

    def convert_latest_emails(self, backup_dir: Path, output_file: Path,
                            days_back: int = 1) -> int:
        """
        Convert emails from last N days to Parquet format

        Args:
            backup_dir: Gmail backup directory
            output_file: Output Parquet file
            days_back: Number of days to look back

        Returns:
            Number of emails processed
        """
        from datetime import datetime, timedelta

        target_dates = []
        for i in range(days_back):
            date = datetime.now().date() - timedelta(days=i+1)
            target_dates.append(date.strftime('%Y-%m-%d'))

        self.logger.info(f"Converting emails from dates: {target_dates}")

        all_email_data = []

        for date_str in target_dates:
            # Create temporary file for this date
            temp_file = output_file.parent / f"temp_{date_str}.parquet"

            count = self.convert_directory(backup_dir, temp_file, date_filter=date_str)

            if count > 0 and temp_file.exists():
                # Read and combine data
                date_df = pd.read_parquet(temp_file)
                all_email_data.append(date_df)

                # Clean up temp file
                temp_file.unlink()

        if not all_email_data:
            self.logger.warning("No emails found for specified dates")
            return 0

        # Combine all data and save
        combined_df = pd.concat(all_email_data, ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['gmail_id'])

        combined_df.to_parquet(output_file, index=False, compression='snappy')

        self.logger.info(f"Combined {len(combined_df)} unique emails to {output_file}")
        return len(combined_df)

def main():
    """CLI interface for email data conversion"""
    parser = argparse.ArgumentParser(description='Convert email files to Parquet format')
    parser.add_argument('--input', required=True, help='Input directory with email files')
    parser.add_argument('--output', required=True, help='Output Parquet file path')
    parser.add_argument('--date', help='Filter by specific date (YYYY-MM-DD)')
    parser.add_argument('--days-back', type=int, default=1, help='Number of days to look back')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    converter = EmailDataConverter(verbose=args.verbose)

    input_dir = Path(args.input)
    output_file = Path(args.output)

    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return 1

    try:
        if args.date:
            count = converter.convert_directory(input_dir, output_file, date_filter=args.date)
        else:
            count = converter.convert_latest_emails(input_dir, output_file, days_back=args.days_back)

        print(f"✅ Successfully converted {count} emails to {output_file}")
        return 0

    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())