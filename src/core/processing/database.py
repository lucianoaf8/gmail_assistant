#!/usr/bin/env python3
"""
Email Database Importer

Creates a SQLite database and imports email data from monthly JSON files
with proper schema design, indexing, and data validation.
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
import logging


class EmailDatabaseImporter:
    def __init__(self, db_path: str = "emails.db", json_folder: str = "monthly_email_data"):
        """
        Initialize the EmailDatabaseImporter.
        
        Args:
            db_path: Path to the SQLite database file
            json_folder: Folder containing monthly JSON files
        """
        self.db_path = Path(db_path)
        self.json_folder = Path(json_folder)
        self.conn = None
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def create_database_schema(self):
        """Create the database schema with proper tables and indexes."""
        schema_sql = """
        -- Main emails table
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            gmail_id TEXT,
            thread_id TEXT,
            date_received TEXT,
            parsed_date TEXT,
            year_month TEXT NOT NULL,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            labels TEXT,
            message_content TEXT,
            extraction_timestamp TEXT NOT NULL,
            import_timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            UNIQUE(file_path),  -- Prevent duplicate imports
            CHECK(length(year_month) = 7)  -- Format: YYYY-MM
        );
        
        -- Table for tracking monthly import batches
        CREATE TABLE IF NOT EXISTS import_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_month TEXT NOT NULL UNIQUE,
            email_count INTEGER NOT NULL,
            source_file TEXT NOT NULL,
            date_range_first TEXT,
            date_range_last TEXT,
            extraction_timestamp TEXT,
            import_timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            CHECK(email_count >= 0)
        );
        
        -- Table for email metadata statistics
        CREATE TABLE IF NOT EXISTS email_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            total_emails INTEGER NOT NULL,
            unique_senders INTEGER,
            unique_recipients INTEGER,
            unique_gmail_ids INTEGER,
            earliest_email TEXT,
            latest_email TEXT,
            months_covered INTEGER
        );
        
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_emails_year_month ON emails(year_month);
        CREATE INDEX IF NOT EXISTS idx_emails_gmail_id ON emails(gmail_id);
        CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id);
        CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender);
        CREATE INDEX IF NOT EXISTS idx_emails_recipient ON emails(recipient);
        CREATE INDEX IF NOT EXISTS idx_emails_parsed_date ON emails(parsed_date);
        CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails(subject);
        
        -- Full-text search for message content (optional, if FTS is available)
        CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
            subject, 
            message_content, 
            sender,
            content='emails',
            content_rowid='id'
        );
        
        -- Triggers to maintain FTS index
        CREATE TRIGGER IF NOT EXISTS emails_fts_insert AFTER INSERT ON emails BEGIN
            INSERT INTO emails_fts(rowid, subject, message_content, sender) 
            VALUES (new.id, new.subject, new.message_content, new.sender);
        END;
        
        CREATE TRIGGER IF NOT EXISTS emails_fts_delete AFTER DELETE ON emails BEGIN
            INSERT INTO emails_fts(emails_fts, rowid, subject, message_content, sender) 
            VALUES('delete', old.id, old.subject, old.message_content, old.sender);
        END;
        
        CREATE TRIGGER IF NOT EXISTS emails_fts_update AFTER UPDATE ON emails BEGIN
            INSERT INTO emails_fts(emails_fts, rowid, subject, message_content, sender) 
            VALUES('delete', old.id, old.subject, old.message_content, old.sender);
            INSERT INTO emails_fts(rowid, subject, message_content, sender) 
            VALUES (new.id, new.subject, new.message_content, new.sender);
        END;
        """
        
        try:
            self.conn.executescript(schema_sql)
            self.conn.commit()
            self.logger.info("Database schema created successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating database schema: {e}")
            raise
    
    def connect_database(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            
            # Enable foreign keys and other pragmas for better performance
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA cache_size = 10000")
            
            self.logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise
    
    def close_database(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")
    
    def import_monthly_json(self, json_file: Path) -> Tuple[int, int]:
        """
        Import emails from a monthly JSON file.
        
        Args:
            json_file: Path to the monthly JSON file
            
        Returns:
            Tuple of (imported_count, skipped_count)
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Error reading JSON file {json_file}: {e}")
            return 0, 0
        
        year_month = data.get('year_month', 'unknown')
        emails = data.get('emails', [])
        
        if not emails:
            self.logger.warning(f"No emails found in {json_file}")
            return 0, 0
        
        imported_count = 0
        skipped_count = 0
        
        # Check if this batch was already imported
        existing_batch = self.conn.execute(
            "SELECT id FROM import_batches WHERE year_month = ?", 
            (year_month,)
        ).fetchone()
        
        if existing_batch:
            self.logger.warning(f"Batch {year_month} already imported, skipping...")
            return 0, len(emails)
        
        # Import emails
        for email in emails:
            try:
                # Check if email already exists (by file_path)
                existing = self.conn.execute(
                    "SELECT id FROM emails WHERE file_path = ?", 
                    (email.get('file_path', ''),)
                ).fetchone()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Insert email
                self.conn.execute("""
                    INSERT INTO emails (
                        filename, file_path, gmail_id, thread_id, date_received,
                        parsed_date, year_month, sender, recipient, subject,
                        labels, message_content, extraction_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email.get('filename', ''),
                    email.get('file_path', ''),
                    email.get('gmail_id', ''),
                    email.get('thread_id', ''),
                    email.get('date_received', ''),
                    email.get('parsed_date', ''),
                    email.get('year_month', year_month),
                    email.get('sender', ''),
                    email.get('recipient', ''),
                    email.get('subject', ''),
                    email.get('labels', ''),
                    email.get('message_content', ''),
                    email.get('extraction_timestamp', '')
                ))
                
                imported_count += 1
                
            except sqlite3.Error as e:
                self.logger.error(f"Error importing email {email.get('filename', 'unknown')}: {e}")
                skipped_count += 1
        
        # Record the import batch
        try:
            self.conn.execute("""
                INSERT INTO import_batches (
                    year_month, email_count, source_file, date_range_first,
                    date_range_last, extraction_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                year_month,
                len(emails),
                str(json_file),
                data.get('date_range', {}).get('first_email', ''),
                data.get('date_range', {}).get('last_email', ''),
                data.get('extraction_info', {}).get('extracted_at', '')
            ))
        except sqlite3.Error as e:
            self.logger.error(f"Error recording import batch: {e}")
        
        self.conn.commit()
        return imported_count, skipped_count
    
    def import_all_monthly_files(self) -> Dict[str, int]:
        """
        Import all monthly JSON files from the specified folder.
        
        Returns:
            Dictionary with import statistics
        """
        if not self.json_folder.exists():
            self.logger.error(f"JSON folder not found: {self.json_folder}")
            return {}
        
        # Find all monthly JSON files
        json_files = list(self.json_folder.glob("*_emails.json"))
        json_files.sort()  # Process in chronological order
        
        if not json_files:
            self.logger.error(f"No monthly JSON files found in {self.json_folder}")
            return {}
        
        stats = {
            'total_files': len(json_files),
            'total_imported': 0,
            'total_skipped': 0,
            'processed_files': 0,
            'failed_files': 0
        }
        
        self.logger.info(f"Found {len(json_files)} monthly JSON files to import")
        
        for json_file in json_files:
            try:
                self.logger.info(f"Processing {json_file.name}...")
                imported, skipped = self.import_monthly_json(json_file)
                
                stats['total_imported'] += imported
                stats['total_skipped'] += skipped
                stats['processed_files'] += 1
                
                self.logger.info(f"  Imported: {imported}, Skipped: {skipped}")
                
            except Exception as e:
                self.logger.error(f"Failed to process {json_file}: {e}")
                stats['failed_files'] += 1
        
        return stats
    
    def update_statistics(self):
        """Update the email_stats table with current database statistics."""
        try:
            # Calculate statistics
            stats_query = """
            SELECT 
                COUNT(*) as total_emails,
                COUNT(DISTINCT sender) as unique_senders,
                COUNT(DISTINCT recipient) as unique_recipients,
                COUNT(DISTINCT gmail_id) as unique_gmail_ids,
                MIN(parsed_date) as earliest_email,
                MAX(parsed_date) as latest_email,
                COUNT(DISTINCT year_month) as months_covered
            FROM emails
            WHERE gmail_id != ''
            """
            
            result = self.conn.execute(stats_query).fetchone()
            
            # Insert statistics
            self.conn.execute("""
                INSERT INTO email_stats (
                    total_emails, unique_senders, unique_recipients, 
                    unique_gmail_ids, earliest_email, latest_email, months_covered
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result['total_emails'],
                result['unique_senders'],
                result['unique_recipients'],
                result['unique_gmail_ids'],
                result['earliest_email'],
                result['latest_email'],
                result['months_covered']
            ))
            
            self.conn.commit()
            self.logger.info("Database statistics updated")
            
        except sqlite3.Error as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def get_database_info(self) -> Dict:
        """Get information about the current database state."""
        try:
            info = {}
            
            # Email counts
            email_count = self.conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
            info['total_emails'] = email_count
            
            # Batch counts
            batch_count = self.conn.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0]
            info['imported_batches'] = batch_count
            
            # Date range
            date_range = self.conn.execute("""
                SELECT MIN(parsed_date) as earliest, MAX(parsed_date) as latest 
                FROM emails WHERE parsed_date != ''
            """).fetchone()
            info['date_range'] = {
                'earliest': date_range['earliest'],
                'latest': date_range['latest']
            }
            
            # Top senders
            top_senders = self.conn.execute("""
                SELECT sender, COUNT(*) as count 
                FROM emails 
                WHERE sender != '' 
                GROUP BY sender 
                ORDER BY count DESC 
                LIMIT 10
            """).fetchall()
            info['top_senders'] = [{'sender': row['sender'], 'count': row['count']} 
                                 for row in top_senders]
            
            # Monthly distribution
            monthly_dist = self.conn.execute("""
                SELECT year_month, COUNT(*) as count 
                FROM emails 
                GROUP BY year_month 
                ORDER BY year_month
            """).fetchall()
            info['monthly_distribution'] = [{'month': row['year_month'], 'count': row['count']} 
                                          for row in monthly_dist]
            
            return info
            
        except sqlite3.Error as e:
            self.logger.error(f"Error getting database info: {e}")
            return {}
    
    def search_emails(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search emails using full-text search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching emails
        """
        try:
            # Use FTS if available, otherwise fall back to LIKE search
            fts_query = """
                SELECT e.*, rank
                FROM emails_fts 
                JOIN emails e ON emails_fts.rowid = e.id
                WHERE emails_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            
            fallback_query = """
                SELECT * FROM emails 
                WHERE subject LIKE ? OR message_content LIKE ? OR sender LIKE ?
                ORDER BY parsed_date DESC
                LIMIT ?
            """
            
            try:
                # Try FTS first
                results = self.conn.execute(fts_query, (query, limit)).fetchall()
            except sqlite3.OperationalError:
                # Fall back to LIKE search
                like_query = f"%{query}%"
                results = self.conn.execute(fallback_query, (like_query, like_query, like_query, limit)).fetchall()
            
            return [dict(row) for row in results]
            
        except sqlite3.Error as e:
            self.logger.error(f"Error searching emails: {e}")
            return []


def main():
    """Main function to run the email database importer."""
    parser = argparse.ArgumentParser(description='Import email data into SQLite database')
    parser.add_argument('--db', '-d', default='emails.db',
                       help='Database file path (default: emails.db)')
    parser.add_argument('--json-folder', '-j', default='monthly_email_data',
                       help='Folder containing monthly JSON files (default: monthly_email_data)')
    parser.add_argument('--info', action='store_true',
                       help='Show database information and exit')
    parser.add_argument('--search', '-s', type=str,
                       help='Search emails for a query')
    parser.add_argument('--force-recreate', action='store_true',
                       help='Delete existing database and recreate')
    
    args = parser.parse_args()
    
    # Initialize importer
    importer = EmailDatabaseImporter(args.db, args.json_folder)
    
    try:
        # Handle database recreation
        if args.force_recreate and Path(args.db).exists():
            Path(args.db).unlink()
            print(f"Deleted existing database: {args.db}")
        
        # Connect to database
        importer.connect_database()
        
        # Create schema if needed
        importer.create_database_schema()
        
        # Handle info request
        if args.info:
            info = importer.get_database_info()
            print("\n=== Database Information ===")
            print(f"Total emails: {info.get('total_emails', 0)}")
            print(f"Imported batches: {info.get('imported_batches', 0)}")
            
            date_range = info.get('date_range', {})
            print(f"Date range: {date_range.get('earliest', 'N/A')} to {date_range.get('latest', 'N/A')}")
            
            print("\nTop senders:")
            for sender in info.get('top_senders', [])[:5]:
                print(f"  {sender['sender']}: {sender['count']} emails")
            
            print(f"\nMonthly distribution: {len(info.get('monthly_distribution', []))} months")
            return
        
        # Handle search request
        if args.search:
            results = importer.search_emails(args.search)
            print(f"\n=== Search Results for '{args.search}' ===")
            print(f"Found {len(results)} matches:")
            
            for result in results[:10]:  # Show first 10 results
                print(f"\nDate: {result.get('parsed_date', 'N/A')}")
                print(f"From: {result.get('sender', 'N/A')}")
                print(f"Subject: {result.get('subject', 'N/A')}")
                content_preview = result.get('message_content', '')[:200]
                print(f"Content: {content_preview}{'...' if len(content_preview) == 200 else ''}")
                print("-" * 50)
            return
        
        # Import emails
        print("Starting email import...")
        stats = importer.import_all_monthly_files()
        
        # Update statistics
        importer.update_statistics()
        
        # Show results
        print("\n=== Import Results ===")
        print(f"Total files found: {stats.get('total_files', 0)}")
        print(f"Files processed: {stats.get('processed_files', 0)}")
        print(f"Files failed: {stats.get('failed_files', 0)}")
        print(f"Emails imported: {stats.get('total_imported', 0)}")
        print(f"Emails skipped: {stats.get('total_skipped', 0)}")
        
        # Show database info
        info = importer.get_database_info()
        print(f"\nDatabase now contains {info.get('total_emails', 0)} emails")
        print(f"Database file: {importer.db_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    finally:
        importer.close_database()
    
    return 0


if __name__ == "__main__":
    exit(main())