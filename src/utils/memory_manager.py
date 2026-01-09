"""
Memory optimization utilities for Gmail Fetcher.
Implements streaming and progressive loading for large datasets.
"""

import gc
import logging
import sys
from typing import Iterator, Dict, Any, Optional, List
from pathlib import Path
import tempfile
import json
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MemoryTracker:
    """Track memory usage and provide optimization recommendations."""

    def __init__(self):
        self.initial_memory = self._get_memory_usage()
        self.peak_memory = self.initial_memory
        self.threshold_warning = 500 * 1024 * 1024  # 500MB
        self.threshold_critical = 1024 * 1024 * 1024  # 1GB

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # Fallback to sys.getsizeof for approximate usage
            return sys.getsizeof(gc.get_objects())

    def check_memory(self) -> Dict[str, Any]:
        """
        Check current memory usage and return status.

        Returns:
            Dictionary with memory status and recommendations
        """
        current_memory = self._get_memory_usage()
        self.peak_memory = max(self.peak_memory, current_memory)

        memory_used = current_memory - self.initial_memory

        status = {
            'current_mb': current_memory / (1024 * 1024),
            'used_mb': memory_used / (1024 * 1024),
            'peak_mb': self.peak_memory / (1024 * 1024),
            'status': 'normal'
        }

        if current_memory > self.threshold_critical:
            status['status'] = 'critical'
            status['recommendation'] = 'Enable streaming mode, reduce batch size'
        elif current_memory > self.threshold_warning:
            status['status'] = 'warning'
            status['recommendation'] = 'Consider streaming for large operations'

        return status

    def force_gc(self) -> int:
        """Force garbage collection and return freed bytes."""
        before = self._get_memory_usage()
        gc.collect()
        after = self._get_memory_usage()
        freed = max(0, before - after)

        if freed > 0:
            logger.info(f"Garbage collection freed {freed / (1024 * 1024):.1f} MB")

        return freed


class StreamingEmailProcessor:
    """Process emails in streaming fashion to minimize memory usage."""

    def __init__(self, temp_dir: Optional[Path] = None, chunk_size: int = 100):
        """
        Initialize streaming processor.

        Args:
            temp_dir: Directory for temporary files
            chunk_size: Number of emails to process in each chunk
        """
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "gmail_assistant"
        self.temp_dir.mkdir(exist_ok=True)
        self.chunk_size = chunk_size
        self.memory_tracker = MemoryTracker()

    def process_emails_streaming(self, email_generator: Iterator[Dict[str, Any]],
                                processor_func: callable) -> Iterator[Dict[str, Any]]:
        """
        Process emails in streaming fashion.

        Args:
            email_generator: Generator yielding email data
            processor_func: Function to process each email

        Yields:
            Processed email results
        """
        chunk = []
        processed_count = 0

        for email_data in email_generator:
            chunk.append(email_data)

            if len(chunk) >= self.chunk_size:
                # Process chunk and yield results
                yield from self._process_chunk(chunk, processor_func)
                processed_count += len(chunk)

                # Clear chunk and check memory
                chunk.clear()
                self._check_memory_and_optimize(processed_count)

        # Process remaining emails
        if chunk:
            yield from self._process_chunk(chunk, processor_func)

    def _process_chunk(self, chunk: List[Dict[str, Any]],
                      processor_func: callable) -> Iterator[Dict[str, Any]]:
        """Process a chunk of emails."""
        for email_data in chunk:
            try:
                result = processor_func(email_data)
                yield result
            except Exception as e:
                logger.error(f"Error processing email: {e}")
                yield {"error": str(e), "email_id": email_data.get("id")}

    def _check_memory_and_optimize(self, processed_count: int) -> None:
        """Check memory usage and optimize if needed."""
        memory_status = self.memory_tracker.check_memory()

        if memory_status['status'] == 'critical':
            logger.warning(f"Critical memory usage: {memory_status['current_mb']:.1f} MB")
            self.memory_tracker.force_gc()
        elif memory_status['status'] == 'warning':
            logger.info(f"High memory usage: {memory_status['current_mb']:.1f} MB after {processed_count} emails")

    @contextmanager
    def temp_file_storage(self, prefix: str = "gmail_data"):
        """Context manager for temporary file storage."""
        temp_file = self.temp_dir / f"{prefix}_{id(self)}.tmp"
        try:
            yield temp_file
        finally:
            if temp_file.exists():
                temp_file.unlink()


