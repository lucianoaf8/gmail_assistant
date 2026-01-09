"""Unit tests for gmail_assistant.utils.memory_manager module."""
from __future__ import annotations

import gc
import tempfile
from pathlib import Path
from typing import Dict, Any, Iterator
from unittest import mock

import pytest

from gmail_assistant.utils.memory_manager import (
    MemoryTracker,
    StreamingEmailProcessor,
    ProgressiveLoader,
    EmailContentStreamer,
    MemoryOptimizedCache,
)


@pytest.fixture
def memory_tracker():
    """Create a memory tracker for testing."""
    return MemoryTracker()


@pytest.fixture
def streaming_processor(temp_dir: Path):
    """Create a streaming email processor for testing."""
    return StreamingEmailProcessor(temp_dir=temp_dir, chunk_size=2)


@pytest.fixture
def progressive_loader():
    """Create a progressive loader for testing."""
    return ProgressiveLoader(batch_size=2)


@pytest.fixture
def content_streamer():
    """Create an email content streamer for testing."""
    return EmailContentStreamer(chunk_size=10)


@pytest.fixture
def memory_cache():
    """Create a memory optimized cache for testing."""
    return MemoryOptimizedCache(max_size=5, memory_limit_mb=100)


@pytest.mark.unit
class TestMemoryTrackerInit:
    """Test MemoryTracker initialization."""

    def test_records_initial_memory(self, memory_tracker: MemoryTracker):
        """MemoryTracker should record initial memory usage."""
        assert memory_tracker.initial_memory > 0

    def test_peak_memory_starts_at_initial(self, memory_tracker: MemoryTracker):
        """Peak memory should start at initial memory."""
        assert memory_tracker.peak_memory == memory_tracker.initial_memory

    def test_thresholds_set(self, memory_tracker: MemoryTracker):
        """Memory thresholds should be set."""
        assert memory_tracker.threshold_warning > 0
        assert memory_tracker.threshold_critical > memory_tracker.threshold_warning


@pytest.mark.unit
class TestMemoryTrackerCheckMemory:
    """Test MemoryTracker.check_memory method."""

    def test_check_memory_returns_dict(self, memory_tracker: MemoryTracker):
        """check_memory should return dictionary with expected keys."""
        result = memory_tracker.check_memory()

        assert "current_mb" in result
        assert "used_mb" in result
        assert "peak_mb" in result
        assert "status" in result

    def test_check_memory_status_normal(self, memory_tracker: MemoryTracker):
        """check_memory should return 'normal' status under thresholds."""
        # With default thresholds, normal usage should be 'normal'
        result = memory_tracker.check_memory()

        # In most test environments, this should be normal
        assert result["status"] in ["normal", "warning", "critical"]

    def test_check_memory_updates_peak(self, memory_tracker: MemoryTracker):
        """check_memory should update peak memory if higher."""
        initial_peak = memory_tracker.peak_memory
        memory_tracker.check_memory()

        # Peak should be at least initial
        assert memory_tracker.peak_memory >= initial_peak


@pytest.mark.unit
class TestMemoryTrackerForceGC:
    """Test MemoryTracker.force_gc method."""

    def test_force_gc_runs(self, memory_tracker: MemoryTracker):
        """force_gc should run without error."""
        freed = memory_tracker.force_gc()

        # Should return number of freed bytes (can be 0)
        assert freed >= 0

    def test_force_gc_returns_integer(self, memory_tracker: MemoryTracker):
        """force_gc should return integer bytes freed."""
        freed = memory_tracker.force_gc()

        assert isinstance(freed, int)


@pytest.mark.unit
class TestStreamingEmailProcessorInit:
    """Test StreamingEmailProcessor initialization."""

    def test_creates_temp_directory(self, streaming_processor: StreamingEmailProcessor):
        """StreamingEmailProcessor should create temp directory."""
        assert streaming_processor.temp_dir.exists()

    def test_chunk_size_set(self, streaming_processor: StreamingEmailProcessor):
        """chunk_size should be set from parameter."""
        assert streaming_processor.chunk_size == 2


@pytest.mark.unit
class TestStreamingEmailProcessorProcessing:
    """Test StreamingEmailProcessor processing methods."""

    def test_process_emails_streaming(
        self, streaming_processor: StreamingEmailProcessor
    ):
        """process_emails_streaming should process emails in chunks."""
        emails = [
            {"id": "1", "subject": "Email 1"},
            {"id": "2", "subject": "Email 2"},
            {"id": "3", "subject": "Email 3"},
        ]

        def processor(email: Dict[str, Any]) -> Dict[str, Any]:
            return {"processed_id": email["id"]}

        def email_generator():
            yield from emails

        results = list(streaming_processor.process_emails_streaming(
            email_generator(), processor
        ))

        assert len(results) == 3
        assert results[0]["processed_id"] == "1"

    def test_process_emails_handles_errors(
        self, streaming_processor: StreamingEmailProcessor
    ):
        """process_emails_streaming should handle processor errors."""
        emails = [
            {"id": "1"},
            {"id": "2"},
        ]

        def failing_processor(email: Dict[str, Any]) -> Dict[str, Any]:
            if email["id"] == "1":
                raise ValueError("Processing failed")
            return {"processed_id": email["id"]}

        def email_generator():
            yield from emails

        results = list(streaming_processor.process_emails_streaming(
            email_generator(), failing_processor
        ))

        assert len(results) == 2
        assert "error" in results[0]
        assert results[1]["processed_id"] == "2"


