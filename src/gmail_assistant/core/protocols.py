"""
Protocol definitions for Gmail Fetcher operations.

This module defines the interfaces (protocols) for all major components
of the Gmail Fetcher system, enabling structural subtyping and
dependency injection patterns.

Using typing.Protocol for structural subtyping allows:
- Duck typing with type safety
- Easier testing with mock objects
- Clear API contracts
- Decoupled components
"""

from abc import abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)
from pathlib import Path
from dataclasses import dataclass

# Type variables for generic protocols
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
EmailData = TypeVar('EmailData', bound=Dict[str, Any])


# =============================================================================
# Data Transfer Objects (DTOs)
# =============================================================================

@dataclass
class EmailMetadata:
    """Metadata for a single email message."""
    id: str
    thread_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: str
    labels: List[str]
    snippet: str = ""
    size_estimate: int = 0


@dataclass
class FetchResult:
    """Result of an email fetch operation."""
    success: bool
    emails_fetched: int
    emails_failed: int
    output_directory: str
    error_message: Optional[str] = None


@dataclass
class DeleteResult:
    """Result of an email delete operation."""
    deleted: int
    failed: int
    trashed: int = 0
    error_messages: List[str] = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []


@dataclass
class ParseResult:
    """Result of an email parsing operation."""
    success: bool
    markdown: str
    strategy: str
    quality: float
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# =============================================================================
# Authentication Protocols
# =============================================================================

@runtime_checkable
class CredentialProviderProtocol(Protocol):
    """Protocol for credential providers."""

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        ...

    def get_credentials(self) -> Any:
        """Get the current credentials object."""
        ...

    def refresh_credentials(self) -> bool:
        """Refresh expired credentials."""
        ...

    def revoke_credentials(self) -> bool:
        """Revoke current credentials."""
        ...


@runtime_checkable
class GmailClientProtocol(Protocol):
    """
    Protocol for Gmail API client operations.

    This protocol defines the base interface for interacting with the Gmail API.
    Implementations must provide authentication and service access.

    Example:
        class MyGmailClient:
            def authenticate(self) -> bool:
                # Implementation
                return True

            def get_service(self) -> Any:
                return self._service

            @property
            def is_authenticated(self) -> bool:
                return self._authenticated
    """

    def authenticate(self) -> bool:
        """
        Authenticate with the Gmail API.

        Returns:
            True if authentication was successful, False otherwise.

        Raises:
            AuthenticationError: If authentication fails critically.
        """
        ...

    def get_service(self) -> Any:
        """
        Get the authenticated Gmail API service object.

        Returns:
            The Gmail API service object for making API calls.

        Raises:
            RuntimeError: If not authenticated.
        """
        ...

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated with the Gmail API."""
        ...

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the authenticated user.

        Returns:
            Dictionary with user info (email, messages_total, etc.)
            or None if not available.
        """
        ...


# =============================================================================
# Fetcher Protocols
# =============================================================================