class ProgressiveLoader:
    """Load large datasets progressively to avoid memory issues."""

    def __init__(self, batch_size: int = 1000):
        """
        Initialize progressive loader.

        Args:
            batch_size: Size of each batch to load
        """
        self.batch_size = batch_size
        self.memory_tracker = MemoryTracker()

    def load_emails_progressive(self, email_ids: List[str],
                               fetch_func: callable) -> Iterator[Dict[str, Any]]:
        """
        Load emails progressively in batches.

        Args:
            email_ids: List of email IDs to fetch
            fetch_func: Function to fetch email data by ID

        Yields:
            Email data dictionaries
        """
        total_emails = len(email_ids)
        processed = 0

        for i in range(0, total_emails, self.batch_size):
            batch_ids = email_ids[i:i + self.batch_size]

            logger.info(f"Loading batch {i//self.batch_size + 1}: "
                       f"emails {i+1}-{min(i+self.batch_size, total_emails)} of {total_emails}")

            # Fetch batch
            batch_data = []
            for email_id in batch_ids:
                try:
                    email_data = fetch_func(email_id)
                    batch_data.append(email_data)
                except Exception as e:
                    logger.error(f"Failed to fetch email {email_id}: {e}")
                    continue

            # Yield emails from batch
            for email_data in batch_data:
                yield email_data

            processed += len(batch_data)

            # Check memory and optimize
            memory_status = self.memory_tracker.check_memory()
            if memory_status['status'] in ['warning', 'critical']:
                logger.info(f"Memory optimization after {processed} emails: "
                           f"{memory_status['current_mb']:.1f} MB")
                self.memory_tracker.force_gc()

            # Clear batch data
            batch_data.clear()


class EmailContentStreamer:
    """Stream email content to avoid loading large emails into memory."""

    def __init__(self, chunk_size: int = 8192):
        """
        Initialize content streamer.

        Args:
            chunk_size: Size of chunks to read/write
        """
        self.chunk_size = chunk_size

    def stream_to_file(self, content: str, output_path: Path) -> bool:
        """
        Stream content to file in chunks.

        Args:
            content: Content to write
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write content in chunks
                for i in range(0, len(content), self.chunk_size):
                    chunk = content[i:i + self.chunk_size]
                    f.write(chunk)

                    # Periodically check memory
                    if i % (self.chunk_size * 10) == 0:
                        gc.collect()

            return True

        except Exception as e:
            logger.error(f"Failed to stream content to {output_path}: {e}")
            return False

    def stream_from_file(self, file_path: Path) -> Iterator[str]:
        """
        Stream content from file in chunks.

        Args:
            file_path: File to read from

        Yields:
            Content chunks
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk

        except Exception as e:
            logger.error(f"Failed to stream from {file_path}: {e}")
            yield ""


class MemoryOptimizedCache:
    """Memory-conscious cache with automatic cleanup."""

    def __init__(self, max_size: int = 100, memory_limit_mb: int = 200):
        """
        Initialize memory-optimized cache.

        Args:
            max_size: Maximum number of items in cache
            memory_limit_mb: Memory limit in MB
        """
        self.max_size = max_size
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.cache: Dict[str, Any] = {}
        self.access_order: List[str] = []
        self.memory_tracker = MemoryTracker()

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        """Put item in cache with memory checking."""
        # Check memory usage before adding
        memory_status = self.memory_tracker.check_memory()
        if memory_status['status'] == 'critical':
            self._cleanup_cache()

        # Remove existing key if present
        if key in self.cache:
            self.access_order.remove(key)
            del self.cache[key]

        # Add new item
        self.cache[key] = value
        self.access_order.append(key)

        # Cleanup if needed
        self._enforce_limits()

    def _enforce_limits(self) -> None:
        """Enforce cache size and memory limits."""
        # Remove oldest items if over size limit
        while len(self.cache) > self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]

        # Check memory limit
        memory_status = self.memory_tracker.check_memory()
        if memory_status['current_mb'] * 1024 * 1024 > self.memory_limit_bytes:
            self._cleanup_cache()

    def _cleanup_cache(self) -> None:
        """Aggressively clean up cache to free memory."""
        # Remove half the cache, starting with oldest
        cleanup_count = len(self.cache) // 2
        for _ in range(cleanup_count):
            if self.access_order:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]

        # Force garbage collection
        self.memory_tracker.force_gc()
        logger.info(f"Cache cleanup: removed {cleanup_count} items")

    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
        self.access_order.clear()
        self.memory_tracker.force_gc()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'memory_mb': self.memory_tracker.check_memory()['current_mb'],
            'memory_limit_mb': self.memory_limit_bytes / (1024 * 1024)
        }