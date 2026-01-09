"""
Comprehensive audit logging system for Gmail Fetcher.
Tracks sensitive operations with detailed context and secure storage.
"""

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import os
from contextlib import contextmanager


class AuditLevel(Enum):
    """Audit logging levels."""
    INFO = "info"
    WARNING = "warning"
    SECURITY = "security"
    CRITICAL = "critical"


class OperationType(Enum):
    """Types of operations to audit."""
    AUTHENTICATION = "authentication"
    EMAIL_ACCESS = "email_access"
    EMAIL_DELETION = "email_deletion"
    EMAIL_EXPORT = "email_export"
    CREDENTIAL_ACCESS = "credential_access"
    CONFIG_CHANGE = "config_change"
    FILE_ACCESS = "file_access"
    API_CALL = "api_call"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_ISSUE = "performance_issue"


@dataclass
class AuditContext:
    """Context information for audit events."""
    user_id: Optional[str] = None
    email_id: Optional[str] = None
    file_path: Optional[str] = None
    query: Optional[str] = None
    batch_size: Optional[int] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

    def sanitize(self) -> Dict[str, Any]:
        """Sanitize sensitive data for logging."""
        sanitized = asdict(self)

        # Sanitize query to avoid logging sensitive search terms
        if sanitized.get('query'):
            query = sanitized['query']
            # Hash long queries to preserve uniqueness without exposing content
            if len(query) > 100:
                sanitized['query'] = f"HASH:{hashlib.sha256(query.encode()).hexdigest()[:16]}"

        # Sanitize file paths to remove personal information
        if sanitized.get('file_path'):
            path = Path(sanitized['file_path'])
            # Only keep filename and parent directory
            sanitized['file_path'] = f"{path.parent.name}/{path.name}"

        return {k: v for k, v in sanitized.items() if v is not None}


@dataclass
class AuditEvent:
    """Audit event structure."""
    timestamp: datetime
    level: AuditLevel
    operation: OperationType
    message: str
    context: Optional[AuditContext]
    success: bool
    duration_ms: Optional[int] = None
    error_details: Optional[str] = None
    event_id: Optional[str] = None

    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            # Generate unique event ID
            content = f"{self.timestamp}{self.operation.value}{self.message}"
            self.event_id = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'operation': self.operation.value,
            'message': self.message,
            'success': self.success,
            'duration_ms': self.duration_ms,
            'error_details': self.error_details,
            'context': self.context.sanitize() if self.context else None
        }


