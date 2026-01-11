#!/usr/bin/env python3
"""
Email Data Extractor

Extracts email metadata and content from regenerated markdown files
and organizes them into monthly JSON files.
"""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


class EmailDataExtractor:
    def __init__(self, base_folder: str, output_folder: str = "monthly_email_data"):
        """
        Initialize the EmailDataExtractor.
        
        Args:
            base_folder: Path to the regenerated folder containing email markdown files
            output_folder: Folder to save monthly JSON files
        """
        self.base_folder = Path(base_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)

    def extract_email_metadata(self, file_path: Path) -> dict | None:
        """
        Extract email metadata and content from a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Dictionary containing email data or None if extraction fails
        """
        try:
            with open(file_path, encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Parse the markdown table for metadata
            metadata = {}

            # Extract metadata from the table format
            table_match = re.search(r'\| Field \| Value \|.*?\n\| --- \| --- \|(.*?)(?=\n##|\Z)', content, re.DOTALL)
            if table_match:
                table_content = table_match.group(1)

                # Parse each table row
                for line in table_content.strip().split('\n'):
                    if '|' in line:
                        parts = [part.strip() for part in line.split('|') if part.strip()]
                        if len(parts) >= 2:
                            field = parts[0]
                            value = parts[1]
                            metadata[field] = value

            # Extract message content (everything after "## Message Content")
            content_match = re.search(r'## Message Content\s*\n(.*)', content, re.DOTALL)
            message_content = content_match.group(1).strip() if content_match else ""

            # Clean up the message content (remove excessive whitespace, normalize line breaks)
            message_content = re.sub(r'\n\s*\n\s*\n', '\n\n', message_content)
            message_content = message_content.strip()

            # Parse date to get year-month for organization
            date_str = metadata.get('Date', '')
            parsed_date = self.parse_date(date_str)

            # If date parsing fails, try to extract from filename
            if not parsed_date:
                filename = file_path.name
                filename_match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{6})_(.+)_([a-f0-9]+)\.md$', filename)
                if filename_match:
                    try:
                        parsed_date = datetime.strptime(filename_match.group(1), '%Y-%m-%d')
                    except ValueError:
                        pass

            # Extract filename components for additional context
            filename = file_path.name

            return {
                'filename': filename,
                'file_path': str(file_path),
                'date_received': metadata.get('Date', ''),
                'sender': metadata.get('From', ''),
                'recipient': metadata.get('To', ''),
                'subject': metadata.get('Subject', ''),
                'gmail_id': metadata.get('Gmail ID', ''),
                'thread_id': metadata.get('Thread ID', ''),
                'labels': metadata.get('Labels', ''),
                'message_content': message_content,
                'parsed_date': parsed_date.isoformat() if parsed_date else None,
                'year_month': f"{parsed_date.year:04d}-{parsed_date.month:02d}" if parsed_date else None,
                'extraction_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            # For debugging, let's see what's in a few of these files
            try:
                if "2024-06-15" in str(file_path):
                    with open(file_path, encoding='utf-8', errors='ignore') as f:
                        sample_content = f.read()[:500]
                        print(f"Sample content from failed file: {sample_content}")
            except OSError:
                pass
            return None

    def parse_date(self, date_str: str) -> datetime | None:
        """
        Parse various date formats found in email headers.
        
        Args:
            date_str: Date string from email header
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not date_str:
            return None

        # Clean up common variations in date strings
        date_str = date_str.strip()
        # Remove (UTC) and similar timezone annotations
        date_str = re.sub(r'\s*\([^)]+\)\s*$', '', date_str)

        # Common email date formats
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',     # Standard RFC 2822
            '%a, %d %b %Y %H:%M:%S +0000',  # UTC with explicit offset
            '%a, %d %b %Y %H:%M:%S -0000',  # UTC with negative offset
            '%a, %d %b %Y %H:%M:%S %Z',     # With timezone name
            '%a, %d %b %Y %H:%M:%S',        # Without timezone
            '%d %b %Y %H:%M:%S %z',         # Without day of week
            '%d %b %Y %H:%M:%S',            # Without day and timezone
            '%Y-%m-%d %H:%M:%S %z',         # ISO with timezone
            '%Y-%m-%d %H:%M:%S',            # ISO without timezone
            '%Y-%m-%d',                     # Date only
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Try to extract date components manually for complex formats
        try:
            # Look for YYYY-MM-DD pattern anywhere in the string
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
            if date_match:
                return datetime.strptime(date_match.group(1), '%Y-%m-%d')

            # Look for DD Mon YYYY pattern
            date_match = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})', date_str)
            if date_match:
                day, month_str, year = date_match.groups()
                # Convert month name to number
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                month = month_map.get(month_str.lower()[:3])
                if month:
                    return datetime(int(year), month, int(day))
        except (ValueError, AttributeError):
            pass

        return None

    def find_md_files_manually(self) -> list[Path]:
        """
        Use system find command to locate markdown files, avoiding Python directory traversal issues.
        
        Returns:
            List of markdown file paths
        """
        md_files = []

        try:
            # Use find command to locate all .md files
            result = subprocess.run([
                'find', str(self.base_folder), '-name', '*.md', '-type', 'f'
            ], capture_output=True, text=True, check=True)

            # Convert output to Path objects
            for file_path in result.stdout.strip().split('\n'):
                if file_path:  # Skip empty lines
                    md_files.append(Path(file_path))

        except subprocess.CalledProcessError as e:
            print(f"Error running find command: {e}")
            # Fallback to Python approach
            md_files = self.find_md_files_python_fallback()

        return md_files

    def find_md_files_python_fallback(self) -> list[Path]:
        """
        Python fallback for finding markdown files, skipping problematic directories.
        
        Returns:
            List of markdown file paths
        """
        md_files = []

        def safe_walk(directory):
            """Safely walk directory tree, skipping problematic subdirectories."""
            try:
                for item in directory.iterdir():
                    if item.is_file() and item.suffix == '.md':
                        md_files.append(item)
                    elif item.is_dir():
                        try:
                            safe_walk(item)
                        except (OSError, PermissionError) as e:
                            print(f"Skipping problematic directory {item}: {e}")
                            continue
            except (OSError, PermissionError) as e:
                print(f"Cannot access directory {directory}: {e}")

        safe_walk(self.base_folder)
        return md_files

    def process_all_emails(self) -> dict[str, int]:
        """
        Process all email markdown files and organize into monthly JSON files.
        
        Returns:
            Dictionary with statistics about processed emails
        """
        monthly_data = {}
        stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'months_created': 0
        }

        # Find all markdown files recursively with error handling
        md_files = []
        try:
            md_files = list(self.base_folder.rglob('*.md'))
        except OSError as e:
            print(f"Error scanning directory tree: {e}")
            print("Attempting alternative directory traversal...")

            # Alternative approach: manually traverse directories
            md_files = self.find_md_files_manually()

        print(f"Found {len(md_files)} markdown files to process")

        for file_path in md_files:
            stats['total_processed'] += 1

            # Extract email data
            email_data = self.extract_email_metadata(file_path)

            if email_data:
                year_month = email_data.get('year_month', 'unknown')

                if year_month not in monthly_data:
                    monthly_data[year_month] = []

                monthly_data[year_month].append(email_data)
                stats['successful_extractions'] += 1

                if stats['total_processed'] % 100 == 0:
                    print(f"Processed {stats['total_processed']} files...")
            else:
                stats['failed_extractions'] += 1
                print(f"Failed to extract data from: {file_path}")

        # Save monthly JSON files
        for year_month, emails in monthly_data.items():
            output_file = self.output_folder / f"{year_month}_emails.json"

            # Sort emails by date for better organization
            emails.sort(key=lambda x: x.get('date_received', ''))

            monthly_summary = {
                'year_month': year_month,
                'email_count': len(emails),
                'date_range': {
                    'first_email': emails[0]['date_received'] if emails else None,
                    'last_email': emails[-1]['date_received'] if emails else None
                },
                'extraction_info': {
                    'extracted_at': datetime.now().isoformat(),
                    'source_folder': str(self.base_folder)
                },
                'emails': emails
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(monthly_summary, f, indent=2, ensure_ascii=False)

            stats['months_created'] += 1
            print(f"Created {output_file} with {len(emails)} emails")

        return stats

    def generate_summary_report(self, stats: dict[str, int]) -> None:
        """Generate a summary report of the extraction process."""
        summary = {
            'extraction_summary': {
                'total_files_processed': stats['total_processed'],
                'successful_extractions': stats['successful_extractions'],
                'failed_extractions': stats['failed_extractions'],
                'success_rate': f"{(stats['successful_extractions'] / stats['total_processed'] * 100):.1f}%" if stats['total_processed'] > 0 else "0%",
                'monthly_files_created': stats['months_created'],
                'extraction_timestamp': datetime.now().isoformat()
            }
        }

        summary_file = self.output_folder / "extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print("\nExtraction Summary:")
        print(f"- Total files processed: {stats['total_processed']}")
        print(f"- Successful extractions: {stats['successful_extractions']}")
        print(f"- Failed extractions: {stats['failed_extractions']}")
        print(f"- Success rate: {(stats['successful_extractions'] / stats['total_processed'] * 100):.1f}%")
        print(f"- Monthly JSON files created: {stats['months_created']}")
        print(f"- Summary saved to: {summary_file}")


def main():
    """Main function to run the email data extractor."""
    parser = argparse.ArgumentParser(description='Extract email data from regenerated markdown files')
    parser.add_argument('--input', '-i',
                       default='analysis_output/regenerated',
                       help='Input folder containing regenerated email markdown files')
    parser.add_argument('--output', '-o',
                       default='monthly_email_data',
                       help='Output folder for monthly JSON files')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')

    args = parser.parse_args()

    # Initialize extractor
    extractor = EmailDataExtractor(args.input, args.output)

    print("Starting email data extraction...")
    print(f"Input folder: {extractor.base_folder}")
    print(f"Output folder: {extractor.output_folder}")
    print("-" * 50)

    # Process all emails
    stats = extractor.process_all_emails()

    # Generate summary report
    extractor.generate_summary_report(stats)

    print("-" * 50)
    print("Email data extraction completed!")


if __name__ == "__main__":
    main()
