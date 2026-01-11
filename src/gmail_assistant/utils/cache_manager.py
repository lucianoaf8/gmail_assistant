"""
Intelligent caching system for Gmail Fetcher.
Provides memory-efficient caching with automatic cleanup and persistence.
"""

import hashlib
import json
import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .memory_manager import MemoryOptimizedCache, MemoryTracker

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: float | None = None
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'key': self.key,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'ttl': self.ttl,
            'size_bytes': self.size_bytes
        }


class IntelligentCache:
    """
    Intelligent caching system with multiple storage layers and automatic optimization.
    """

    def __init__(self,
                 memory_limit_mb: int = 100,
                 disk_cache_dir: Path | None = None,
                 default_ttl: int = 3600,
                 enable_persistence: bool = True):
        """
        Initialize intelligent cache.

        Args:
            memory_limit_mb: Memory limit for in-memory cache
            disk_cache_dir: Directory for disk cache (None for temp)
            default_ttl: Default time-to-live in seconds
            enable_persistence: Whether to enable disk persistence
        """
        self.memory_cache = MemoryOptimizedCache(max_size=1000, memory_limit_mb=memory_limit_mb)
        self.memory_tracker = MemoryTracker()
        self.default_ttl = default_ttl
        self.enable_persistence = enable_persistence

        # Disk cache setup
        if disk_cache_dir:
            self.disk_cache_dir = disk_cache_dir
        else:
            self.disk_cache_dir = Path.home() / '.gmail_assistant_cache'

        self.disk_cache_dir.mkdir(exist_ok=True)

        # Cache metadata
        self.metadata: dict[str, CacheEntry] = {}
        self.lock = threading.RLock()

        # Load existing metadata
        self._load_metadata()

        # Cleanup expired entries
        self._cleanup_expired()

    def _get_cache_key(self, key: str) -> str:
        """Generate consistent cache key."""
        if isinstance(key, str) and len(key) < 100:
            return key

        # Hash long keys
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _get_disk_path(self, cache_key: str) -> Path:
        """Get disk cache file path."""
        return self.disk_cache_dir / f"{cache_key}.cache"

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, (dict, list)):
                return len(json.dumps(value, default=str).encode())
            else:
                # For other types, try JSON serialization
                return len(json.dumps(value, default=str).encode())
        except Exception as e:
            logger.debug(f"Could not estimate size for value: {e}")
            return 1024  # Default estimate

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache with intelligent fallback.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        cache_key = self._get_cache_key(key)

        with self.lock:
            # Check memory cache first
            value = self.memory_cache.get(cache_key)
            if value is not None:
                self._update_access_metadata(cache_key)
                return value

            # Check disk cache
            if self.enable_persistence:
                value = self._load_from_disk(cache_key)
                if value is not None:
                    # Promote to memory cache
                    self.memory_cache.put(cache_key, value)
                    self._update_access_metadata(cache_key)
                    return value

            return default

    def put(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Store value in cache with intelligent placement.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds (None for default)

        Returns:
            True if stored successfully
        """
        cache_key = self._get_cache_key(key)
        ttl = ttl or self.default_ttl

        with self.lock:
            try:
                # Create cache entry
                now = time.time()
                size_bytes = self._estimate_size(value)

                entry = CacheEntry(
                    key=cache_key,
                    value=value,
                    created_at=now,
                    last_accessed=now,
                    access_count=0,
                    ttl=ttl,
                    size_bytes=size_bytes
                )

                # Store in memory cache
                self.memory_cache.put(cache_key, value)

                # Store metadata
                self.metadata[cache_key] = entry

                # Persist to disk if enabled and valuable
                if self.enable_persistence and self._should_persist(entry):
                    self._save_to_disk(cache_key, value)

                self._save_metadata()
                return True

            except Exception as e:
                logger.error(f"Error storing cache entry {cache_key}: {e}")
                return False

    def _should_persist(self, entry: CacheEntry) -> bool:
        """Determine if entry should be persisted to disk."""
        # Persist if:
        # - Entry is larger than 1KB (potentially expensive to recompute)
        # - TTL is longer than 1 hour (long-lived data)
        # - Memory pressure is high

        if entry.size_bytes > 1024:
            return True

        if entry.ttl and entry.ttl > 3600:
            return True

        memory_status = self.memory_tracker.check_memory()
        if memory_status['status'] in ['warning', 'critical']:
            return True

        return False

    def _load_from_disk(self, cache_key: str) -> Any:
        """Load value from disk cache using JSON for security."""
        try:
            disk_path = self._get_disk_path(cache_key)
            if not disk_path.exists():
                return None

            # Check if entry is expired
            if cache_key in self.metadata:
                entry = self.metadata[cache_key]
                if entry.is_expired():
                    disk_path.unlink(missing_ok=True)
                    del self.metadata[cache_key]
                    return None

            # Load value using JSON (secure deserialization)
            with open(disk_path, encoding='utf-8') as f:
                return json.load(f)

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in cache file {cache_key}, removing: {e}")
            disk_path.unlink(missing_ok=True)
            return None
        except Exception as e:
            logger.error(f"Error loading from disk cache {cache_key}: {e}")
            return None

    def _save_to_disk(self, cache_key: str, value: Any) -> bool:
        """Save value to disk cache using JSON for security."""
        try:
            disk_path = self._get_disk_path(cache_key)
            with open(disk_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, default=str, indent=2)
            return True

        except (TypeError, ValueError) as e:
            logger.warning(f"Value not JSON serializable for cache {cache_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saving to disk cache {cache_key}: {e}")
            return False

    def _update_access_metadata(self, cache_key: str) -> None:
        """Update access metadata for cache entry."""
        if cache_key in self.metadata:
            entry = self.metadata[cache_key]
            entry.last_accessed = time.time()
            entry.access_count += 1

    def _load_metadata(self) -> None:
        """Load cache metadata from disk."""
        try:
            metadata_path = self.disk_cache_dir / 'metadata.json'
            if metadata_path.exists():
                with open(metadata_path) as f:
                    data = json.load(f)

                # Reconstruct metadata
                for key, entry_data in data.items():
                    entry = CacheEntry(
                        key=entry_data['key'],
                        value=None,  # Value loaded separately
                        created_at=entry_data['created_at'],
                        last_accessed=entry_data['last_accessed'],
                        access_count=entry_data['access_count'],
                        ttl=entry_data.get('ttl'),
                        size_bytes=entry_data.get('size_bytes', 0)
                    )
                    self.metadata[key] = entry

        except Exception as e:
            logger.error(f"Error loading cache metadata: {e}")

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        try:
            metadata_path = self.disk_cache_dir / 'metadata.json'
            data = {key: entry.to_dict() for key, entry in self.metadata.items()}

            with open(metadata_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")

    def _cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        expired_keys = []

        with self.lock:
            for key, entry in self.metadata.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                # Remove from memory cache
                if key in self.memory_cache.cache:
                    del self.memory_cache.cache[key]

                # Remove from disk
                disk_path = self._get_disk_path(key)
                disk_path.unlink(missing_ok=True)

                # Remove metadata
                del self.metadata[key]

            if expired_keys:
                self._save_metadata()
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def invalidate(self, key: str) -> bool:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was found and removed
        """
        cache_key = self._get_cache_key(key)

        with self.lock:
            found = False

            # Remove from memory cache
            if cache_key in self.memory_cache.cache:
                del self.memory_cache.cache[key]
                found = True

            # Remove from disk
            disk_path = self._get_disk_path(cache_key)
            if disk_path.exists():
                disk_path.unlink()
                found = True

            # Remove metadata
            if cache_key in self.metadata:
                del self.metadata[cache_key]
                found = True

            if found:
                self._save_metadata()

            return found

    def clear(self) -> None:
        """Clear entire cache."""
        with self.lock:
            # Clear memory cache
            self.memory_cache.clear()

            # Clear disk cache
            if self.enable_persistence:
                for cache_file in self.disk_cache_dir.glob('*.cache'):
                    cache_file.unlink()

            # Clear metadata
            self.metadata.clear()
            self._save_metadata()

            logger.info("Cache cleared completely")

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self.lock:
            memory_stats = self.memory_cache.get_stats()

            # Calculate disk usage
            disk_files = list(self.disk_cache_dir.glob('*.cache'))
            disk_size_mb = sum(f.stat().st_size for f in disk_files) / (1024 * 1024)

            # Calculate hit/miss ratios
            total_entries = len(self.metadata)
            total_accesses = sum(entry.access_count for entry in self.metadata.values())

            return {
                'memory_cache': memory_stats,
                'disk_cache': {
                    'files': len(disk_files),
                    'size_mb': disk_size_mb,
                    'directory': str(self.disk_cache_dir)
                },
                'total_entries': total_entries,
                'total_accesses': total_accesses,
                'average_accesses': total_accesses / max(total_entries, 1),
                'expired_cleanup_available': len([e for e in self.metadata.values() if e.is_expired()])
            }

    @contextmanager
    def batch_operations(self):
        """Context manager for batch cache operations."""
        with self.lock:
            yield self

    def optimize(self) -> dict[str, int]:
        """
        Optimize cache by cleaning up expired entries and managing memory.

        Returns:
            Dictionary with optimization statistics
        """
        stats = {
            'expired_removed': 0,
            'memory_freed_mb': 0,
            'disk_freed_mb': 0
        }

        # Clean up expired entries
        stats['expired_removed'] = self._cleanup_expired()

        # Force memory cleanup
        before_memory = self.memory_tracker.check_memory()['current_mb']
        freed_bytes = self.memory_tracker.force_gc()
        after_memory = self.memory_tracker.check_memory()['current_mb']
        stats['memory_freed_mb'] = max(0, before_memory - after_memory)

        # Clean up least recently used disk entries if disk usage is high
        disk_stats = self.get_stats()['disk_cache']
        if disk_stats['size_mb'] > 500:  # If disk cache > 500MB
            stats['disk_freed_mb'] = self._cleanup_lru_disk_entries()

        logger.info(f"Cache optimization: {stats}")
        return stats

    def _cleanup_lru_disk_entries(self, target_mb: int = 250) -> float:
        """Clean up least recently used disk entries."""
        freed_mb = 0.0

        # Sort entries by last access time
        sorted_entries = sorted(
            self.metadata.items(),
            key=lambda x: x[1].last_accessed
        )

        current_disk_mb = self.get_stats()['disk_cache']['size_mb']

        for key, entry in sorted_entries:
            if current_disk_mb <= target_mb:
                break

            disk_path = self._get_disk_path(key)
            if disk_path.exists():
                size_mb = disk_path.stat().st_size / (1024 * 1024)
                disk_path.unlink()
                freed_mb += size_mb
                current_disk_mb -= size_mb

                # Remove from metadata but keep in memory if present
                del self.metadata[key]

        if freed_mb > 0:
            self._save_metadata()
            logger.info(f"Freed {freed_mb:.1f} MB from disk cache")

        return freed_mb


class CacheManager:
    """
    Global cache manager for Gmail Fetcher operations.
    """

    def __init__(self):
        """Initialize cache manager with specialized caches."""

        # Email metadata cache (small, frequently accessed)
        self.metadata_cache = IntelligentCache(
            memory_limit_mb=50,
            default_ttl=7200,  # 2 hours
            enable_persistence=True
        )

        # Email content cache (large, less frequently accessed)
        self.content_cache = IntelligentCache(
            memory_limit_mb=200,
            default_ttl=86400,  # 24 hours
            enable_persistence=True
        )

        # Query results cache (medium, variable access)
        self.query_cache = IntelligentCache(
            memory_limit_mb=100,
            default_ttl=3600,  # 1 hour
            enable_persistence=True
        )

        # Profile and settings cache (tiny, long-lived)
        self.profile_cache = IntelligentCache(
            memory_limit_mb=10,
            default_ttl=86400,  # 24 hours
            enable_persistence=True
        )

    def cache_email_metadata(self, email_id: str, metadata: dict[str, Any]) -> None:
        """Cache email metadata."""
        self.metadata_cache.put(f"metadata:{email_id}", metadata, ttl=7200)

    def get_email_metadata(self, email_id: str) -> dict[str, Any] | None:
        """Get cached email metadata."""
        return self.metadata_cache.get(f"metadata:{email_id}")

    def cache_email_content(self, email_id: str, content: str) -> None:
        """Cache email content."""
        self.content_cache.put(f"content:{email_id}", content, ttl=86400)

    def get_email_content(self, email_id: str) -> str | None:
        """Get cached email content."""
        return self.content_cache.get(f"content:{email_id}")

    def cache_query_results(self, query: str, results: list[str]) -> None:
        """Cache query results."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        self.query_cache.put(f"query:{query_hash}", results, ttl=3600)

    def get_query_results(self, query: str) -> list[str] | None:
        """Get cached query results."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return self.query_cache.get(f"query:{query_hash}")

    def cache_profile(self, profile: dict[str, Any]) -> None:
        """Cache Gmail profile."""
        self.profile_cache.put("gmail_profile", profile, ttl=86400)

    def get_profile(self) -> dict[str, Any] | None:
        """Get cached Gmail profile."""
        return self.profile_cache.get("gmail_profile")

    def invalidate_email(self, email_id: str) -> None:
        """Invalidate all cached data for an email."""
        self.metadata_cache.invalidate(f"metadata:{email_id}")
        self.content_cache.invalidate(f"content:{email_id}")

    def clear_all(self) -> None:
        """Clear all caches."""
        self.metadata_cache.clear()
        self.content_cache.clear()
        self.query_cache.clear()
        self.profile_cache.clear()

    def get_global_stats(self) -> dict[str, Any]:
        """Get statistics for all caches."""
        return {
            'metadata_cache': self.metadata_cache.get_stats(),
            'content_cache': self.content_cache.get_stats(),
            'query_cache': self.query_cache.get_stats(),
            'profile_cache': self.profile_cache.get_stats()
        }

    def optimize_all(self) -> dict[str, Any]:
        """Optimize all caches."""
        return {
            'metadata_cache': self.metadata_cache.optimize(),
            'content_cache': self.content_cache.optimize(),
            'query_cache': self.query_cache.optimize(),
            'profile_cache': self.profile_cache.optimize()
        }
