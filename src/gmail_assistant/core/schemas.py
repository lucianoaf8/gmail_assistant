"""
Canonical email data models using Pydantic for validation.
Single source of truth for all email data structures.

This module replaces duplicate structures:
- EmailMetadata (protocols.py) - DEPRECATED
- EmailData (newsletter_cleaner.py) - DEPRECATED

Use Email class for all new code.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import warnings


class ParticipantType(str, Enum):
    """Email participant types."""
    FROM = "from"
    TO = "to"
    CC = "cc"
    BCC = "bcc"


class EmailParticipant(BaseModel):
    """Email participant with type and parsed domain."""
    address: str = Field(..., description="Email address")
    type: ParticipantType = Field(..., description="Participant type")
    display_name: Optional[str] = Field(default=None, description="Display name")

    model_config = ConfigDict(frozen=True)

    @property
    def domain(self) -> str:
        """Extract domain from email address."""
        return self.address.split("@")[1] if "@" in self.address else ""


class Email(BaseModel):
    """
    Canonical email model - single source of truth.

    Replaces:
    - EmailMetadata (protocols.py)
    - EmailData (newsletter_cleaner.py)

    Usage:
        email = Email(
            gmail_id="abc123",
            thread_id="thread123",
            subject="Test Email",
            sender="test@example.com",
            date=datetime.now()
        )
    """
    # Identity
    gmail_id: str = Field(..., description="Unique Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")

    # Core metadata
    subject: str = Field(default="", description="Email subject line")
    sender: str = Field(..., description="Sender email address")
    recipients: List[EmailParticipant] = Field(default_factory=list, description="Recipients")
    date: datetime = Field(..., description="Email received timestamp")

    # Content
    body_plain: Optional[str] = Field(default=None, description="Plain text body")
    body_html: Optional[str] = Field(default=None, description="HTML body")

    # Gmail-specific
    labels: List[str] = Field(default_factory=list, description="Gmail labels")
    snippet: str = Field(default="", description="Email preview snippet")
    history_id: int = Field(default=0, description="Gmail history ID for sync")
    size_estimate: int = Field(default=0, description="Estimated size in bytes")

    # Status flags
    is_unread: bool = Field(default=True)
    is_starred: bool = Field(default=False)
    has_attachments: bool = Field(default=False)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        populate_by_name=True
    )

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date from various formats."""
        if v is None:
            return datetime.now()
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Handle multiple date formats from Gmail
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S.%f%z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]
            # Remove timezone name in parentheses if present
            clean_v = v.split(' (')[0].strip()
            for fmt in formats:
                try:
                    return datetime.strptime(clean_v, fmt)
                except ValueError:
                    continue
            # Last resort: try fromisoformat
            try:
                return datetime.fromisoformat(clean_v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Unable to parse date: {v}")
        return v

    @property
    def sender_domain(self) -> str:
        """Extract sender's domain."""
        return self.sender.split("@")[1] if "@" in self.sender else ""

    @property
    def year_month(self) -> str:
        """Get year-month string for partitioning."""
        return self.date.strftime("%Y-%m")

    def to_email_metadata(self) -> 'EmailMetadataCompat':
        """
        Convert to legacy EmailMetadata for backward compatibility.

        DEPRECATED: Use Email directly instead.
        """
        warnings.warn(
            "to_email_metadata() is deprecated. Use Email directly.",
            DeprecationWarning,
            stacklevel=2
        )
        return EmailMetadataCompat(
            id=self.gmail_id,
            thread_id=self.thread_id,
            subject=self.subject,
            sender=self.sender,
            recipients=[p.address for p in self.recipients if p.type == ParticipantType.TO],
            date=self.date.isoformat(),
            labels=self.labels,
            snippet=self.snippet,
            size_estimate=self.size_estimate
        )

    def to_email_data(self) -> 'EmailDataCompat':
        """
        Convert to legacy EmailData for backward compatibility.

        DEPRECATED: Use Email directly instead.
        """
        warnings.warn(
            "to_email_data() is deprecated. Use Email directly.",
            DeprecationWarning,
            stacklevel=2
        )
        return EmailDataCompat(
            id=self.gmail_id,
            subject=self.subject,
            sender=self.sender,
            date=self.date.isoformat(),
            labels=self.labels,
            thread_id=self.thread_id,
            body_snippet=self.snippet
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.model_dump(mode='json')

    @classmethod
    def from_gmail_message(cls, message: Dict[str, Any]) -> 'Email':
        """
        Create Email from Gmail API message response.

        Args:
            message: Gmail API message object

        Returns:
            Email instance
        """
        headers = {
            h['name'].lower(): h['value']
            for h in message.get('payload', {}).get('headers', [])
        }

        # Extract sender email from "Name <email>" format
        sender_raw = headers.get('from', '')
        if '<' in sender_raw and '>' in sender_raw:
            sender = sender_raw.split('<')[-1].rstrip('>').strip()
        else:
            sender = sender_raw.strip()

        # Parse recipients
        recipients = []
        for recipient_type, header_name in [
            (ParticipantType.TO, 'to'),
            (ParticipantType.CC, 'cc'),
            (ParticipantType.BCC, 'bcc')
        ]:
            if header_name in headers:
                for addr in headers[header_name].split(','):
                    addr = addr.strip()
                    if '<' in addr and '>' in addr:
                        email_addr = addr.split('<')[-1].rstrip('>').strip()
                        display = addr.split('<')[0].strip().strip('"')
                    else:
                        email_addr = addr
                        display = None
                    if email_addr:
                        recipients.append(EmailParticipant(
                            address=email_addr,
                            type=recipient_type,
                            display_name=display
                        ))

        labels = message.get('labelIds', [])

        return cls(
            gmail_id=message['id'],
            thread_id=message.get('threadId', ''),
            subject=headers.get('subject', ''),
            sender=sender or 'unknown@unknown.com',
            recipients=recipients,
            date=headers.get('date', ''),
            labels=labels,
            snippet=message.get('snippet', ''),
            history_id=int(message.get('historyId', 0)),
            size_estimate=message.get('sizeEstimate', 0),
            is_unread='UNREAD' in labels,
            is_starred='STARRED' in labels
        )


class EmailBatch(BaseModel):
    """Batch of emails for bulk operations."""
    emails: List[Email]
    total_count: int
    next_page_token: Optional[str] = None
    history_id: Optional[int] = None


# =============================================================================
# Backward Compatibility Classes (DEPRECATED)
# =============================================================================

class EmailMetadataCompat(BaseModel):
    """
    DEPRECATED: Legacy EmailMetadata for backward compatibility.
    Use Email class instead.
    """
    id: str
    thread_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: str
    labels: List[str]
    snippet: str = ""
    size_estimate: int = 0

    def __init__(self, **data):
        warnings.warn(
            "EmailMetadataCompat is deprecated. Use Email class instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(**data)

    def to_email(self) -> Email:
        """Convert to canonical Email model."""
        return Email(
            gmail_id=self.id,
            thread_id=self.thread_id,
            subject=self.subject,
            sender=self.sender,
            recipients=[
                EmailParticipant(address=r, type=ParticipantType.TO)
                for r in self.recipients
            ],
            date=self.date,
            labels=self.labels,
            snippet=self.snippet,
            size_estimate=self.size_estimate
        )


class EmailDataCompat(BaseModel):
    """
    DEPRECATED: Legacy EmailData for backward compatibility.
    Use Email class instead.
    """
    id: str
    subject: str
    sender: str
    date: str
    labels: Optional[List[str]] = None
    thread_id: Optional[str] = None
    body_snippet: str = ""

    def __init__(self, **data):
        warnings.warn(
            "EmailDataCompat is deprecated. Use Email class instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(**data)

    def to_email(self) -> Email:
        """Convert to canonical Email model."""
        return Email(
            gmail_id=self.id,
            thread_id=self.thread_id or "",
            subject=self.subject,
            sender=self.sender,
            date=self.date,
            labels=self.labels or [],
            snippet=self.body_snippet
        )


# =============================================================================
# Factory Functions
# =============================================================================

def create_email_from_dict(data: Dict[str, Any]) -> Email:
    """
    Create Email from dictionary with flexible field mapping.

    Handles various field naming conventions:
    - gmail_id / id / message_id
    - body_snippet / snippet
    - etc.
    """
    # Normalize field names
    normalized = {
        'gmail_id': data.get('gmail_id') or data.get('id') or data.get('message_id', ''),
        'thread_id': data.get('thread_id') or data.get('threadId', ''),
        'subject': data.get('subject', ''),
        'sender': data.get('sender') or data.get('from', ''),
        'date': data.get('date') or data.get('received_date') or data.get('parsed_date', ''),
        'labels': data.get('labels', []),
        'snippet': data.get('snippet') or data.get('body_snippet', ''),
        'body_plain': data.get('body_plain') or data.get('body_text') or data.get('message_content'),
        'body_html': data.get('body_html'),
    }

    # Handle labels as comma-separated string
    if isinstance(normalized['labels'], str):
        normalized['labels'] = [l.strip() for l in normalized['labels'].split(',') if l.strip()]

    return Email(**normalized)
