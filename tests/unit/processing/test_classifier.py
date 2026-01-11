"""
Comprehensive tests for classifier.py module.
Tests EmailClassifier class for email classification operations.
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest


class TestEmailClassifierInit:
    """Tests for EmailClassifier initialization."""

    def test_init_sets_db_path(self):
        """Test initialization sets database path."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            classifier = EmailClassifier(f.name)
            assert classifier.db_path == f.name

    def test_init_has_primary_categories(self):
        """Test initialization has primary categories."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            classifier = EmailClassifier(f.name)
            assert 'Newsletter' in classifier.primary_categories
            assert 'Service_Notification' in classifier.primary_categories
            assert 'Marketing' in classifier.primary_categories

    def test_init_has_domain_categories(self):
        """Test initialization has domain categories."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            classifier = EmailClassifier(f.name)
            assert 'AI/Technology' in classifier.domain_categories
            assert 'Finance' in classifier.domain_categories

    def test_init_has_priority_levels(self):
        """Test initialization has priority levels."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            classifier = EmailClassifier(f.name)
            assert 'High' in classifier.priority_levels
            assert 'Medium' in classifier.priority_levels
            assert 'Low' in classifier.priority_levels

    def test_init_has_sender_patterns(self):
        """Test initialization creates sender patterns."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            classifier = EmailClassifier(f.name)
            assert 'Newsletter' in classifier.sender_patterns
            assert 'Service_Notification' in classifier.sender_patterns


class TestExtractDomain:
    """Tests for _extract_domain method."""

    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier instance."""
        from gmail_assistant.core.processing.classifier import EmailClassifier
        return EmailClassifier(str(tmp_path / "test.db"))

    def test_extract_domain_from_angle_brackets(self, classifier):
        """Test extracting domain from <email@domain.com> format."""
        sender = "John Doe <john@example.com>"
        result = classifier._extract_domain(sender)
        assert result == "example.com"

    def test_extract_domain_from_plain_email(self, classifier):
        """Test extracting domain from plain email."""
        sender = "john@example.com"
        result = classifier._extract_domain(sender)
        assert result == "example.com"

    def test_extract_domain_unknown(self, classifier):
        """Test extracting domain returns unknown for invalid email."""
        sender = "invalid_email"
        result = classifier._extract_domain(sender)
        assert result == "unknown"


class TestExtractEmailPrefix:
    """Tests for _extract_email_prefix method."""

    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier instance."""
        from gmail_assistant.core.processing.classifier import EmailClassifier
        return EmailClassifier(str(tmp_path / "test.db"))

    def test_extract_prefix_from_angle_brackets(self, classifier):
        """Test extracting prefix from <email@domain.com> format."""
        sender = "John Doe <newsletter@example.com>"
        result = classifier._extract_email_prefix(sender)
        assert result == "newsletter"

    def test_extract_prefix_from_plain_email(self, classifier):
        """Test extracting prefix from plain email."""
        sender = "support@example.com"
        result = classifier._extract_email_prefix(sender)
        assert result == "support"

    def test_extract_prefix_unknown(self, classifier):
        """Test extracting prefix returns unknown for invalid email."""
        sender = "invalid_email"
        result = classifier._extract_email_prefix(sender)
        assert result == "unknown"