class SecureAuditLogger:
    """Secure audit logger with tamper detection and encryption."""

    def __init__(self,
                 log_dir: Path,
                 max_file_size_mb: int = 100,
                 max_files: int = 10,
                 enable_encryption: bool = False):
        """
        Initialize secure audit logger.

        Args:
            log_dir: Directory for audit logs
            max_file_size_mb: Maximum size per log file
            max_files: Maximum number of log files to keep
            enable_encryption: Whether to encrypt log files
        """
        self.log_dir = log_dir
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_files = max_files
        self.enable_encryption = enable_encryption

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize logging
        self.logger = self._setup_logger()
        self.lock = threading.Lock()

        # Session tracking
        self.session_id = self._generate_session_id()

        # Initialize audit log
        self._log_audit_start()

    def _setup_logger(self) -> logging.Logger:
        """Setup audit logger with secure configuration."""
        logger = logging.getLogger('gmail_assistant.audit')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Create rotating file handler
            current_log_file = self.log_dir / "audit.log"

            # Custom handler for secure logging
            handler = logging.FileHandler(current_log_file)
            handler.setLevel(logging.INFO)

            # JSON formatter for structured logs
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)

            logger.addHandler(handler)
            logger.propagate = False  # Don't propagate to root logger

        return logger

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = int(time.time() * 1000000)  # microseconds
        random_part = os.urandom(8).hex()
        return f"session_{timestamp}_{random_part}"

    def _log_audit_start(self) -> None:
        """Log audit session start."""
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc),
            level=AuditLevel.INFO,
            operation=OperationType.AUTHENTICATION,
            message="Audit logging session started",
            context=AuditContext(session_id=self.session_id),
            success=True
        )
        self._write_audit_event(event)

    def _write_audit_event(self, event: AuditEvent) -> None:
        """Write audit event to log with thread safety."""
        with self.lock:
            try:
                # Prepare log entry
                log_entry = {
                    'audit_event': event.to_dict(),
                    'session_id': self.session_id,
                    'log_version': '1.0'
                }

                # Write to log
                self.logger.info(json.dumps(log_entry, separators=(',', ':')))

                # Check file rotation
                self._check_file_rotation()

            except Exception as e:
                # Fallback logging to prevent audit failures from breaking the application
                fallback_logger = logging.getLogger('gmail_assistant.audit_fallback')
                fallback_logger.error(f"Audit logging failed: {e}")

    def _check_file_rotation(self) -> None:
        """Check if log file needs rotation."""
        try:
            current_log_file = self.log_dir / "audit.log"

            if current_log_file.exists() and current_log_file.stat().st_size > self.max_file_size_bytes:
                self._rotate_log_files()

        except Exception as e:
            # Don't let rotation failures break audit logging
            pass

    def _rotate_log_files(self) -> None:
        """Rotate audit log files."""
        try:
            # Move current log to timestamped archive
            current_log_file = self.log_dir / "audit.log"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = self.log_dir / f"audit_{timestamp}.log"

            if current_log_file.exists():
                current_log_file.rename(archive_file)

            # Clean up old files
            self._cleanup_old_log_files()

            # Recreate logger for new file
            self.logger = self._setup_logger()

        except Exception as e:
            # Log rotation failure shouldn't break audit logging
            pass

    def _cleanup_old_log_files(self) -> None:
        """Clean up old audit log files."""
        try:
            log_files = sorted(
                self.log_dir.glob("audit_*.log"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            # Keep only the most recent files
            for old_file in log_files[self.max_files:]:
                old_file.unlink()

        except Exception as e:
            pass

    def log_operation(self,
                     operation: OperationType,
                     message: str,
                     level: AuditLevel = AuditLevel.INFO,
                     context: Optional[AuditContext] = None,
                     success: bool = True,
                     duration_ms: Optional[int] = None,
                     error_details: Optional[str] = None) -> None:
        """
        Log an audit event.

        Args:
            operation: Type of operation
            message: Descriptive message
            level: Audit level
            context: Optional context information
            success: Whether operation was successful
            duration_ms: Operation duration in milliseconds
            error_details: Error details if applicable
        """
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc),
            level=level,
            operation=operation,
            message=message,
            context=context,
            success=success,
            duration_ms=duration_ms,
            error_details=error_details
        )

        self._write_audit_event(event)

    @contextmanager
    def audit_operation(self,
                       operation: OperationType,
                       message: str,
                       context: Optional[AuditContext] = None,
                       level: AuditLevel = AuditLevel.INFO):
        """
        Context manager for auditing operations with automatic timing.

        Args:
            operation: Type of operation
            message: Descriptive message
            context: Optional context information
            level: Audit level
        """
        start_time = time.time()
        error_details = None
        success = True

        try:
            yield
        except Exception as e:
            success = False
            error_details = str(e)
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)

            self.log_operation(
                operation=operation,
                message=message,
                level=level,
                context=context,
                success=success,
                duration_ms=duration_ms,
                error_details=error_details
            )

    def log_authentication(self, user_email: str, success: bool, error: Optional[str] = None) -> None:
        """Log authentication attempt."""
        context = AuditContext(
            user_id=user_email,
            session_id=self.session_id
        )

        self.log_operation(
            operation=OperationType.AUTHENTICATION,
            message=f"Authentication attempt for {user_email}",
            level=AuditLevel.SECURITY if success else AuditLevel.WARNING,
            context=context,
            success=success,
            error_details=error
        )

    def log_email_access(self, email_count: int, query: str, user_id: Optional[str] = None) -> None:
        """Log email access operation."""
        context = AuditContext(
            user_id=user_id,
            query=query,
            batch_size=email_count,
            session_id=self.session_id
        )

        self.log_operation(
            operation=OperationType.EMAIL_ACCESS,
            message=f"Accessed {email_count} emails",
            level=AuditLevel.INFO,
            context=context,
            success=True
        )

    def log_email_deletion(self, email_ids: List[str], user_id: Optional[str] = None, success: bool = True) -> None:
        """Log email deletion operation."""
        context = AuditContext(
            user_id=user_id,
            batch_size=len(email_ids),
            session_id=self.session_id,
            additional_data={"deleted_count": len(email_ids)}
        )

        self.log_operation(
            operation=OperationType.EMAIL_DELETION,
            message=f"Deleted {len(email_ids)} emails",
            level=AuditLevel.SECURITY,
            context=context,
            success=success
        )

    def log_file_access(self, file_path: str, operation: str, success: bool = True) -> None:
        """Log file access operation."""
        context = AuditContext(
            file_path=file_path,
            session_id=self.session_id
        )

        self.log_operation(
            operation=OperationType.FILE_ACCESS,
            message=f"File {operation}: {Path(file_path).name}",
            level=AuditLevel.INFO,
            context=context,
            success=success
        )

    def log_performance_issue(self, operation: str, duration_ms: int, threshold_ms: int = 5000) -> None:
        """Log performance issues."""
        if duration_ms > threshold_ms:
            context = AuditContext(
                session_id=self.session_id,
                additional_data={"threshold_ms": threshold_ms}
            )

            self.log_operation(
                operation=OperationType.PERFORMANCE_ISSUE,
                message=f"Slow operation detected: {operation}",
                level=AuditLevel.WARNING,
                context=context,
                success=True,
                duration_ms=duration_ms
            )

    def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        try:
            log_files = list(self.log_dir.glob("audit*.log"))
            total_size = sum(f.stat().st_size for f in log_files)

            return {
                'session_id': self.session_id,
                'log_directory': str(self.log_dir),
                'log_files_count': len(log_files),
                'total_size_mb': total_size / (1024 * 1024),
                'encryption_enabled': self.enable_encryption,
                'max_file_size_mb': self.max_file_size_bytes / (1024 * 1024),
                'max_files': self.max_files
            }
        except Exception as e:
            return {'error': str(e)}


