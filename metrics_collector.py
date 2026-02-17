"""Metrics collection for Dalio Lite observability."""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from threading import Lock
from collections import defaultdict


class MetricsCollector:
    """
    Collects and persists operational metrics.

    Thread-safe singleton for recording metrics from any part of the application.
    Writes metrics to JSON file periodically for dashboard consumption.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global metrics collection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, metrics_file: str = "monitoring/metrics.json"):
        """Initialize metrics collector (only once)."""
        if getattr(self, '_initialized', False):
            return

        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timestamps: Dict[str, str] = {}

        self._write_lock = Lock()

        # Load existing metrics
        self._load_metrics()

        self._initialized = True

    def increment(self, metric_name: str, value: int = 1):
        """Increment a counter metric."""
        with self._write_lock:
            self.counters[metric_name] += value

    def set_gauge(self, metric_name: str, value: float):
        """Set a gauge metric (current value)."""
        with self._write_lock:
            self.gauges[metric_name] = value

    def record_duration(self, metric_name: str, duration_seconds: float):
        """Record a duration measurement (histogram)."""
        with self._write_lock:
            self.histograms[metric_name].append(duration_seconds)
            # Keep last 1000 measurements
            if len(self.histograms[metric_name]) > 1000:
                self.histograms[metric_name] = self.histograms[metric_name][-1000:]

    def set_timestamp(self, metric_name: str):
        """Set a timestamp metric (ISO 8601)."""
        with self._write_lock:
            self.timestamps[metric_name] = datetime.now().isoformat()

    def flush(self):
        """Write metrics to disk."""
        with self._write_lock:
            # Calculate histogram stats
            histogram_stats = {}
            for name, values in self.histograms.items():
                if values:
                    histogram_stats[f"{name}_avg"] = sum(values) / len(values)
                    histogram_stats[f"{name}_p95"] = self._percentile(values, 95)
                    histogram_stats[f"{name}_max"] = max(values)

            # Combine all metrics
            data = {
                "last_updated": datetime.now().isoformat(),
                **self.counters,
                **self.gauges,
                **histogram_stats,
                **self.timestamps
            }

            # Write to file (atomic)
            temp_file = self.metrics_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)

            temp_file.replace(self.metrics_file)

    def _load_metrics(self):
        """Load existing metrics from disk."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)

                # Restore counters and gauges
                for key, value in data.items():
                    if key.endswith('_total') or key.endswith('_success') or key.endswith('_failed'):
                        self.counters[key] = value
                    elif key.endswith('_usd') or key.endswith('_pct') or key.endswith('_days'):
                        self.gauges[key] = value
                    elif key.endswith('_last_run'):
                        self.timestamps[key] = value

            except Exception:
                pass  # Start fresh if corrupted

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100.0))
        return sorted_values[min(index, len(sorted_values) - 1)]


# Global singleton instance
metrics = MetricsCollector()
