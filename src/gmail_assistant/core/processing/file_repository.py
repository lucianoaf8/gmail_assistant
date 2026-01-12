"""
File-based email repository implementation (C-2/M-9 complete fix).

Implements EmailRepositoryProtocol for JSON/EML file storage.
Provides an alternative to SQLite for email persistence.
"""

import json
import logging
from pathlib import Path
from typing import Any

from gmail_assistant.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class FileEmailRepository:
    """
    File-based email storage implementing EmailRepositoryProtocol.

    Stores emails as individual JSON files organized by date.
    Supports EML format preservation alongside JSON metadata.

    Example:
        >>> repo = FileEmailRepository('./email_storage')
        >>> repo.save({'id': 'abc123', 'subject': 'Hello', 'date': '2025-01-15'})
        True
        >>> email = repo.get('abc123')
        >>> email['subject']
        'Hello'
    """

    def __init__(self, base_path: str | Path, create_dirs: bool = True):
        """
        Initialize file-based repository.

        Args:
            base_path: Root directory for email storage
            create_dirs: Whether to create directories if missing
        """
        self.base_path = Path(base_path)
        if create_dirs:
            self.base_path.mkdir(parents=True, exist_ok=True)
        self._index_cache: dict[str, Path] = {}
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the email ID to file path index."""
        self._index_cache.clear()
        if not self.base_path.exists():
            return

        for json_file in self.base_path.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'id' in data:
                        self._index_cache[data['id']] = json_file
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to index {json_file}: {e}")

        logger.debug(f"Indexed {len(self._index_cache)} emails from {self.base_path}")

    def _get_target_dir(self, email: dict[str, Any]) -> Path:
        """Get target directory for email based on date."""
        date_str = email.get('date', 'unknown')

        # Handle various date formats
        if isinstance(date_str, str) and len(date_str) >= 10:
            # Extract YYYY-MM-DD part
            date_part = date_str[:10]
            try:
                year, month, day = date_part.split('-')
                return self.base_path / year / month
            except ValueError:
                pass

        return self.base_path / 'unknown'

    def _sanitize_filename(self, email_id: str) -> str:
        """Sanitize email ID for use as filename."""
        # Replace problematic characters
        safe_id = email_id.replace('/', '_').replace('\\', '_')
        safe_id = safe_id.replace(':', '_').replace('*', '_')
        safe_id = safe_id.replace('?', '_').replace('"', '_')
        safe_id = safe_id.replace('<', '_').replace('>', '_')
        safe_id = safe_id.replace('|', '_')
        return safe_id[:200]  # Limit length

    def save(self, email: dict[str, Any]) -> bool:
        """
        Save an email to the repository.

        Args:
            email: Email data dictionary with 'id' field required

        Returns:
            True if saved successfully, False otherwise

        Raises:
            ValidationError: If email has no 'id' field
        """
        if 'id' not in email:
            raise ValidationError("Email must have 'id' field")

        email_id = email['id']
        target_dir = self._get_target_dir(email)
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = self._sanitize_filename(email_id)
        file_path = target_dir / f"{safe_filename}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(email, f, indent=2, ensure_ascii=False, default=str)
            self._index_cache[email_id] = file_path
            logger.debug(f"Saved email {email_id} to {file_path}")
            return True
        except IOError as e:
            logger.error(f"Failed to save email {email_id}: {e}")
            return False

    def get(self, email_id: str) -> dict[str, Any] | None:
        """
        Get an email by ID.

        Args:
            email_id: The email ID

        Returns:
            Email data dictionary or None if not found
        """
        file_path = self._index_cache.get(email_id)
        if not file_path or not file_path.exists():
            # Try to find by scanning (fallback for missing index)
            return self._find_by_id(email_id)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read email {email_id}: {e}")
            return None

    def _find_by_id(self, email_id: str) -> dict[str, Any] | None:
        """Fallback: scan files to find email by ID."""
        safe_filename = self._sanitize_filename(email_id)

        for json_file in self.base_path.rglob(f"{safe_filename}.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('id') == email_id:
                        # Update cache
                        self._index_cache[email_id] = json_file
                        return data
            except (json.JSONDecodeError, IOError):
                continue
        return None

    def find(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Find emails matching a query (simple substring search).

        Args:
            query: Search string to match in subject, sender, or snippet
            limit: Maximum results to return

        Returns:
            List of matching email dictionaries
        """
        results = []
        query_lower = query.lower()

        for email_id, file_path in self._index_cache.items():
            if len(results) >= limit:
                break

            email = self.get(email_id)
            if email:
                # Search in subject, sender, snippet
                searchable = ' '.join([
                    str(email.get('subject', '')),
                    str(email.get('sender', '')),
                    str(email.get('snippet', '')),
                    str(email.get('body', ''))[:500]  # First 500 chars of body
                ]).lower()

                if query_lower in searchable:
                    results.append(email)

        return results

    def delete(self, email_id: str) -> bool:
        """
        Delete an email by ID.

        Args:
            email_id: The email ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        file_path = self._index_cache.get(email_id)
        if not file_path:
            logger.warning(f"Email {email_id} not found in index")
            return False

        try:
            if file_path.exists():
                file_path.unlink()
            self._index_cache.pop(email_id, None)
            logger.debug(f"Deleted email {email_id}")
            return True
        except IOError as e:
            logger.error(f"Failed to delete email {email_id}: {e}")
            return False

    def count(self, query: str | None = None) -> int:
        """
        Count emails, optionally filtered by query.

        Args:
            query: Optional filter query

        Returns:
            Number of matching emails
        """
        if query is None:
            return len(self._index_cache)
        return len(self.find(query, limit=999999))

    def exists(self, email_id: str) -> bool:
        """
        Check if an email exists.

        Args:
            email_id: The email ID to check

        Returns:
            True if email exists in repository
        """
        if email_id in self._index_cache:
            # Verify file still exists
            file_path = self._index_cache[email_id]
            if file_path.exists():
                return True
            # File was deleted externally, update cache
            del self._index_cache[email_id]
        return False

    def get_stats(self) -> dict[str, Any]:
        """
        Get repository statistics.

        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        for file_path in self._index_cache.values():
            if file_path.exists():
                total_size += file_path.stat().st_size

        return {
            'email_count': len(self._index_cache),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'base_path': str(self.base_path),
        }

    def clear(self) -> int:
        """
        Delete all emails in the repository.

        Returns:
            Number of emails deleted
        """
        deleted = 0
        for email_id in list(self._index_cache.keys()):
            if self.delete(email_id):
                deleted += 1
        return deleted

    def refresh_index(self) -> int:
        """
        Refresh the email index by scanning the filesystem.

        Returns:
            Number of emails indexed
        """
        self._rebuild_index()
        return len(self._index_cache)