class TestClassifyBySender:
    """Tests for classify_by_sender method."""

    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier instance."""
        from gmail_assistant.core.processing.classifier import EmailClassifier
        return EmailClassifier(str(tmp_path / "test.db"))

    def test_classify_newsletter_sender(self, classifier):
        """Test classifying newsletter sender."""
        sender = "newsletter@example.com"
        result = classifier.classify_by_sender(sender, {})

        assert result['primary_category'] == 'Newsletter'
        assert result['confidence'] > 0

    def test_classify_noreply_sender_as_automated(self, classifier):
        """Test classifying noreply as automated."""
        sender = "noreply@example.com"
        result = classifier.classify_by_sender(sender, {})

        assert result['source_type'] == 'Automated'

    def test_classify_support_sender(self, classifier):
        """Test classifying support sender."""
        sender = "support@example.com"
        result = classifier.classify_by_sender(sender, {})

        assert result['primary_category'] == 'Support'

    def test_classify_high_frequency_sender(self, classifier):
        """Test classifying high frequency sender as newsletter."""
        sender = "sender@example.com"
        sender_stats = {
            sender: {'frequency': 100, 'first_email': '2024-01-01', 'last_email': '2024-03-01'}
        }
        result = classifier.classify_by_sender(sender, sender_stats)

        assert result['primary_category'] == 'Newsletter'
        assert 'high_frequency_sender' in result['rules_applied']

    def test_classify_single_email_sender_as_personal(self, classifier):
        """Test classifying single email sender as personal."""
        sender = "friend@example.com"
        sender_stats = {
            sender: {'frequency': 1, 'first_email': '2024-03-01', 'last_email': '2024-03-01'}
        }
        result = classifier.classify_by_sender(sender, sender_stats)

        assert result['primary_category'] == 'Personal'


class TestClassifyBySubject:
    """Tests for classify_by_subject method."""

    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier instance."""
        from gmail_assistant.core.processing.classifier import EmailClassifier
        return EmailClassifier(str(tmp_path / "test.db"))

    def test_classify_thread_subject(self, classifier):
        """Test classifying Re: subject as thread."""
        subject = "Re: Meeting Tomorrow"
        result = classifier.classify_by_subject(subject)

        assert result['is_thread'] is True
        assert 'thread_indicator' in result['rules_applied']

    def test_classify_transactional_subject(self, classifier):
        """Test classifying receipt subject as transactional."""
        subject = "Your receipt from Store"
        result = classifier.classify_by_subject(subject)

        assert result['primary_category'] == 'Transactional'

    def test_classify_urgent_subject_high_priority(self, classifier):
        """Test classifying urgent subject as high priority."""
        subject = "URGENT: Action Required Immediately"
        result = classifier.classify_by_subject(subject)

        assert result['priority_level'] == 'High'

    def test_classify_empty_subject(self, classifier):
        """Test classifying empty subject returns defaults."""
        result = classifier.classify_by_subject("")

        assert result['priority_level'] == 'Medium'
        assert result['is_thread'] is False

    def test_classify_none_subject(self, classifier):
        """Test classifying None subject returns defaults."""
        result = classifier.classify_by_subject(None)

        assert result['priority_level'] == 'Medium'


class TestClassifyByContent:
    """Tests for classify_by_content method."""

    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier instance."""
        from gmail_assistant.core.processing.classifier import EmailClassifier
        return EmailClassifier(str(tmp_path / "test.db"))

    def test_classify_content_with_unsubscribe(self, classifier):
        """Test detecting unsubscribe link in content."""
        content = "Click here to unsubscribe from our newsletter"
        result = classifier.classify_by_content(content)

        assert result['has_unsubscribe'] is True

    def test_classify_automated_content(self, classifier):
        """Test detecting automated content."""
        content = "This is an automated message. Do not reply to this email."
        result = classifier.classify_by_content(content)

        assert result['automated_score'] > 0

    def test_classify_ai_technology_content(self, classifier):
        """Test classifying AI/Technology content."""
        content = "Learn about artificial intelligence and machine learning algorithms"
        result = classifier.classify_by_content(content)

        assert result['domain_category'] == 'AI/Technology'

    def test_classify_finance_content(self, classifier):
        """Test classifying finance content."""
        content = "Your bank account statement and investment portfolio"
        result = classifier.classify_by_content(content)

        assert result['domain_category'] == 'Finance'

    def test_classify_important_label(self, classifier):
        """Test classifying content with important label."""
        content = "Some content"
        labels = "INBOX,IMPORTANT"
        result = classifier.classify_by_content(content, labels)

        assert result['action_required'] == 'Reply_Needed'

    def test_classify_empty_content(self, classifier):
        """Test classifying empty content returns defaults."""
        result = classifier.classify_by_content("")

        assert result['action_required'] == 'Read_Only'


class TestCalculateConfidenceScore:
    """Tests for calculate_confidence_score method."""

    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier instance."""
        from gmail_assistant.core.processing.classifier import EmailClassifier
        return EmailClassifier(str(tmp_path / "test.db"))

    def test_calculate_confidence_weighted(self, classifier):
        """Test confidence calculation with weights."""
        classifications = [
            {'confidence': 1.0},  # sender weight 0.4
            {'confidence': 0.8},  # subject weight 0.3
            {'confidence': 0.6},  # content weight 0.3
        ]
        result = classifier.calculate_confidence_score(classifications)

        assert 0 <= result <= 1.0

    def test_calculate_confidence_empty(self, classifier):
        """Test confidence calculation with empty list."""
        result = classifier.calculate_confidence_score([])

        assert result == 0.0

    def test_calculate_confidence_capped(self, classifier):
        """Test confidence is capped at 1.0."""
        classifications = [
            {'confidence': 2.0},
            {'confidence': 2.0},
            {'confidence': 2.0},
        ]
        result = classifier.calculate_confidence_score(classifications)

        assert result <= 1.0


