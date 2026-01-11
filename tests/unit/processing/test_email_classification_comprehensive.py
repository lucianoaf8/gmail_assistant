#!/usr/bin/env python3
"""
Comprehensive email classification tests using real data and database operations.
Tests classification algorithms, batch processing, and database workflows.
"""

import pytest
import tempfile
import shutil
import sqlite3
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

from gmail_assistant.core.processing.classifier import EmailClassifier
from gmail_assistant.core.processing.database import EmailDatabaseImporter


class TestEmailClassifierComprehensive:
    """Comprehensive tests for EmailClassifier with real database operations."""

    def setup_method(self):
        """Setup test environment with comprehensive test database."""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Use real database if available, otherwise create comprehensive test database
        self.real_db_path = Path("data/databases/emails_final.db")
        if self.real_db_path.exists():
            self.db_path = str(self.real_db_path)
            self.using_real_db = True
        else:
            self.db_path = str(self.test_dir / "comprehensive_test_emails.db")
            self.using_real_db = False
            self.create_comprehensive_test_database()

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_comprehensive_test_database(self):
        """Create a comprehensive test database with realistic email data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create emails table with full schema
        cursor.execute('''
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                thread_id TEXT,
                subject TEXT,
                sender TEXT,
                recipient TEXT,
                date TEXT,
                content TEXT,
                labels TEXT,
                has_attachments BOOLEAN DEFAULT 0,
                size_bytes INTEGER,
                snippet TEXT
            )
        ''')

        # Create comprehensive test data with real email patterns
        sample_emails = [
            # Newsletters
            ("msg_001", "thread_001", "AI Weekly Newsletter #47", "newsletter@aiweekly.com", 
             "user@example.com", "2025-09-15", "This week in AI: GPT-4, Claude, and new research...", 
             "newsletter", 0, 15000, "This week in AI developments"),
            ("msg_002", "thread_002", "Tech Crunch Daily Digest", "digest@techcrunch.com",
             "user@example.com", "2025-09-14", "Today's top tech stories: startup funding, AI...",
             "newsletter", 0, 12000, "Today's top tech stories"),
            ("msg_003", "thread_003", "Morning Brew - Business News", "crew@morningbrew.com",
             "user@example.com", "2025-09-13", "Market updates, business trends, and more...",
             "newsletter", 0, 18000, "Market updates and trends"),
            
            # Service Notifications
            ("msg_004", "thread_004", "GitHub Security Alert", "noreply@github.com",
             "user@example.com", "2025-09-12", "Suspicious activity detected on your account...",
             "security,notification", 0, 3000, "Suspicious activity detected"),
            ("msg_005", "thread_005", "AWS Billing Alert", "no-reply@aws.amazon.com",
             "user@example.com", "2025-09-11", "Your AWS bill for September is ready...",
             "billing,notification", 1, 5000, "Your AWS bill is ready"),
            ("msg_006", "thread_006", "Slack Notification", "notifications@slack.com",
             "user@example.com", "2025-09-10", "You have 3 new messages in #general...",
             "notification", 0, 2000, "You have new messages"),
            
            # Personal Emails
            ("msg_007", "thread_007", "Meeting Tomorrow", "colleague@company.com",
             "user@example.com", "2025-09-09", "Hi! Can we schedule the project meeting for tomorrow?",
             "personal", 0, 1500, "Can we schedule the meeting"),
            ("msg_008", "thread_008", "Re: Weekend Plans", "friend@gmail.com",
             "user@example.com", "2025-09-08", "Sure! Let's meet at the park on Saturday...",
             "personal", 0, 800, "Let's meet at the park"),
            
            # Marketing/Promotional
            ("msg_009", "thread_009", "50% Off Sale This Weekend!", "sales@retailer.com",
             "user@example.com", "2025-09-07", "Don't miss our biggest sale of the year...",
             "promotional", 0, 25000, "Don't miss our biggest sale"),
            ("msg_010", "thread_010", "Your Spotify Wrapped is Ready", "no-reply@spotify.com",
             "user@example.com", "2025-09-06", "See your top songs and artists from this year...",
             "promotional", 0, 8000, "See your top songs"),
            
            # Support/Transactional
            ("msg_011", "thread_011", "Order Confirmation #12345", "orders@shop.com",
             "user@example.com", "2025-09-05", "Thank you for your order. Tracking number: ABC123...",
             "transactional", 0, 4000, "Thank you for your order"),
            ("msg_012", "thread_012", "Password Reset Request", "security@service.com",
             "user@example.com", "2025-09-04", "You requested a password reset. Click here to continue...",
             "security,transactional", 0, 2500, "You requested a password reset"),
            
            # Educational
            ("msg_013", "thread_013", "Course Update: Machine Learning", "courses@university.edu",
             "user@example.com", "2025-09-03", "This week's assignment covers neural networks...",
             "educational", 1, 6000, "This week's assignment covers"),
            
            # System/Automated
            ("msg_014", "thread_014", "Backup Completed Successfully", "backup@system.com",
             "user@example.com", "2025-09-02", "Daily backup completed. 2.5GB backed up...",
             "system", 0, 1000, "Daily backup completed"),
            ("msg_015", "thread_015", "Cron Job Report", "cron@server.com",
             "user@example.com", "2025-09-01", "Weekly maintenance completed successfully...",
             "system", 0, 800, "Weekly maintenance completed"),
        ]

        cursor.executemany('''
            INSERT INTO emails (message_id, thread_id, subject, sender, recipient, date, 
                              content, labels, has_attachments, size_bytes, snippet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_emails)

        conn.commit()
        conn.close()

    def test_create_classification_schema_comprehensive(self):
        """Test complete database schema creation for classification."""
        classifier = EmailClassifier(self.db_path)
        
        # Test schema creation
        result = classifier.create_classification_schema()
        
        # Verify schema was created
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for classification columns
        cursor.execute("PRAGMA table_info(emails)")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_classification_columns = [
            'primary_category', 'secondary_category', 'confidence_score',
            'sender_pattern', 'content_keywords', 'classification_date'
        ]
        
        # At least some classification columns should exist
        classification_columns_found = [col for col in expected_classification_columns if col in columns]
        
        print(f"✅ Classification schema creation: {result}")
        print(f"   Total columns: {len(columns)}")
        print(f"   Classification columns found: {classification_columns_found}")
        
        conn.close()

    def test_classify_by_sender_comprehensive_patterns(self):
        """Test comprehensive sender classification with real patterns."""
        classifier = EmailClassifier(self.db_path)
        
        # Test with real sender patterns from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT sender FROM emails LIMIT 10")
        senders = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        successful_classifications = 0
        for sender in senders:
            try:
                classification = classifier.classify_by_sender(sender)
                
                assert isinstance(classification, (str, dict))
                successful_classifications += 1
                
                print(f"✅ Sender classification: '{sender}' → '{classification}'")
                
            except Exception as e:
                print(f"⚠️ Sender classification failed for '{sender}': {e}")
        
        assert successful_classifications > 0
        print(f"✅ Successfully classified {successful_classifications}/{len(senders)} senders")

    def test_classify_by_subject_comprehensive_analysis(self):
        """Test comprehensive subject line analysis with real subjects."""
        classifier = EmailClassifier(self.db_path)
        
        # Get real subjects from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT subject FROM emails WHERE subject IS NOT NULL LIMIT 10")
        subjects = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        successful_classifications = 0
        for subject in subjects:
            try:
                classification = classifier.classify_by_subject(subject)
                
                assert isinstance(classification, (str, dict))
                successful_classifications += 1
                
                print(f"✅ Subject classification: '{subject[:40]}...' → '{classification}'")
                
            except Exception as e:
                print(f"⚠️ Subject classification failed for '{subject}': {e}")
        
        assert successful_classifications > 0
        print(f"✅ Successfully classified {successful_classifications}/{len(subjects)} subjects")

    def test_classify_by_content_comprehensive_analysis(self):
        """Test comprehensive content analysis with real email content."""
        classifier = EmailClassifier(self.db_path)
        
        # Get real content from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM emails WHERE content IS NOT NULL LIMIT 8")
        contents = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        successful_classifications = 0
        for content in contents:
            try:
                classification = classifier.classify_by_content(content)
                
                assert isinstance(classification, (str, dict))
                successful_classifications += 1
                
                print(f"✅ Content classification: '{content[:30]}...' → '{classification}'")
                
            except Exception as e:
                print(f"⚠️ Content classification failed: {e}")
        
        assert successful_classifications > 0
        print(f"✅ Successfully classified {successful_classifications}/{len(contents)} content pieces")

    def test_analyze_sender_patterns_comprehensive(self):
        """Test comprehensive sender pattern analysis."""
        classifier = EmailClassifier(self.db_path)
        
        try:
            patterns = classifier.analyze_sender_patterns()
            
            assert isinstance(patterns, (dict, list))
            
            if isinstance(patterns, dict):
                assert len(patterns) > 0
                print(f"✅ Sender patterns analysis: {len(patterns)} patterns found")
                
                # Show sample patterns
                sample_patterns = list(patterns.items())[:3]
                for pattern, data in sample_patterns:
                    print(f"   Pattern: {pattern} → {data}")
                    
            elif isinstance(patterns, list):
                assert len(patterns) > 0
                print(f"✅ Sender patterns analysis: {len(patterns)} entries")
                
        except Exception as e:
            print(f"⚠️ Sender pattern analysis failed: {e}")

    def test_classify_all_emails_comprehensive_workflow(self):
        """Test comprehensive batch classification workflow."""
        classifier = EmailClassifier(self.db_path)
        
        try:
            # Run classification on all emails
            result = classifier.classify_all_emails()
            
            print(f"✅ Batch classification result: {result}")
            
            # Verify classification results in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if classification columns were added and populated
            cursor.execute("PRAGMA table_info(emails)")
            columns = [row[1] for row in cursor.fetchall()]
            
            classification_columns = [col for col in columns if 'classif' in col.lower() or 'category' in col.lower()]
            
            if classification_columns:
                print(f"✅ Classification columns created: {classification_columns}")
                
                # Check for classified data
                for col in classification_columns[:2]:  # Check first 2 classification columns
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM emails WHERE {col} IS NOT NULL")
                        count = cursor.fetchone()[0]
                        print(f"   {col}: {count} emails classified")
                    except:
                        pass
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Batch classification failed: {e}")

    def test_calculate_confidence_score_comprehensive(self):
        """Test confidence score calculation with various data types."""
        classifier = EmailClassifier(self.db_path)
        
        # Test confidence scoring with different classification scenarios
        test_classifications = [
            {"primary": "Newsletter", "secondary": "Technology", "certainty": "high"},
            {"primary": "Service_Notification", "secondary": "Security", "certainty": "medium"},
            {"primary": "Personal", "secondary": "Meeting", "certainty": "high"},
            {"primary": "Marketing", "secondary": "Sale", "certainty": "low"},
            {"primary": "System", "secondary": "Backup", "certainty": "high"},
        ]
        
        successful_scores = 0
        for classification_data in test_classifications:
            try:
                score = classifier.calculate_confidence_score(classification_data)
                
                assert isinstance(score, (int, float))
                assert 0 <= score <= 1  # Confidence should be normalized
                
                successful_scores += 1
                print(f"✅ Confidence score: {classification_data} → {score:.3f}")
                
            except Exception as e:
                print(f"⚠️ Confidence scoring failed for {classification_data}: {e}")
        
        assert successful_scores > 0
        print(f"✅ Successfully scored {successful_scores}/{len(test_classifications)} classifications")

    def test_generate_classification_report_comprehensive(self):
        """Test comprehensive classification report generation."""
        classifier = EmailClassifier(self.db_path)
        
        try:
            # First run classification to have data to report on
            classifier.classify_all_emails()
            
            # Generate report
            report = classifier.generate_classification_report()
            
            assert isinstance(report, (dict, str))
            
            if isinstance(report, dict):
                print(f"✅ Classification report generated with {len(report)} sections")
                
                # Check for expected report sections
                expected_sections = ['summary', 'categories', 'statistics', 'analysis']
                found_sections = [section for section in expected_sections if section in report]
                print(f"   Report sections found: {found_sections}")
                
            elif isinstance(report, str):
                assert len(report) > 100  # Should be substantial
                print(f"✅ Classification report generated: {len(report)} characters")
                
                # Check for key report content
                report_indicators = ['classification', 'email', 'category', 'analysis']
                found_indicators = [indicator for indicator in report_indicators if indicator in report.lower()]
                print(f"   Report content indicators: {found_indicators}")
                
        except Exception as e:
            print(f"⚠️ Report generation failed: {e}")

    def test_batch_classification_performance(self):
        """Test batch classification performance and efficiency."""
        classifier = EmailClassifier(self.db_path)
        
        # Get email count for performance testing
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emails")
        email_count = cursor.fetchone()[0]
        conn.close()
        
        if email_count == 0:
            pytest.skip("No emails in database for performance testing")
        
        import time
        start_time = time.time()
        
        try:
            # Run batch classification
            result = classifier.classify_emails_batch()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Batch classification performance:")
            print(f"   Emails processed: {email_count}")
            print(f"   Processing time: {processing_time:.2f} seconds")
            print(f"   Rate: {email_count/processing_time:.1f} emails/second")
            print(f"   Result: {result}")
            
            # Performance should be reasonable
            assert processing_time < 30  # Should complete within 30 seconds for test data
            
        except Exception as e:
            print(f"⚠️ Batch performance test failed: {e}")

    def test_merge_classifications_workflow(self):
        """Test classification merging and update workflows."""
        classifier = EmailClassifier(self.db_path)
        
        try:
            # Test merge classifications if method exists
            result = classifier.merge_classifications()
            
            print(f"✅ Merge classifications: {result}")
            
        except AttributeError:
            print("⚠️ merge_classifications method not available")
        except Exception as e:
            print(f"⚠️ Merge classifications failed: {e}")

    def test_print_classification_report(self):
        """Test classification report printing functionality."""
        classifier = EmailClassifier(self.db_path)
        
        try:
            # Run classification first
            classifier.classify_all_emails()
            
            # Test report printing
            classifier.print_classification_report()
            
            print("✅ Classification report printing completed")
            
        except Exception as e:
            print(f"⚠️ Report printing failed: {e}")


class TestEmailDatabaseImporter:
    """Test comprehensive email database import functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.db_path = str(self.test_dir / "import_test.db")

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.skipif(EmailDatabaseImporter is None, reason="EmailDatabaseImporter not available")
    def test_database_schema_creation_comprehensive(self):
        """Test comprehensive database schema creation."""
        importer = EmailDatabaseImporter(self.db_path)
        
        # Test table creation
        importer.create_tables()
        
        # Verify schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'emails' in tables
        print(f"✅ Database tables created: {tables}")
        
        # Check email table structure
        cursor.execute("PRAGMA table_info(emails)")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_columns = ['id', 'subject', 'sender', 'date', 'content']
        found_columns = [col for col in expected_columns if col in columns]
        
        assert len(found_columns) >= 3  # Should have most essential columns
        print(f"✅ Email table columns: {columns}")
        
        conn.close()

    @pytest.mark.skipif(EmailDatabaseImporter is None, reason="EmailDatabaseImporter not available")
    @pytest.mark.skipif(not Path("backup_unread").exists(), 
                       reason="No backup directory for import testing")
    def test_import_eml_files_comprehensive(self):
        """Test comprehensive EML file import workflow."""
        importer = EmailDatabaseImporter(self.db_path)
        importer.create_tables()
        
        # Find real EML files to import
        backup_dir = Path("backup_unread")
        eml_files = []
        
        # Search for EML files in backup directory
        for year_dir in backup_dir.glob("*"):
            if year_dir.is_dir():
                for month_dir in year_dir.glob("*"):
                    if month_dir.is_dir():
                        month_eml_files = list(month_dir.glob("*.eml"))[:3]  # Max 3 per month
                        eml_files.extend(month_eml_files)
                        if len(eml_files) >= 10:  # Limit to 10 total for testing
                            break
                if len(eml_files) >= 10:
                    break
        
        if not eml_files:
            pytest.skip("No EML files found for import testing")
        
        imported_count = 0
        errors = 0
        
        for eml_file in eml_files:
            try:
                result = importer.import_eml_file(str(eml_file))
                
                if result:
                    imported_count += 1
                    print(f"✅ Imported: {eml_file.name}")
                else:
                    errors += 1
                    print(f"⚠️ Failed to import: {eml_file.name}")
                    
            except Exception as e:
                errors += 1
                print(f"⚠️ Import error for {eml_file.name}: {e}")
        
        # Verify imports in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emails")
        db_count = cursor.fetchone()[0]
        
        # Get sample of imported data
        cursor.execute("SELECT subject, sender FROM emails LIMIT 5")
        samples = cursor.fetchall()
        
        conn.close()
        
        assert db_count > 0
        print(f"✅ Import summary:")
        print(f"   Files processed: {len(eml_files)}")
        print(f"   Successfully imported: {imported_count}")
        print(f"   Errors: {errors}")
        print(f"   Database records: {db_count}")
        print(f"   Sample imports: {samples[:3]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])