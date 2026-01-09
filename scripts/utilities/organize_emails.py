#!/usr/bin/env python3
"""
Organize fetched emails by year/month structure and extract dates
"""

import os
import shutil
import email
from pathlib import Path
from datetime import datetime
import re

def extract_email_date(eml_file):
    """Extract date from EML file using raw parsing"""
    try:
        # Read raw file content
        with open(eml_file, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()

        # Search for Date: header in raw content
        lines = raw_content.split('\n')
        for line in lines:
            if line.startswith('Date:'):
                date_str = line[5:].strip()  # Remove 'Date:' prefix

                if date_str:
                    try:
                        # Clean up timezone info in parentheses
                        if '(' in date_str:
                            date_str = date_str.split('(')[0].strip()

                        # Common Gmail date formats
                        for fmt in [
                            '%a, %d %b %Y %H:%M:%S %z',
                            '%a, %d %b %Y %H:%M:%S %Z',
                            '%d %b %Y %H:%M:%S %z',
                            '%a, %d %b %Y %H:%M:%S'
                        ]:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                return parsed_date
                            except ValueError:
                                continue

                    except Exception as e:
                        print(f"[WARNING] Could not parse date '{date_str}' from {eml_file}: {e}")

    except Exception as e:
        print(f"[ERROR] Could not read {eml_file}: {e}")

    return None

def organize_emails(source_dir, target_dir):
    """Organize emails from source to target directory by year/month"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    if not source_path.exists():
        print(f"[ERROR] Source directory does not exist: {source_dir}")
        return False

    target_path.mkdir(parents=True, exist_ok=True)

    eml_files = list(source_path.glob('*.eml'))
    print(f"[INFO] Found {len(eml_files)} EML files to organize")

    organized_count = 0
    failed_count = 0

    for eml_file in eml_files:
        try:
            # Extract date from email
            email_date = extract_email_date(eml_file)

            if email_date:
                # Create year/month folder structure
                year = email_date.strftime('%Y')
                month = email_date.strftime('%m')

                dest_folder = target_path / year / month
                dest_folder.mkdir(parents=True, exist_ok=True)

                # Copy file to organized location
                dest_file = dest_folder / eml_file.name
                shutil.copy2(eml_file, dest_file)

                organized_count += 1
                print(f"[INFO] {eml_file.name} -> {year}/{month}/")

            else:
                # Fallback: use current date if email date cannot be parsed
                fallback_date = datetime.now()
                year = fallback_date.strftime('%Y')
                month = fallback_date.strftime('%m')

                dest_folder = target_path / year / month
                dest_folder.mkdir(parents=True, exist_ok=True)

                dest_file = dest_folder / eml_file.name
                shutil.copy2(eml_file, dest_file)

                failed_count += 1
                print(f"[WARNING] {eml_file.name} -> {year}/{month}/ (fallback date)")

        except Exception as e:
            print(f"[ERROR] Failed to organize {eml_file.name}: {e}")
            failed_count += 1

    print(f"\n[SUMMARY]")
    print(f"Successfully organized: {organized_count}")
    print(f"Failed/fallback: {failed_count}")
    print(f"Total processed: {len(eml_files)}")

    # Show folder structure
    print(f"\n[FOLDER STRUCTURE]")
    for year_folder in sorted(target_path.iterdir()):
        if year_folder.is_dir():
            print(f"{year_folder.name}/")
            for month_folder in sorted(year_folder.iterdir()):
                if month_folder.is_dir():
                    file_count = len(list(month_folder.glob('*.eml')))
                    print(f"  {month_folder.name}/ ({file_count} files)")

    return True

def main():
    source_dir = "incremental_backup"
    target_dir = "data/fetched_emails"

    print("[INFO] Organizing fetched emails by year/month...")
    success = organize_emails(source_dir, target_dir)

    if success:
        print("\n[SUCCESS] Email organization completed!")
    else:
        print("\n[FAILED] Email organization failed!")

if __name__ == "__main__":
    main()