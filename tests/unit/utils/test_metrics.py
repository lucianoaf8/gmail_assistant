"""
Comprehensive tests for metrics.py module.
Tests MetricsCollector class for metrics collection and reporting.
"""

import tempfile
import threading
import time
from pathlib import Path

import pytest

from gmail_assistant.utils.metrics import (
    MetricsCollector,
    MetricPoint,
    HistogramStats,
    get_metrics,
    inc_counter,
    set_gauge,
    observe,
    timer,
    timed,
)


class TestMetricPoint:
    """Tests for MetricPoint dataclass."""

    def test_metric_point_creation(self):
        """Test creating a MetricPoint."""
        from datetime import datetime
        point = MetricPoint(
            name="test_metric",
            value=42.0,
            timestamp=datetime.now(),
            labels={"env": "test"},
            metric_type="counter"
        )
        assert point.name == "test_metric"
        assert point.value == 42.0
        assert point.labels == {"env": "test"}
        assert point.metric_type == "counter"

    def test_metric_point_default_type(self):
        """Test MetricPoint default metric_type is gauge."""
        from datetime import datetime
        point = MetricPoint(
            name="test",
            value=1.0,
            timestamp=datetime.now()
        )
        assert point.metric_type == "gauge"


class TestHistogramStats:
    """Tests for HistogramStats dataclass."""

    def test_histogram_stats_creation(self):
        """Test creating HistogramStats."""
        stats = HistogramStats(
            count=100,
            sum=500.0,
            min=1.0,
            max=10.0,
            mean=5.0,
            p50=4.5,
            p95=9.0,
            p99=9.9
        )
        assert stats.count == 100
        assert stats.sum == 500.0
        assert stats.min == 1.0
        assert stats.max == 10.0
        assert stats.mean == 5.0
        assert stats.p50 == 4.5
        assert stats.p95 == 9.0
        assert stats.p99 == 9.9


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_collector_init(self, collector):
        """Test MetricsCollector initialization."""
        assert collector.name == "test"

    def test_collector_default_name(self):
        """Test MetricsCollector default name."""
        collector = MetricsCollector()
        assert collector.name == "gmail_assistant"


class TestCounterMetrics:
    """Tests for counter metrics."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_inc_counter_default(self, collector):
        """Test incrementing counter by default value."""
        collector.inc_counter("requests")
        assert collector.get_counter("requests") == 1.0

    def test_inc_counter_custom_value(self, collector):
        """Test incrementing counter by custom value."""
        collector.inc_counter("emails_processed", value=10)
        assert collector.get_counter("emails_processed") == 10.0

    def test_inc_counter_accumulates(self, collector):
        """Test counter accumulates values."""
        collector.inc_counter("total", value=5)
        collector.inc_counter("total", value=3)
        assert collector.get_counter("total") == 8.0

    def test_inc_counter_with_labels(self, collector):
        """Test counter with labels."""
        collector.inc_counter("requests", labels={"status": "200"})
        collector.inc_counter("requests", labels={"status": "500"})
        assert collector.get_counter("requests", labels={"status": "200"}) == 1.0
        assert collector.get_counter("requests", labels={"status": "500"}) == 1.0

    def test_dec_counter(self, collector):
        """Test decrementing counter."""
        collector.inc_counter("balance", value=100)
        collector.dec_counter("balance", value=30)
        assert collector.get_counter("balance") == 70.0

    def test_get_counter_nonexistent(self, collector):
        """Test getting non-existent counter returns 0."""
        assert collector.get_counter("nonexistent") == 0.0


class TestGaugeMetrics:
    """Tests for gauge metrics."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_set_gauge(self, collector):
        """Test setting gauge value."""
        collector.set_gauge("temperature", 98.6)
        assert collector.get_gauge("temperature") == 98.6

    def test_set_gauge_overwrites(self, collector):
        """Test setting gauge overwrites previous value."""
        collector.set_gauge("connections", 10)
        collector.set_gauge("connections", 15)
        assert collector.get_gauge("connections") == 15

    def test_set_gauge_with_labels(self, collector):
        """Test gauge with labels."""
        collector.set_gauge("cpu_usage", 50.0, labels={"host": "server1"})
        collector.set_gauge("cpu_usage", 75.0, labels={"host": "server2"})
        assert collector.get_gauge("cpu_usage", labels={"host": "server1"}) == 50.0
        assert collector.get_gauge("cpu_usage", labels={"host": "server2"}) == 75.0

    def test_get_gauge_nonexistent(self, collector):
        """Test getting non-existent gauge returns None."""
        assert collector.get_gauge("nonexistent") is None