@runtime_checkable
class EmailFetcherProtocol(Protocol):
    """
    Protocol for email fetching operations.

    Defines the interface for fetching and downloading emails from Gmail.
    Implementations should handle pagination, rate limiting, and error recovery.
    """

    def search_messages(
        self,
        query: str,
        max_results: int = 100
    ) -> List[str]:
        """
        Search for messages matching the given query.

        Args:
            query: Gmail search query (e.g., "is:unread", "from:example.com")
            max_results: Maximum number of message IDs to return

        Returns:
            List of message IDs matching the query.
        """
        ...

    def get_message(
        self,
        message_id: str,
        format: str = "full"
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single message by ID.

        Args:
            message_id: The Gmail message ID
            format: Message format ("full", "minimal", "metadata", "raw")

        Returns:
            Message data dictionary or None if not found.
        """
        ...

    def get_message_metadata(
        self,
        message_id: str
    ) -> Optional[EmailMetadata]:
        """
        Get metadata for a single message.

        Args:
            message_id: The Gmail message ID

        Returns:
            EmailMetadata object or None if not found.
        """
        ...

    def download_emails(
        self,
        query: str,
        max_emails: int = 100,
        output_dir: str = "gmail_backup",
        format_type: str = "both",
        organize_by: str = "date"
    ) -> FetchResult:
        """
        Download emails matching query to local files.

        Args:
            query: Gmail search query
            max_emails: Maximum number of emails to download
            output_dir: Directory to save emails
            format_type: Output format ("eml", "markdown", "both")
            organize_by: Organization strategy ("date", "sender", "none")

        Returns:
            FetchResult with operation summary.
        """
        ...

    def get_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get the Gmail profile for the authenticated user.

        Returns:
            Profile dictionary with email, messagesTotal, threadsTotal.
        """
        ...


@runtime_checkable
class StreamingFetcherProtocol(Protocol):
    """Protocol for streaming email fetching with memory efficiency."""

    def stream_messages(
        self,
        query: str,
        batch_size: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream messages matching query.

        Args:
            query: Gmail search query
            batch_size: Number of messages to fetch per batch

        Yields:
            Message data dictionaries.
        """
        ...

    def stream_message_ids(
        self,
        query: str,
        batch_size: int = 500
    ) -> Iterator[str]:
        """
        Stream message IDs matching query.

        Args:
            query: Gmail search query
            batch_size: Number of IDs to fetch per batch

        Yields:
            Message ID strings.
        """
        ...


# =============================================================================
# Deleter Protocols
# =============================================================================

@runtime_checkable
class EmailDeleterProtocol(Protocol):
    """
    Protocol for email deletion operations.

    Defines the interface for deleting emails from Gmail.
    Implementations must handle safety confirmations and rate limiting.
    """

    def delete_emails(
        self,
        email_ids: List[str],
        batch_size: int = 100
    ) -> DeleteResult:
        """
        Permanently delete emails by ID.

        Args:
            email_ids: List of Gmail message IDs to delete
            batch_size: Number of emails to delete per batch

        Returns:
            DeleteResult with operation summary.

        Warning:
            This permanently deletes emails - they cannot be recovered!
        """
        ...

    def trash_emails(
        self,
        email_ids: List[str]
    ) -> DeleteResult:
        """
        Move emails to trash.

        Args:
            email_ids: List of Gmail message IDs to trash

        Returns:
            DeleteResult with operation summary.

        Note:
            Trashed emails can be recovered within 30 days.
        """
        ...

    def get_email_count(
        self,
        query: str
    ) -> int:
        """
        Get count of emails matching query.

        Args:
            query: Gmail search query

        Returns:
            Estimated number of matching emails.
        """
        ...

    def delete_by_query(
        self,
        query: str,
        dry_run: bool = True,
        max_delete: Optional[int] = None
    ) -> DeleteResult:
        """
        Delete emails matching a query.

        Args:
            query: Gmail search query
            dry_run: If True, only show what would be deleted
            max_delete: Maximum number of emails to delete

        Returns:
            DeleteResult with operation summary.
        """
        ...


# =============================================================================
# Parser Protocols
# =============================================================================

@runtime_checkable
class EmailParserProtocol(Protocol):
    """
    Protocol for email parsing operations.

    Defines the interface for parsing email content and converting
    between formats (EML, HTML, Markdown).
    """

    def parse_eml(
        self,
        file_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Parse an EML file and extract its contents.

        Args:
            file_path: Path to the EML file

        Returns:
            Dictionary with parsed email data including:
            - headers: Dict of email headers
            - body_text: Plain text body
            - body_html: HTML body
            - attachments: List of attachment info
        """
        ...

    def parse_html(
        self,
        html_content: str,
        sender: str = ""
    ) -> ParseResult:
        """
        Parse HTML email content.

        Args:
            html_content: Raw HTML content
            sender: Sender email/domain for targeted parsing

        Returns:
            ParseResult with parsed content.
        """
        ...

    def extract_headers(
        self,
        headers: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """
        Extract and normalize email headers.

        Args:
            headers: List of header dictionaries with 'name' and 'value'

        Returns:
            Normalized header dictionary.
        """
        ...


@runtime_checkable
class MarkdownConverterProtocol(Protocol):
    """Protocol for converting email content to Markdown."""

    def to_markdown(
        self,
        email_data: Dict[str, Any]
    ) -> str:
        """
        Convert email data to Markdown format.

        Args:
            email_data: Dictionary with email content and metadata

        Returns:
            Markdown formatted string.
        """
        ...

    def clean_html(
        self,
        html_content: str
    ) -> str:
        """
        Clean and prepare HTML for conversion.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned HTML string.
        """
        ...

    def html_to_markdown(
        self,
        html_content: str
    ) -> str:
        """
        Convert HTML to Markdown.

        Args:
            html_content: HTML content

        Returns:
            Markdown formatted string.
        """
        ...


# =============================================================================
# Output Protocols
# =============================================================================

@runtime_checkable
class OutputPluginProtocol(Protocol):
    """Protocol for output format plugins."""

    @property
    def name(self) -> str:
        """Plugin name identifier."""
        ...

    @property
    def extension(self) -> str:
        """File extension for this format (e.g., '.eml', '.md')."""
        ...

    def generate(
        self,
        email_data: Dict[str, Any]
    ) -> str:
        """
        Generate output content from email data.

        Args:
            email_data: Dictionary with email content and metadata

        Returns:
            Formatted content string.
        """
        ...

    def save(
        self,
        content: str,
        path: Path
    ) -> bool:
        """
        Save content to file.

        Args:
            content: Content to save
            path: File path

        Returns:
            True if successful.
        """
        ...


@runtime_checkable
class OrganizationPluginProtocol(Protocol):
    """Protocol for file organization plugins."""

    @property
    def name(self) -> str:
        """Plugin name identifier."""
        ...

    def get_path(
        self,
        email_data: Dict[str, Any],
        base_dir: Path
    ) -> Path:
        """
        Determine the output path for an email.

        Args:
            email_data: Dictionary with email metadata
            base_dir: Base output directory

        Returns:
            Full path for the email file.
        """
        ...


# =============================================================================
# Caching Protocols
# =============================================================================

@runtime_checkable
class CacheProtocol(Protocol[T]):
    """Generic protocol for cache implementations."""

    def get(
        self,
        key: str,
        default: Optional[T] = None
    ) -> Optional[T]:
        """Get value from cache."""
        ...

    def put(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None
    ) -> bool:
        """Put value in cache."""
        ...

    def invalidate(
        self,
        key: str
    ) -> bool:
        """Invalidate cache entry."""
        ...

    def clear(self) -> None:
        """Clear entire cache."""
        ...


# =============================================================================
# Rate Limiting Protocols
# =============================================================================

@runtime_checkable
class RateLimiterProtocol(Protocol):
    """Protocol for rate limiting implementations."""

    def wait_if_needed(
        self,
        quota_cost: int = 1
    ) -> float:
        """
        Wait if rate limit would be exceeded.

        Args:
            quota_cost: Cost of the upcoming operation

        Returns:
            Time waited in seconds.
        """
        ...

    def check_quota(self) -> Dict[str, Any]:
        """
        Check current quota status.

        Returns:
            Dictionary with quota information.
        """
        ...

    def reset(self) -> None:
        """Reset rate limiter state."""
        ...


# =============================================================================
# Service Container Protocol
# =============================================================================

@runtime_checkable
class ServiceContainerProtocol(Protocol):
    """Protocol for dependency injection containers."""

    def register(
        self,
        service_type: type,
        instance: Any
    ) -> None:
        """Register a service instance."""
        ...

    def register_factory(
        self,
        service_type: type,
        factory: Callable[[], Any]
    ) -> None:
        """Register a factory function for a service."""
        ...

    def resolve(
        self,
        service_type: type
    ) -> Any:
        """Resolve a service by type."""
        ...

    def has_service(
        self,
        service_type: type
    ) -> bool:
        """Check if a service is registered."""
        ...


# =============================================================================
# Validation Protocols
# =============================================================================

@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol for input validation."""

    def validate_email(
        self,
        email: str
    ) -> str:
        """Validate email address format."""
        ...

    def validate_gmail_query(
        self,
        query: str
    ) -> str:
        """Validate Gmail search query."""
        ...

    def validate_file_path(
        self,
        path: Union[str, Path],
        must_exist: bool = False
    ) -> Path:
        """Validate file path."""
        ...

    def validate_batch_size(
        self,
        size: int,
        max_allowed: int = 1000
    ) -> int:
        """Validate batch size."""
        ...


# =============================================================================
# Error Handling Protocols
# =============================================================================

@runtime_checkable
class ErrorHandlerProtocol(Protocol):
    """Protocol for error handling."""

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle an error with context."""
        ...

    def is_recoverable(
        self,
        error: Exception
    ) -> bool:
        """Check if error is recoverable."""
        ...

    def get_recovery_action(
        self,
        error: Exception
    ) -> Optional[Callable[[], bool]]:
        """Get recovery action for error."""
        ...


# =============================================================================
# Type Aliases for Common Patterns
# =============================================================================

# Common callback types
ProgressCallback = Callable[[int, int], None]  # (current, total)
ErrorCallback = Callable[[Exception], None]
SuccessCallback = Callable[[Dict[str, Any]], None]

# Email-related type aliases
MessageId = str
ThreadId = str
EmailHeaders = Dict[str, str]
EmailBody = Dict[str, str]  # {'text': ..., 'html': ...}

# Operation result types
OperationResult = Dict[str, Union[int, bool, str, List[str]]]


# =============================================================================
# Protocol Utilities
# =============================================================================

def implements_protocol(obj: Any, protocol: type) -> bool:
    """
    Check if an object implements a protocol.

    Args:
        obj: Object to check
        protocol: Protocol class to check against

    Returns:
        True if object implements the protocol.
    """
    return isinstance(obj, protocol)


def assert_protocol(obj: Any, protocol: type, name: str = "object") -> None:
    """
    Assert that an object implements a protocol.

    Args:
        obj: Object to check
        protocol: Protocol class to check against
        name: Name for error message

    Raises:
        TypeError: If object doesn't implement protocol.
    """
    if not implements_protocol(obj, protocol):
        raise TypeError(
            f"{name} must implement {protocol.__name__}, "
            f"got {type(obj).__name__}"
        )