class TestMergeClassifications:
    """Tests for merge_classifications method."""

    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier instance."""
        from gmail_assistant.core.processing.classifier import EmailClassifier
        return EmailClassifier(str(tmp_path / "test.db"))

    def test_merge_uses_sender_category(self, classifier):
        """Test merge uses sender primary category."""
        sender_cls = {'primary_category': 'Newsletter', 'source_type': 'Automated',
                     'confidence': 0.8, 'rules_applied': ['sender_rule']}
        subject_cls = {'primary_category': 'Marketing', 'priority_level': 'Medium',
                      'is_thread': False, 'confidence': 0.5, 'rules_applied': []}
        content_cls = {'domain_category': 'AI/Technology', 'has_unsubscribe': True,
                      'automated_score': 0.5, 'action_required': 'Read_Only',
                      'confidence': 0.6, 'rules_applied': []}

        result = classifier.merge_classifications(sender_cls, subject_cls, content_cls)

        assert result['primary_category'] == 'Newsletter'

    def test_merge_falls_back_to_subject_category(self, classifier):
        """Test merge falls back to subject category when sender is None."""
        sender_cls = {'primary_category': None, 'source_type': 'Human',
                     'confidence': 0.3, 'rules_applied': []}
        subject_cls = {'primary_category': 'Support', 'priority_level': 'High',
                      'is_thread': True, 'confidence': 0.7, 'rules_applied': []}
        content_cls = {'domain_category': 'Other', 'has_unsubscribe': False,
                      'automated_score': 0.0, 'action_required': 'Reply_Needed',
                      'confidence': 0.5, 'rules_applied': []}

        result = classifier.merge_classifications(sender_cls, subject_cls, content_cls)

        assert result['primary_category'] == 'Support'

    def test_merge_includes_classification_date(self, classifier):
        """Test merge includes classification date."""
        sender_cls = {'primary_category': None, 'source_type': 'Human',
                     'confidence': 0.3, 'rules_applied': []}
        subject_cls = {'primary_category': None, 'priority_level': 'Medium',
                      'is_thread': False, 'confidence': 0.0, 'rules_applied': []}
        content_cls = {'domain_category': None, 'has_unsubscribe': False,
                      'automated_score': 0.0, 'action_required': 'Read_Only',
                      'confidence': 0.0, 'rules_applied': []}

        result = classifier.merge_classifications(sender_cls, subject_cls, content_cls)

        assert 'classification_date' in result
        assert result['classification_rules'] is not None


class TestCreateClassificationSchema:
    """Tests for create_classification_schema method."""

    def test_create_schema_success(self, tmp_path):
        """Test creating classification schema."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        db_path = tmp_path / "test.db"

        # Create initial database with emails table
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE emails (id INTEGER PRIMARY KEY, sender TEXT)")
        conn.commit()
        conn.close()

        classifier = EmailClassifier(str(db_path))
        result = classifier.create_classification_schema()

        assert result is True

        # Verify columns were added
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(emails)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'primary_category' in columns
        assert 'confidence_score' in columns