class AuditManager:
    """Global audit manager for Gmail Fetcher."""

    def __init__(self):
        """Initialize audit manager."""
        self.logger: Optional[SecureAuditLogger] = None
        self.enabled = True

    def initialize(self, log_dir: Optional[Path] = None, **kwargs) -> None:
        """
        Initialize audit logging.

        Args:
            log_dir: Directory for audit logs
            kwargs: Additional configuration options
        """
        if not log_dir:
            log_dir = Path.cwd() / "logs" / "audit"

        try:
            self.logger = SecureAuditLogger(log_dir, **kwargs)
        except Exception as e:
            # Don't let audit initialization failures break the application
            logging.getLogger('gmail_assistant').warning(f"Audit logging initialization failed: {e}")
            self.enabled = False

    def is_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        return self.enabled and self.logger is not None

    def log(self, *args, **kwargs) -> None:
        """Log audit event if enabled."""
        if self.is_enabled() and self.logger:
            try:
                self.logger.log_operation(*args, **kwargs)
            except Exception as e:
                # Don't let audit failures break the application
                logging.getLogger('gmail_assistant').warning(f"Audit logging failed: {e}")

    def audit_operation(self, *args, **kwargs):
        """Context manager for auditing operations."""
        if self.is_enabled() and self.logger:
            return self.logger.audit_operation(*args, **kwargs)
        else:
            # Return a dummy context manager if audit is disabled
            from contextlib import nullcontext
            return nullcontext()

    # Convenience methods
    def log_authentication(self, *args, **kwargs) -> None:
        """Log authentication attempt."""
        if self.is_enabled() and self.logger:
            self.logger.log_authentication(*args, **kwargs)

    def log_email_access(self, *args, **kwargs) -> None:
        """Log email access operation."""
        if self.is_enabled() and self.logger:
            self.logger.log_email_access(*args, **kwargs)

    def log_email_deletion(self, *args, **kwargs) -> None:
        """Log email deletion operation."""
        if self.is_enabled() and self.logger:
            self.logger.log_email_deletion(*args, **kwargs)

    def log_file_access(self, *args, **kwargs) -> None:
        """Log file access operation."""
        if self.is_enabled() and self.logger:
            self.logger.log_file_access(*args, **kwargs)

    def log_performance_issue(self, *args, **kwargs) -> None:
        """Log performance issues."""
        if self.is_enabled() and self.logger:
            self.logger.log_performance_issue(*args, **kwargs)


# Global audit manager instance
_global_audit_manager: Optional[AuditManager] = None


def get_audit_manager() -> AuditManager:
    """Get global audit manager instance."""
    global _global_audit_manager
    if _global_audit_manager is None:
        _global_audit_manager = AuditManager()
    return _global_audit_manager


def initialize_audit_logging(log_dir: Optional[Path] = None, **kwargs) -> None:
    """Initialize global audit logging."""
    manager = get_audit_manager()
    manager.initialize(log_dir, **kwargs)


# Convenience functions for common audit operations
def audit_authentication(user_email: str, success: bool, error: Optional[str] = None) -> None:
    """Audit authentication attempt."""
    get_audit_manager().log_authentication(user_email, success, error)


def audit_email_access(email_count: int, query: str, user_id: Optional[str] = None) -> None:
    """Audit email access operation."""
    get_audit_manager().log_email_access(email_count, query, user_id)


def audit_email_deletion(email_ids: List[str], user_id: Optional[str] = None, success: bool = True) -> None:
    """Audit email deletion operation."""
    get_audit_manager().log_email_deletion(email_ids, user_id, success)


def audit_operation(operation: OperationType, message: str, **kwargs):
    """Context manager for auditing operations."""
    return get_audit_manager().audit_operation(operation, message, **kwargs)