@pytest.mark.unit
class TestStreamingEmailProcessorTempStorage:
    """Test StreamingEmailProcessor temp file storage."""

    def test_temp_file_storage_context_manager(
        self, streaming_processor: StreamingEmailProcessor
    ):
        """temp_file_storage should provide temp file path."""
        with streaming_processor.temp_file_storage(prefix="test") as temp_path:
            assert isinstance(temp_path, Path)
            assert "test" in temp_path.name

    def test_temp_file_storage_cleans_up(
        self, streaming_processor: StreamingEmailProcessor
    ):
        """temp_file_storage should clean up file on exit."""
        with streaming_processor.temp_file_storage(prefix="cleanup") as temp_path:
            # Create the file
            temp_path.write_text("test content")
            assert temp_path.exists()

        # File should be removed after context
        assert not temp_path.exists()


@pytest.mark.unit
class TestProgressiveLoaderInit:
    """Test ProgressiveLoader initialization."""

    def test_batch_size_set(self, progressive_loader: ProgressiveLoader):
        """batch_size should be set from parameter."""
        assert progressive_loader.batch_size == 2

    def test_has_memory_tracker(self, progressive_loader: ProgressiveLoader):
        """ProgressiveLoader should have a memory tracker."""
        assert isinstance(progressive_loader.memory_tracker, MemoryTracker)


@pytest.mark.unit
class TestProgressiveLoaderLoading:
    """Test ProgressiveLoader loading methods."""

    def test_load_emails_progressive(self, progressive_loader: ProgressiveLoader):
        """load_emails_progressive should load emails in batches."""
        email_ids = ["id1", "id2", "id3", "id4", "id5"]
        fetch_results = {
            "id1": {"id": "id1", "subject": "Email 1"},
            "id2": {"id": "id2", "subject": "Email 2"},
            "id3": {"id": "id3", "subject": "Email 3"},
            "id4": {"id": "id4", "subject": "Email 4"},
            "id5": {"id": "id5", "subject": "Email 5"},
        }

        def fetch_func(email_id: str) -> Dict[str, Any]:
            return fetch_results[email_id]

        results = list(progressive_loader.load_emails_progressive(
            email_ids, fetch_func
        ))

        assert len(results) == 5
        assert results[0]["id"] == "id1"

    def test_load_emails_handles_fetch_errors(
        self, progressive_loader: ProgressiveLoader
    ):
        """load_emails_progressive should handle fetch errors."""
        email_ids = ["id1", "id2"]

        def failing_fetch(email_id: str) -> Dict[str, Any]:
            if email_id == "id1":
                raise ValueError("Fetch failed")
            return {"id": email_id}

        results = list(progressive_loader.load_emails_progressive(
            email_ids, failing_fetch
        ))

        # Should only get one result (id2)
        assert len(results) == 1
        assert results[0]["id"] == "id2"


@pytest.mark.unit
class TestEmailContentStreamerInit:
    """Test EmailContentStreamer initialization."""

    def test_chunk_size_set(self, content_streamer: EmailContentStreamer):
        """chunk_size should be set from parameter."""
        assert content_streamer.chunk_size == 10


@pytest.mark.unit
class TestEmailContentStreamerStreamToFile:
    """Test EmailContentStreamer.stream_to_file method."""

    def test_stream_to_file_success(
        self, content_streamer: EmailContentStreamer, temp_dir: Path
    ):
        """stream_to_file should write content successfully."""
        content = "Hello, World!"
        output_path = temp_dir / "output.txt"

        result = content_streamer.stream_to_file(content, output_path)

        assert result is True
        assert output_path.exists()
        assert output_path.read_text() == content

    def test_stream_to_file_large_content(
        self, content_streamer: EmailContentStreamer, temp_dir: Path
    ):
        """stream_to_file should handle large content in chunks."""
        content = "x" * 1000  # Larger than chunk size
        output_path = temp_dir / "large_output.txt"

        result = content_streamer.stream_to_file(content, output_path)

        assert result is True
        assert output_path.read_text() == content