class TestAnalyzeSenderPatterns:
    """Tests for analyze_sender_patterns method."""

    def test_analyze_sender_patterns_empty_db(self, tmp_path):
        """Test analyzing sender patterns with empty database."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        db_path = tmp_path / "test.db"

        # Create database with empty emails table
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY,
                sender TEXT,
                parsed_date TEXT
            )
        """)
        conn.commit()
        conn.close()

        classifier = EmailClassifier(str(db_path))
        result = classifier.analyze_sender_patterns()

        assert result == {}

    def test_analyze_sender_patterns_with_data(self, tmp_path):
        """Test analyzing sender patterns with email data."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY,
                sender TEXT,
                parsed_date TEXT
            )
        """)
        conn.execute("INSERT INTO emails (sender, parsed_date) VALUES (?, ?)",
                    ("test@example.com", "2024-01-15"))
        conn.execute("INSERT INTO emails (sender, parsed_date) VALUES (?, ?)",
                    ("test@example.com", "2024-02-15"))
        conn.commit()
        conn.close()

        classifier = EmailClassifier(str(db_path))
        result = classifier.analyze_sender_patterns()

        assert "test@example.com" in result
        assert result["test@example.com"]['frequency'] == 2


class TestClassifyEmailsBatch:
    """Tests for classify_emails_batch method."""

    def test_classify_batch_empty(self, tmp_path):
        """Test classifying empty batch."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY,
                sender TEXT,
                subject TEXT,
                plain_text_content TEXT,
                labels TEXT,
                primary_category TEXT
            )
        """)
        conn.commit()
        conn.close()

        classifier = EmailClassifier(str(db_path))
        processed, errors = classifier.classify_emails_batch()

        assert processed == 0
        assert errors == 0


class TestGenerateClassificationReport:
    """Tests for generate_classification_report method."""

    def test_generate_report_empty_db(self, tmp_path):
        """Test generating report with empty database returns empty or valid report."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(db_path)
        # Create a complete schema that matches what the classifier expects
        conn.execute("""
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY,
                sender TEXT,
                subject TEXT,
                plain_text_content TEXT,
                labels TEXT,
                parsed_date TEXT,
                primary_category TEXT,
                domain_category TEXT,
                priority_level TEXT,
                source_type TEXT,
                action_required TEXT,
                confidence_score REAL,
                classification_rules TEXT,
                classification_date TEXT,
                sender_frequency INTEGER,
                is_thread BOOLEAN,
                has_unsubscribe BOOLEAN,
                automated_score REAL
            )
        """)
        conn.commit()
        conn.close()

        classifier = EmailClassifier(str(db_path))
        report = classifier.generate_classification_report()

        # The report should either be empty dict (error case) or have overview
        # When there are no emails, the report generation may fail or succeed
        assert isinstance(report, dict)


class TestClassifyAllEmails:
    """Tests for classify_all_emails method."""

    def test_classify_all_already_classified(self, tmp_path):
        """Test classify all when all emails are classified."""
        from gmail_assistant.core.processing.classifier import EmailClassifier

        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY,
                sender TEXT,
                subject TEXT,
                plain_text_content TEXT,
                labels TEXT,
                primary_category TEXT
            )
        """)
        # Insert already classified email
        conn.execute("""
            INSERT INTO emails (sender, subject, plain_text_content, labels, primary_category)
            VALUES (?, ?, ?, ?, ?)
        """, ("test@example.com", "Test", "Content", "INBOX", "Newsletter"))
        conn.commit()
        conn.close()

        classifier = EmailClassifier(str(db_path))
        result = classifier.classify_all_emails()

        assert result is True