class TestHistogramMetrics:
    """Tests for histogram metrics."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_observe_histogram(self, collector):
        """Test observing histogram values."""
        collector.observe_histogram("response_time", 0.5)
        collector.observe_histogram("response_time", 1.0)
        collector.observe_histogram("response_time", 1.5)

        stats = collector.get_histogram_stats("response_time")
        assert stats is not None
        assert stats.count == 3
        assert stats.sum == 3.0

    def test_histogram_stats_calculation(self, collector):
        """Test histogram statistics are calculated correctly."""
        for i in range(1, 101):
            collector.observe_histogram("values", float(i))

        stats = collector.get_histogram_stats("values")
        assert stats.count == 100
        assert stats.min == 1.0
        assert stats.max == 100.0
        assert stats.mean == 50.5

    def test_histogram_with_labels(self, collector):
        """Test histogram with labels."""
        collector.observe_histogram("latency", 0.1, labels={"endpoint": "/api"})
        collector.observe_histogram("latency", 0.2, labels={"endpoint": "/api"})

        stats = collector.get_histogram_stats("latency", labels={"endpoint": "/api"})
        assert stats.count == 2

    def test_get_histogram_nonexistent(self, collector):
        """Test getting non-existent histogram returns None."""
        stats = collector.get_histogram_stats("nonexistent")
        assert stats is None


class TestTimerContext:
    """Tests for timer context manager."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_timer_records_duration(self, collector):
        """Test timer records operation duration."""
        with collector.timer("operation"):
            time.sleep(0.01)  # 10ms

        # Timer adds labels {"success": "true"}, so query with labels
        stats = collector.get_histogram_stats(
            "operation_duration_seconds",
            labels={"success": "true"}
        )
        assert stats is not None
        assert stats.count == 1
        assert stats.min >= 0.005  # At least ~10ms (allow some variance)

    def test_timer_increments_counter(self, collector):
        """Test timer increments call counter."""
        with collector.timer("api_call"):
            pass

        counter = collector.get_counter("api_call_total", labels={"success": "true"})
        assert counter == 1.0

    def test_timer_on_exception(self, collector):
        """Test timer records failure on exception."""
        with pytest.raises(ValueError):
            with collector.timer("failing_op"):
                raise ValueError("Test error")

        counter = collector.get_counter("failing_op_total", labels={"success": "false"})
        assert counter == 1.0

    def test_timer_with_labels(self, collector):
        """Test timer with custom labels."""
        with collector.timer("request", labels={"method": "GET"}):
            pass

        stats = collector.get_histogram_stats(
            "request_duration_seconds",
            labels={"method": "GET", "success": "true"}
        )
        assert stats is not None


class TestMetricsReport:
    """Tests for metrics reporting."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_get_metrics(self, collector):
        """Test get_metrics returns all metrics."""
        collector.inc_counter("requests", value=10)
        collector.set_gauge("connections", 5)
        collector.observe_histogram("latency", 0.1)

        metrics = collector.get_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
        assert "uptime_seconds" in metrics

    def test_report_generation(self, collector):
        """Test report generates string output."""
        collector.inc_counter("test_counter")
        collector.set_gauge("test_gauge", 42)

        report = collector.report()
        assert "METRICS REPORT" in report
        assert "COUNTERS" in report
        assert "GAUGES" in report

    def test_report_to_file(self, collector, temp_dir):
        """Test report writes to file."""
        collector.inc_counter("test")
        output_file = str(temp_dir / "metrics.txt")

        collector.report(output_file=output_file)

        assert Path(output_file).exists()
        content = Path(output_file).read_text()
        assert "METRICS REPORT" in content

    def test_export_json(self, collector, temp_dir):
        """Test exporting metrics as JSON."""
        collector.inc_counter("requests", value=100)
        output_file = str(temp_dir / "metrics.json")

        collector.export_json(output_file)

        assert Path(output_file).exists()
        import json
        with open(output_file) as f:
            data = json.load(f)
        assert "counters" in data

    def test_get_summary(self, collector):
        """Test get_summary returns high-level stats."""
        collector.inc_counter("requests_total", value=100)
        with collector.timer("operation"):
            pass

        summary = collector.get_summary()
        assert "uptime_seconds" in summary
        assert "total_operations" in summary
        assert "counter_count" in summary


class TestMetricsReset:
    """Tests for metrics reset functionality."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_reset_clears_all_metrics(self, collector):
        """Test reset clears all metrics."""
        collector.inc_counter("counter1", value=10)
        collector.set_gauge("gauge1", 50)
        collector.observe_histogram("histogram1", 1.0)

        collector.reset()

        assert collector.get_counter("counter1") == 0.0
        assert collector.get_gauge("gauge1") is None
        assert collector.get_histogram_stats("histogram1") is None

    def test_reset_updates_last_reset(self, collector):
        """Test reset updates last_reset timestamp."""
        initial_metrics = collector.get_metrics()
        initial_reset = initial_metrics["last_reset"]

        time.sleep(0.01)
        collector.reset()

        new_metrics = collector.get_metrics()
        assert new_metrics["last_reset"] != initial_reset