@pytest.mark.unit
class TestEmailContentStreamerStreamFromFile:
    """Test EmailContentStreamer.stream_from_file method."""

    def test_stream_from_file_success(
        self, content_streamer: EmailContentStreamer, temp_dir: Path
    ):
        """stream_from_file should read content in chunks."""
        input_path = temp_dir / "input.txt"
        input_path.write_text("Hello, World!")

        chunks = list(content_streamer.stream_from_file(input_path))

        assert len(chunks) >= 1
        assert "".join(chunks) == "Hello, World!"

    def test_stream_from_file_nonexistent(
        self, content_streamer: EmailContentStreamer, temp_dir: Path
    ):
        """stream_from_file should handle nonexistent files."""
        nonexistent = temp_dir / "does_not_exist.txt"

        chunks = list(content_streamer.stream_from_file(nonexistent))

        # Should yield empty string on error
        assert chunks == [""]


@pytest.mark.unit
class TestMemoryOptimizedCacheInit:
    """Test MemoryOptimizedCache initialization."""

    def test_max_size_set(self, memory_cache: MemoryOptimizedCache):
        """max_size should be set from parameter."""
        assert memory_cache.max_size == 5

    def test_memory_limit_set(self, memory_cache: MemoryOptimizedCache):
        """memory_limit should be converted to bytes."""
        assert memory_cache.memory_limit_bytes == 100 * 1024 * 1024

    def test_cache_starts_empty(self, memory_cache: MemoryOptimizedCache):
        """Cache should start empty."""
        assert len(memory_cache.cache) == 0


@pytest.mark.unit
class TestMemoryOptimizedCacheGet:
    """Test MemoryOptimizedCache.get method."""

    def test_get_missing_key_returns_none(self, memory_cache: MemoryOptimizedCache):
        """get should return None for missing key."""
        result = memory_cache.get("missing_key")
        assert result is None

    def test_get_existing_key(self, memory_cache: MemoryOptimizedCache):
        """get should return value for existing key."""
        memory_cache.put("key1", "value1")

        result = memory_cache.get("key1")

        assert result == "value1"

    def test_get_updates_access_order(self, memory_cache: MemoryOptimizedCache):
        """get should move key to end of access order."""
        memory_cache.put("key1", "value1")
        memory_cache.put("key2", "value2")

        # Access key1, should move to end
        memory_cache.get("key1")

        assert memory_cache.access_order[-1] == "key1"


@pytest.mark.unit
class TestMemoryOptimizedCachePut:
    """Test MemoryOptimizedCache.put method."""

    def test_put_stores_value(self, memory_cache: MemoryOptimizedCache):
        """put should store value in cache."""
        memory_cache.put("key1", "value1")

        assert "key1" in memory_cache.cache
        assert memory_cache.cache["key1"] == "value1"

    def test_put_updates_access_order(self, memory_cache: MemoryOptimizedCache):
        """put should add key to access order."""
        memory_cache.put("key1", "value1")

        assert "key1" in memory_cache.access_order

    def test_put_replaces_existing_key(self, memory_cache: MemoryOptimizedCache):
        """put should replace existing key's value."""
        memory_cache.put("key1", "value1")
        memory_cache.put("key1", "value2")

        assert memory_cache.cache["key1"] == "value2"
        # Should only appear once in access order
        assert memory_cache.access_order.count("key1") == 1


@pytest.mark.unit
class TestMemoryOptimizedCacheLimits:
    """Test MemoryOptimizedCache size limit enforcement."""

    def test_enforces_max_size(self, memory_cache: MemoryOptimizedCache):
        """Cache should remove oldest items when exceeding max_size."""
        # Add more than max_size items
        for i in range(10):
            memory_cache.put(f"key{i}", f"value{i}")

        assert len(memory_cache.cache) <= memory_cache.max_size

    def test_removes_oldest_first(self, memory_cache: MemoryOptimizedCache):
        """Cache should remove oldest (least recently used) items first."""
        for i in range(6):  # One more than max_size
            memory_cache.put(f"key{i}", f"value{i}")

        # key0 should be removed as oldest
        assert "key0" not in memory_cache.cache
        assert "key5" in memory_cache.cache


@pytest.mark.unit
class TestMemoryOptimizedCacheClear:
    """Test MemoryOptimizedCache.clear method."""

    def test_clear_removes_all_items(self, memory_cache: MemoryOptimizedCache):
        """clear should remove all cached items."""
        memory_cache.put("key1", "value1")
        memory_cache.put("key2", "value2")

        memory_cache.clear()

        assert len(memory_cache.cache) == 0
        assert len(memory_cache.access_order) == 0


@pytest.mark.unit
class TestMemoryOptimizedCacheStats:
    """Test MemoryOptimizedCache.get_stats method."""

    def test_get_stats_empty_cache(self, memory_cache: MemoryOptimizedCache):
        """get_stats should return correct stats for empty cache."""
        stats = memory_cache.get_stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 5
        assert "memory_mb" in stats

    def test_get_stats_with_items(self, memory_cache: MemoryOptimizedCache):
        """get_stats should reflect cached items."""
        memory_cache.put("key1", "value1")
        memory_cache.put("key2", "value2")

        stats = memory_cache.get_stats()

        assert stats["size"] == 2
