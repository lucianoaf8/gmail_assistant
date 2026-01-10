"""
Metrics and observability for Gmail Assistant.
Provides structured metrics collection and reporting.

Features:
- Counter, gauge, and histogram metrics
- Labels for dimensional analysis
- Timer context manager for operation timing
- Thread-safe collection
- Periodic reporting and export

Usage:
    from gmail_assistant.utils.metrics import get_metrics, timer, inc_counter

    # Time an operation
    with timer('api_call', labels={'endpoint': 'messages'}):
        result = api.messages().list().execute()

    # Count events
    inc_counter('emails_fetched', value=10)

    # Get report
    report = get_metrics().report()
"""

import time
import logging
import threading
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


@dataclass
class HistogramStats:
    """Statistics for a histogram metric."""
    count: int
    sum: float
    min: float
    max: float
    mean: float
    p50: float
    p95: float
    p99: float


class MetricsCollector:
    """
    Thread-safe metrics collector.

    Supports three metric types:
    - Counter: Monotonically increasing value
    - Gauge: Point-in-time value
    - Histogram: Distribution of values with percentile calculation

    Example:
        >>> metrics = MetricsCollector()
        >>> metrics.inc_counter('requests_total')
        >>> metrics.set_gauge('active_connections', 42)
        >>> with metrics.timer('request_duration'):
        ...     do_something()
        >>> print(metrics.report())
    """

    def __init__(self, name: str = "gmail_assistant"):
        """
        Initialize metrics collector.

        Args:
            name: Name prefix for metrics
        """
        self.name = name
        self._lock = threading.Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._labels: Dict[str, Dict[str, str]] = {}
        self._start_time = datetime.now()
        self._last_reset = datetime.now()

    def inc_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Value to add (default 1)
            labels: Optional dimensional labels
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
            if labels:
                self._labels[key] = labels

    def dec_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Decrement a counter (use sparingly - counters should increase)."""
        self.inc_counter(name, -value, labels)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric to a specific value.

        Args:
            name: Gauge name
            value: Value to set
            labels: Optional dimensional labels
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
            if labels:
                self._labels[key] = labels

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram observation.

        Args:
            name: Histogram name
            value: Observed value
            labels: Optional dimensional labels
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            if labels:
                self._labels[key] = labels

    @contextmanager
    def timer(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Context manager for timing operations.

        Records duration as histogram and increments call counter.

        Args:
            name: Operation name
            labels: Optional dimensional labels

        Yields:
            None (timing happens automatically)
        """
        start = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.perf_counter() - start
            timer_labels = dict(labels) if labels else {}
            timer_labels['success'] = str(success).lower()

            self.observe_histogram(f"{name}_duration_seconds", duration, timer_labels)
            self.inc_counter(f"{name}_total", labels=timer_labels)

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create unique key for metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _parse_key(self, key: str) -> tuple:
        """Parse key back to name and labels."""
        if '{' not in key:
            return key, {}
        name, label_str = key.split('{', 1)
        label_str = label_str.rstrip('}')
        labels = {}
        if label_str:
            for pair in label_str.split(','):
                k, v = pair.split('=', 1)
                labels[k] = v
        return name, labels

    def get_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Get current counter value."""
        key = self._make_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0.0)

    def get_gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Get current gauge value."""
        key = self._make_key(name, labels)
        with self._lock:
            return self._gauges.get(key)

    def get_histogram_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[HistogramStats]:
        """Get histogram statistics."""
        key = self._make_key(name, labels)
        with self._lock:
            values = self._histograms.get(key, [])
            if not values:
                return None
            return self._calculate_histogram_stats(values)

    def _calculate_histogram_stats(self, values: List[float]) -> HistogramStats:
        """Calculate histogram statistics."""
        sorted_values = sorted(values)
        n = len(sorted_values)

        return HistogramStats(
            count=n,
            sum=sum(values),
            min=sorted_values[0],
            max=sorted_values[-1],
            mean=sum(values) / n,
            p50=sorted_values[n // 2],
            p95=sorted_values[int(n * 0.95)] if n > 20 else sorted_values[-1],
            p99=sorted_values[int(n * 0.99)] if n > 100 else sorted_values[-1],
        )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all current metrics as dictionary.

        Returns:
            Dictionary with counters, gauges, and histogram stats
        """
        with self._lock:
            result = {
                'name': self.name,
                'uptime_seconds': (datetime.now() - self._start_time).total_seconds(),
                'last_reset': self._last_reset.isoformat(),
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {}
            }

            # Calculate histogram statistics
            for key, values in self._histograms.items():
                if values:
                    stats = self._calculate_histogram_stats(values)
                    result['histograms'][key] = asdict(stats)

            return result

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._labels.clear()
            self._last_reset = datetime.now()
            logger.debug("Metrics reset")

    def report(self, output_file: Optional[str] = None) -> str:
        """
        Generate human-readable metrics report.

        Args:
            output_file: Optional file path to write report

        Returns:
            Formatted report string
        """
        metrics = self.get_metrics()

        lines = [
            "=" * 60,
            f" {self.name.upper()} METRICS REPORT ",
            "=" * 60,
            f"Uptime: {metrics['uptime_seconds']:.1f}s",
            f"Last Reset: {metrics['last_reset']}",
            "",
            "-" * 30 + " COUNTERS " + "-" * 30,
        ]

        for name, value in sorted(metrics['counters'].items()):
            lines.append(f"  {name}: {value:,.0f}")

        lines.extend([
            "",
            "-" * 30 + " GAUGES " + "-" * 32,
        ])

        for name, value in sorted(metrics['gauges'].items()):
            lines.append(f"  {name}: {value:,.2f}")

        lines.extend([
            "",
            "-" * 28 + " HISTOGRAMS " + "-" * 28,
        ])

        for name, stats in sorted(metrics['histograms'].items()):
            lines.append(f"  {name}:")
            lines.append(
                f"    count={stats['count']:,} mean={stats['mean']:.4f} "
                f"p50={stats['p50']:.4f} p95={stats['p95']:.4f} p99={stats['p99']:.4f}"
            )

        lines.append("=" * 60)

        report = "\n".join(lines)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
                f.write("\n\n--- RAW JSON ---\n")
                json.dump(metrics, f, indent=2, default=str)
            logger.info(f"Metrics report written to {output_file}")

        return report

    def export_json(self, output_file: str) -> None:
        """Export metrics as JSON file."""
        metrics = self.get_metrics()
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level metrics summary."""
        metrics = self.get_metrics()

        # Calculate totals
        total_ops = sum(
            v for k, v in metrics['counters'].items()
            if k.endswith('_total')
        )

        # Average durations
        durations = []
        for name, stats in metrics['histograms'].items():
            if 'duration' in name:
                durations.append(stats['mean'])

        return {
            'uptime_seconds': metrics['uptime_seconds'],
            'total_operations': total_ops,
            'avg_duration_seconds': sum(durations) / len(durations) if durations else 0,
            'counter_count': len(metrics['counters']),
            'gauge_count': len(metrics['gauges']),
            'histogram_count': len(metrics['histograms']),
        }


# =============================================================================
# Global Instance and Convenience Functions
# =============================================================================

_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def inc_counter(
    name: str,
    value: float = 1.0,
    labels: Optional[Dict[str, str]] = None
) -> None:
    """Increment counter (convenience function)."""
    get_metrics().inc_counter(name, value, labels)


def set_gauge(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
) -> None:
    """Set gauge (convenience function)."""
    get_metrics().set_gauge(name, value, labels)


def observe(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
) -> None:
    """Observe histogram value (convenience function)."""
    get_metrics().observe_histogram(name, value, labels)


def timer(name: str, labels: Optional[Dict[str, str]] = None):
    """Timer context manager (convenience function)."""
    return get_metrics().timer(name, labels)


# =============================================================================
# Decorator for Function Timing
# =============================================================================

def timed(name: Optional[str] = None, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to time function execution.

    Args:
        name: Metric name (defaults to function name)
        labels: Optional dimensional labels

    Example:
        @timed('database_query', labels={'table': 'emails'})
        def query_emails():
            ...
    """
    def decorator(func: Callable):
        metric_name = name or func.__name__

        def wrapper(*args, **kwargs):
            with timer(metric_name, labels):
                return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