class TestKeyHandling:
    """Tests for metric key handling with labels."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_make_key_no_labels(self, collector):
        """Test key generation without labels."""
        key = collector._make_key("metric_name")
        assert key == "metric_name"

    def test_make_key_with_labels(self, collector):
        """Test key generation with labels."""
        key = collector._make_key("metric", {"a": "1", "b": "2"})
        assert "metric" in key
        assert "a=1" in key
        assert "b=2" in key

    def test_parse_key_no_labels(self, collector):
        """Test parsing key without labels."""
        name, labels = collector._parse_key("simple_metric")
        assert name == "simple_metric"
        assert labels == {}

    def test_parse_key_with_labels(self, collector):
        """Test parsing key with labels."""
        name, labels = collector._parse_key("metric{env=prod,host=server1}")
        assert name == "metric"
        assert labels == {"env": "prod", "host": "server1"}


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_counter_increments(self):
        """Test counter is thread-safe for concurrent increments."""
        collector = MetricsCollector()
        threads = []

        def increment():
            for _ in range(1000):
                collector.inc_counter("concurrent_test")

        for _ in range(10):
            t = threading.Thread(target=increment)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert collector.get_counter("concurrent_test") == 10000.0

    def test_concurrent_gauge_updates(self):
        """Test gauge is thread-safe for concurrent updates."""
        collector = MetricsCollector()
        threads = []

        def update_gauge(value):
            collector.set_gauge("test_gauge", value)

        for i in range(10):
            t = threading.Thread(target=update_gauge, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have a valid final value
        assert collector.get_gauge("test_gauge") is not None


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_metrics_returns_collector(self):
        """Test get_metrics returns MetricsCollector."""
        collector = get_metrics()
        assert isinstance(collector, MetricsCollector)

    def test_get_metrics_singleton(self):
        """Test get_metrics returns same instance."""
        collector1 = get_metrics()
        collector2 = get_metrics()
        assert collector1 is collector2

    def test_inc_counter_function(self):
        """Test inc_counter convenience function."""
        initial = get_metrics().get_counter("global_test")
        inc_counter("global_test", value=5)
        assert get_metrics().get_counter("global_test") == initial + 5

    def test_set_gauge_function(self):
        """Test set_gauge convenience function."""
        set_gauge("global_gauge", 123.0)
        assert get_metrics().get_gauge("global_gauge") == 123.0

    def test_observe_function(self):
        """Test observe convenience function."""
        observe("global_histogram", 1.5)
        stats = get_metrics().get_histogram_stats("global_histogram")
        assert stats is not None

    def test_timer_function(self):
        """Test timer convenience function."""
        with timer("global_timer"):
            pass
        # Timer adds labels {"success": "true"}
        stats = get_metrics().get_histogram_stats(
            "global_timer_duration_seconds",
            labels={"success": "true"}
        )
        assert stats is not None


class TestTimedDecorator:
    """Tests for @timed decorator."""

    def test_timed_decorator_basic(self):
        """Test @timed decorator records timing."""
        collector = MetricsCollector()

        @timed("decorated_func")
        def my_function():
            return "result"

        # Execute with the global metrics
        result = my_function()
        assert result == "result"

    def test_timed_decorator_preserves_function_name(self):
        """Test @timed preserves function name."""
        @timed("test")
        def original_name():
            pass

        assert original_name.__name__ == "original_name"

    def test_timed_decorator_default_name(self):
        """Test @timed uses function name as default."""
        @timed()
        def auto_named():
            pass

        # Function should still work
        auto_named()

    def test_timed_decorator_with_labels(self):
        """Test @timed with custom labels."""
        @timed("api", labels={"version": "v1"})
        def api_call():
            return True

        result = api_call()
        assert result is True


class TestHistogramCalculations:
    """Tests for histogram statistics calculations."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(name="test")

    def test_percentile_calculation_small_sample(self, collector):
        """Test percentile calculation with small sample."""
        for v in [1, 2, 3, 4, 5]:
            collector.observe_histogram("small", float(v))

        stats = collector.get_histogram_stats("small")
        assert stats.p50 == 3.0  # Median
        assert stats.p95 == 5.0  # Small sample uses max
        assert stats.p99 == 5.0

    def test_percentile_calculation_large_sample(self, collector):
        """Test percentile calculation with large sample."""
        for i in range(1, 201):
            collector.observe_histogram("large", float(i))

        stats = collector.get_histogram_stats("large")
        # With 200 values, median (p50) should be around 100-101
        assert 99 <= stats.p50 <= 102
        # 95th percentile should be around 190
        assert 185 <= stats.p95 <= 195
        # 99th percentile should be around 198
        assert 196 <= stats.p99 <= 200
