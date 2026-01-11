"""
Comprehensive tests for schemas.py module.
Tests Email, EmailBatch, and related Pydantic models.
"""

import warnings
from datetime import datetime
from unittest import mock

import pytest


class TestParticipantType:
    """Tests for ParticipantType enum."""

    def test_participant_type_values(self):
        """Test all ParticipantType values exist."""
        from gmail_assistant.core.schemas import ParticipantType

        assert ParticipantType.FROM.value == "from"
        assert ParticipantType.TO.value == "to"
        assert ParticipantType.CC.value == "cc"
        assert ParticipantType.BCC.value == "bcc"


class TestEmailParticipant:
    """Tests for EmailParticipant model."""

    def test_participant_creation(self):
        """Test creating EmailParticipant."""
        from gmail_assistant.core.schemas import EmailParticipant, ParticipantType

        participant = EmailParticipant(
            address="test@example.com",
            type=ParticipantType.TO,
            display_name="Test User"
        )

        assert participant.address == "test@example.com"
        assert participant.type == ParticipantType.TO
        assert participant.display_name == "Test User"

    def test_participant_domain_property(self):
        """Test domain property extraction."""
        from gmail_assistant.core.schemas import EmailParticipant, ParticipantType

        participant = EmailParticipant(
            address="test@example.com",
            type=ParticipantType.TO
        )

        assert participant.domain == "example.com"

    def test_participant_domain_no_at_sign(self):
        """Test domain property with invalid email."""
        from gmail_assistant.core.schemas import EmailParticipant, ParticipantType

        participant = EmailParticipant(
            address="invalid_email",
            type=ParticipantType.TO
        )

        assert participant.domain == ""

    def test_participant_is_frozen(self):
        """Test EmailParticipant is immutable."""
        from gmail_assistant.core.schemas import EmailParticipant, ParticipantType

        participant = EmailParticipant(
            address="test@example.com",
            type=ParticipantType.TO
        )

        with pytest.raises(Exception):  # ValidationError for frozen model
            participant.address = "new@example.com"


class TestEmail:
    """Tests for Email model."""

    def test_email_creation_minimal(self):
        """Test creating Email with minimal fields."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date=datetime.now()
        )

        assert email.gmail_id == "msg123"
        assert email.thread_id == "thread123"
        assert email.sender == "test@example.com"

    def test_email_creation_full(self):
        """Test creating Email with all fields."""
        from gmail_assistant.core.schemas import Email, EmailParticipant, ParticipantType

        recipients = [
            EmailParticipant(address="recipient@example.com", type=ParticipantType.TO)
        ]

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            subject="Test Subject",
            sender="sender@example.com",
            recipients=recipients,
            date=datetime.now(),
            body_plain="Plain text body",
            body_html="<p>HTML body</p>",
            labels=["INBOX", "UNREAD"],
            snippet="Email preview...",
            history_id=12345,
            size_estimate=1024,
            is_unread=True,
            is_starred=False,
            has_attachments=True
        )

        assert email.subject == "Test Subject"
        assert len(email.recipients) == 1
        assert email.body_plain == "Plain text body"
        assert email.has_attachments is True

    def test_email_default_values(self):
        """Test Email default values."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date=datetime.now()
        )

        assert email.subject == ""
        assert email.recipients == []
        assert email.labels == []
        assert email.is_unread is True
        assert email.is_starred is False

    def test_email_parse_date_string(self):
        """Test Email parses date string."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date="Mon, 15 Jan 2024 10:30:00 +0000"
        )

        assert isinstance(email.date, datetime)
        assert email.date.year == 2024
        assert email.date.month == 1

    def test_email_parse_iso_date(self):
        """Test Email parses ISO date format."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date="2024-01-15T10:30:00+00:00"
        )

        assert email.date.year == 2024

    def test_email_sender_domain_property(self):
        """Test sender_domain property."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date=datetime.now()
        )

        assert email.sender_domain == "example.com"

    def test_email_year_month_property(self):
        """Test year_month property."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date=datetime(2024, 3, 15)
        )

        assert email.year_month == "2024-03"

    def test_email_to_dict(self):
        """Test to_dict method."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date=datetime(2024, 1, 15, 10, 30, 0)
        )

        result = email.to_dict()

        assert isinstance(result, dict)
        assert result['gmail_id'] == "msg123"
        assert 'date' in result

    def test_email_to_email_metadata_deprecated(self):
        """Test to_email_metadata emits deprecation warning."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date=datetime.now()
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = email.to_email_metadata()

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_email_to_email_data_deprecated(self):
        """Test to_email_data emits deprecation warning."""
        from gmail_assistant.core.schemas import Email

        email = Email(
            gmail_id="msg123",
            thread_id="thread123",
            sender="test@example.com",
            date=datetime.now()
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = email.to_email_data()

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)


class TestEmailFromGmailMessage:
    """Tests for Email.from_gmail_message factory method."""

    def test_from_gmail_message_basic(self):
        """Test creating Email from Gmail API response."""
        from gmail_assistant.core.schemas import Email

        message = {
            'id': 'msg123',
            'threadId': 'thread123',
            'labelIds': ['INBOX', 'UNREAD'],
            'snippet': 'Email preview...',
            'historyId': '12345',
            'sizeEstimate': 1024,
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'recipient@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': 'Mon, 15 Jan 2024 10:30:00 +0000'}
                ]
            }
        }

        email = Email.from_gmail_message(message)

        assert email.gmail_id == 'msg123'
        assert email.thread_id == 'thread123'
        assert email.sender == 'sender@example.com'
        assert email.subject == 'Test Subject'
        assert email.is_unread is True

    def test_from_gmail_message_with_display_name(self):
        """Test parsing sender with display name."""
        from gmail_assistant.core.schemas import Email

        message = {
            'id': 'msg123',
            'threadId': 'thread123',
            'labelIds': [],
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'John Doe <john@example.com>'},
                    {'name': 'Date', 'value': '2024-01-15'}
                ]
            }
        }

        email = Email.from_gmail_message(message)

        assert email.sender == 'john@example.com'

    def test_from_gmail_message_multiple_recipients(self):
        """Test parsing multiple recipients."""
        from gmail_assistant.core.schemas import Email, ParticipantType

        message = {
            'id': 'msg123',
            'threadId': 'thread123',
            'labelIds': [],
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'user1@example.com, user2@example.com'},
                    {'name': 'Cc', 'value': 'cc@example.com'},
                    {'name': 'Date', 'value': '2024-01-15'}
                ]
            }
        }

        email = Email.from_gmail_message(message)

        to_recipients = [r for r in email.recipients if r.type == ParticipantType.TO]
        cc_recipients = [r for r in email.recipients if r.type == ParticipantType.CC]

        assert len(to_recipients) == 2
        assert len(cc_recipients) == 1

    def test_from_gmail_message_starred(self):
        """Test detecting starred email."""
        from gmail_assistant.core.schemas import Email

        message = {
            'id': 'msg123',
            'threadId': 'thread123',
            'labelIds': ['STARRED'],
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': '2024-01-15'}
                ]
            }
        }

        email = Email.from_gmail_message(message)

        assert email.is_starred is True


class TestEmailBatch:
    """Tests for EmailBatch model."""

    def test_batch_creation(self):
        """Test creating EmailBatch."""
        from gmail_assistant.core.schemas import Email, EmailBatch

        emails = [
            Email(
                gmail_id=f"msg{i}",
                thread_id=f"thread{i}",
                sender="test@example.com",
                date=datetime.now()
            )
            for i in range(3)
        ]

        batch = EmailBatch(
            emails=emails,
            total_count=100,
            next_page_token="token123",
            history_id=99999
        )

        assert len(batch.emails) == 3
        assert batch.total_count == 100
        assert batch.next_page_token == "token123"
        assert batch.history_id == 99999

    def test_batch_optional_fields(self):
        """Test EmailBatch optional fields."""
        from gmail_assistant.core.schemas import EmailBatch

        batch = EmailBatch(
            emails=[],
            total_count=0
        )

        assert batch.next_page_token is None
        assert batch.history_id is None


class TestEmailMetadataCompat:
    """Tests for EmailMetadataCompat backward compatibility."""

    def test_compat_emits_deprecation_warning(self):
        """Test EmailMetadataCompat emits deprecation warning."""
        from gmail_assistant.core.schemas import EmailMetadataCompat

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compat = EmailMetadataCompat(
                id="msg123",
                thread_id="thread123",
                subject="Test",
                sender="test@example.com",
                recipients=["recipient@example.com"],
                date="2024-01-15",
                labels=["INBOX"]
            )

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_compat_to_email_conversion(self):
        """Test converting EmailMetadataCompat to Email."""
        from gmail_assistant.core.schemas import EmailMetadataCompat

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = EmailMetadataCompat(
                id="msg123",
                thread_id="thread123",
                subject="Test",
                sender="test@example.com",
                recipients=["recipient@example.com"],
                date="2024-01-15",
                labels=["INBOX"],
                snippet="Preview",
                size_estimate=1024
            )

            email = compat.to_email()

            assert email.gmail_id == "msg123"
            assert email.subject == "Test"


class TestEmailDataCompat:
    """Tests for EmailDataCompat backward compatibility."""

    def test_compat_emits_deprecation_warning(self):
        """Test EmailDataCompat emits deprecation warning."""
        from gmail_assistant.core.schemas import EmailDataCompat

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compat = EmailDataCompat(
                id="msg123",
                subject="Test",
                sender="test@example.com",
                date="2024-01-15"
            )

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_compat_to_email_conversion(self):
        """Test converting EmailDataCompat to Email."""
        from gmail_assistant.core.schemas import EmailDataCompat

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = EmailDataCompat(
                id="msg123",
                subject="Test",
                sender="test@example.com",
                date="2024-01-15",
                labels=["INBOX"],
                thread_id="thread123",
                body_snippet="Preview"
            )

            email = compat.to_email()

            assert email.gmail_id == "msg123"
            assert email.thread_id == "thread123"


class TestCreateEmailFromDict:
    """Tests for create_email_from_dict factory function."""

    def test_create_from_dict_basic(self):
        """Test creating Email from basic dict."""
        from gmail_assistant.core.schemas import create_email_from_dict

        data = {
            'gmail_id': 'msg123',
            'thread_id': 'thread123',
            'sender': 'test@example.com',
            'date': '2024-01-15'
        }

        email = create_email_from_dict(data)

        assert email.gmail_id == 'msg123'
        assert email.sender == 'test@example.com'

    def test_create_from_dict_normalized_fields(self):
        """Test creating Email normalizes field names."""
        from gmail_assistant.core.schemas import create_email_from_dict

        data = {
            'id': 'msg123',  # Instead of gmail_id
            'threadId': 'thread123',  # Instead of thread_id
            'from': 'test@example.com',  # Instead of sender
            'received_date': '2024-01-15'  # Instead of date
        }

        email = create_email_from_dict(data)

        assert email.gmail_id == 'msg123'
        assert email.sender == 'test@example.com'

    def test_create_from_dict_handles_labels_string(self):
        """Test creating Email handles comma-separated labels."""
        from gmail_assistant.core.schemas import create_email_from_dict

        data = {
            'gmail_id': 'msg123',
            'thread_id': 'thread123',
            'sender': 'test@example.com',
            'date': '2024-01-15',
            'labels': 'INBOX, UNREAD, IMPORTANT'
        }

        email = create_email_from_dict(data)

        assert 'INBOX' in email.labels
        assert 'UNREAD' in email.labels
        assert 'IMPORTANT' in email.labels
