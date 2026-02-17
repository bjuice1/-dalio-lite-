# Observability & Monitoring Specification

**Document:** 04-observability-monitoring.md
**Project:** Dalio Lite Production Hardening
**Date:** 2026-02-17
**Status:** Final
**Dependencies:** 03-error-handling-recovery.md (error metrics taxonomy)
**Enables:** 06-migration-rollout.md (monitoring validates migration), 07-production-checklist.md (health check gates)

---

## Overview

This document defines the observability and monitoring infrastructure for Dalio Lite, addressing the **critical gap** identified in audit1: "Missing production observability - no monitoring, alerting, or observability beyond basic file logging."

**Why This Exists:**
- Current state: Single log file, no metrics, no health checks, no alerting
- Risk: Silent failures (AutoPilot crashes, no one notices until manual check)
- Operational blindness: Can't answer "When did last rebalance happen?", "Why did rebalancing stop?"
- Audit1 severity: High (operational failures invisible)

**What This Covers:**
- Metrics collection (rebalance success rate, API latency, order execution time)
- Health check endpoints
- Alerting rules and thresholds
- Operational dashboard (Streamlit page)
- Historical tracking and trending

**What This Does NOT Cover:**
- Distributed tracing (single-process system)
- APM (New Relic, DataDog) integration (optional future upgrade)
- Real-time alerting infrastructure (PagerDuty, etc.) - using email notifications

---

## Architecture

### Metrics Collection Flow

```
┌─────────────────────────────────────────────────────────────┐
│              DalioLite Operations                           │
│  • Rebalance execution                                      │
│  • Order submission                                         │
│  • API calls                                                │
│  • Circuit breaker checks                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ Record metrics
┌─────────────────────────────────────────────────────────────┐
│            MetricsCollector (NEW)                           │
│  • Increments counters                                      │
│  • Records durations                                        │
│  • Tracks gauges                                            │
│  • Thread-safe                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ Write every 60s
┌─────────────────────────────────────────────────────────────┐
│      monitoring/metrics.json (Time-Series Data)             │
│  {                                                           │
│    "timestamp": "2026-02-17T10:00:00Z",                     │
│    "rebalance_total": 42,                                   │
│    "rebalance_success": 40,                                 │
│    "rebalance_failed": 2,                                   │
│    "orders_executed": 168,                                  │
│    "avg_rebalance_duration_seconds": 12.5                   │
│  }                                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ Read by
┌─────────────────────────────────────────────────────────────┐
│        Streamlit Dashboard (Monitoring Page)                │
│  • Charts (success rate over time)                          │
│  • Tables (recent operations)                               │
│  • Alerts (health check status)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Specification

### 1. Metrics to Track

| Metric | Type | Description | Alert Threshold |
|--------|------|-------------|-----------------|
| **rebalance_total** | Counter | Total rebalances attempted | - |
| **rebalance_success** | Counter | Successful rebalances | - |
| **rebalance_failed** | Counter | Failed rebalances | >1 in 7 days |
| **rebalance_partial** | Counter | Partial failures | >2 in 30 days |
| **orders_executed** | Counter | Total orders submitted | - |
| **orders_success** | Counter | Successful orders | - |
| **orders_failed** | Counter | Failed orders | >5% failure rate |
| **circuit_breaker_triggered** | Counter | Circuit breaker activations | >0 (immediate alert) |
| **api_calls_total** | Counter | Alpaca API calls | - |
| **api_errors** | Counter | API errors | >10 in 1 hour |
| **rebalance_duration_seconds** | Histogram | Time to complete rebalance | >60s (investigate) |
| **order_execution_duration_ms** | Histogram | Time per order | >5000ms (slow API) |
| **portfolio_value_usd** | Gauge | Current portfolio value | - |
| **drift_max_pct** | Gauge | Max drift from target | >15% (should rebalance) |
| **days_since_rebalance** | Gauge | Days since last rebalance | >60 days (stuck?) |
| **autopilot_last_run** | Timestamp | Last AutoPilot execution | >2 days ago (broken?) |
| **lock_acquisition_time_ms** | Histogram | Time to acquire state lock | >5000ms (contention) |

---

### 2. MetricsCollector Implementation

**File:** `metrics_collector.py` (new file)

```python
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
        if self._initialized:
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
                    elif key.endswith('_usd') or key.endswith('_pct'):
                        self.gauges[key] = value

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
```

---

### 3. Instrumentation Points

**Modified `dalio_lite.py` with metrics collection:**

```python
from metrics_collector import metrics

class DalioLite:
    # ... existing code ...

    def execute_rebalance(self, dry_run: bool = False) -> bool:
        """Execute rebalancing with metrics collection."""
        start_time = time.time()

        try:
            metrics.increment("rebalance_total")

            # ... existing rebalance logic ...

            if all_success:
                metrics.increment("rebalance_success")
            else:
                metrics.increment("rebalance_partial")

            return all_success

        except Exception as e:
            metrics.increment("rebalance_failed")
            raise

        finally:
            # Record duration
            duration = time.time() - start_time
            metrics.record_duration("rebalance_duration_seconds", duration)

            # Update gauges
            self._update_gauges()

            # Flush metrics to disk
            metrics.flush()

    def _execute_order(self, ticker: str, amount_usd: float, side: OrderSide, max_retries: int = 3):
        """Execute order with metrics."""
        start_time = time.time()

        try:
            metrics.increment("orders_executed")
            metrics.increment("api_calls_total")

            result = self._execute_order_impl(ticker, amount_usd, side, max_retries)

            if result.status == OrderStatus.SUCCESS:
                metrics.increment("orders_success")
            else:
                metrics.increment("orders_failed")

            return result

        except Exception as e:
            metrics.increment("api_errors")
            raise

        finally:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_duration("order_execution_duration_ms", duration_ms)

    def _update_gauges(self):
        """Update gauge metrics with current state."""
        # Portfolio value
        account = self.trading_client.get_account()
        metrics.set_gauge("portfolio_value_usd", float(account.portfolio_value))

        # Max drift
        drift = self.calculate_drift()
        max_drift = max(abs(d) for d in drift.values())
        metrics.set_gauge("drift_max_pct", max_drift * 100)

        # Days since last rebalance
        if self.last_rebalance:
            days_since = (datetime.now() - self.last_rebalance).days
            metrics.set_gauge("days_since_rebalance", days_since)

    def check_circuit_breakers(self):
        """Check circuit breakers with metrics."""
        triggered, reason = self._check_circuit_breakers_impl()

        if triggered:
            metrics.increment("circuit_breaker_triggered")

        return triggered, reason

    def run_daily_check(self, dry_run: bool = False):
        """Daily check with metrics."""
        # Record AutoPilot execution
        metrics.set_timestamp("autopilot_last_run")

        # ... existing logic ...

        metrics.flush()
```

---

### 4. Health Check System

**New File:** `health_check.py`

```python
"""Health check system for operational status."""

from datetime import datetime, timedelta
from typing import Dict, Tuple
from metrics_collector import metrics
import json
from pathlib import Path

class HealthChecker:
    """Check system health and raise alerts."""

    def check_all(self) -> Tuple[str, Dict]:
        """
        Run all health checks.

        Returns:
            (status, details) where status is "healthy", "warning", or "critical"
        """
        checks = {
            "autopilot": self._check_autopilot(),
            "rebalance_success_rate": self._check_rebalance_success_rate(),
            "circuit_breaker": self._check_circuit_breaker(),
            "api_errors": self._check_api_errors(),
            "drift": self._check_drift()
        }

        # Aggregate status
        if any(c["status"] == "critical" for c in checks.values()):
            overall_status = "critical"
        elif any(c["status"] == "warning" for c in checks.values()):
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return overall_status, checks

    def _check_autopilot(self) -> Dict:
        """Check if AutoPilot is running on schedule."""
        try:
            # Load metrics
            metrics_file = Path("monitoring/metrics.json")
            if not metrics_file.exists():
                return {"status": "warning", "message": "No metrics file found"}

            with open(metrics_file, 'r') as f:
                data = json.load(f)

            last_run_str = data.get("autopilot_last_run")
            if not last_run_str:
                return {"status": "warning", "message": "AutoPilot never run"}

            last_run = datetime.fromisoformat(last_run_str)
            hours_since = (datetime.now() - last_run).total_seconds() / 3600

            if hours_since > 48:  # 2 days
                return {
                    "status": "critical",
                    "message": f"AutoPilot last ran {hours_since:.1f} hours ago (expected: daily)"
                }
            elif hours_since > 30:  # 1.25 days
                return {
                    "status": "warning",
                    "message": f"AutoPilot last ran {hours_since:.1f} hours ago"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"Last ran {hours_since:.1f} hours ago"
                }

        except Exception as e:
            return {"status": "warning", "message": f"Check failed: {e}"}

    def _check_rebalance_success_rate(self) -> Dict:
        """Check rebalance success rate."""
        try:
            metrics_file = Path("monitoring/metrics.json")
            with open(metrics_file, 'r') as f:
                data = json.load(f)

            total = data.get("rebalance_total", 0)
            success = data.get("rebalance_success", 0)
            failed = data.get("rebalance_failed", 0)

            if total == 0:
                return {"status": "healthy", "message": "No rebalances yet"}

            success_rate = (success / total) * 100

            if success_rate < 50:
                return {
                    "status": "critical",
                    "message": f"Success rate: {success_rate:.1f}% ({success}/{total})"
                }
            elif success_rate < 80:
                return {
                    "status": "warning",
                    "message": f"Success rate: {success_rate:.1f}% ({success}/{total})"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"Success rate: {success_rate:.1f}% ({success}/{total})"
                }

        except Exception as e:
            return {"status": "warning", "message": f"Check failed: {e}"}

    # ... similar methods for other checks ...

# Global instance
health = HealthChecker()
```

---

### 5. Monitoring Dashboard Page

**New File:** `pages/5_📊_Monitoring.py`

```python
"""Monitoring dashboard page."""

import streamlit as st
import json
from pathlib import Path
import plotly.graph_objects as go
from datetime import datetime, timedelta
from health_check import health

st.set_page_config(page_title="Monitoring", page_icon="📊", layout="wide")

st.title("📊 System Monitoring")

# Health check section
st.header("🏥 Health Status")

status, checks = health.check_all()

# Status badge
if status == "healthy":
    st.success("✅ System Healthy")
elif status == "warning":
    st.warning("⚠️ Warnings Detected")
else:
    st.error("🔴 Critical Issues")

# Health check details
cols = st.columns(len(checks))
for col, (check_name, check_result) in zip(cols, checks.items()):
    with col:
        status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "🔴"}[check_result["status"]]
        st.metric(
            check_name.replace("_", " ").title(),
            status_icon,
            check_result["message"]
        )

# Metrics section
st.header("📈 Metrics")

try:
    with open("monitoring/metrics.json", 'r') as f:
        metrics_data = json.load(f)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Rebalances",
            metrics_data.get("rebalance_total", 0),
            help="Total rebalances attempted"
        )

    with col2:
        success_rate = (metrics_data.get("rebalance_success", 0) /
                       max(metrics_data.get("rebalance_total", 1), 1)) * 100
        st.metric(
            "Success Rate",
            f"{success_rate:.1f}%",
            help="Percentage of successful rebalances"
        )

    with col3:
        st.metric(
            "Orders Executed",
            metrics_data.get("orders_executed", 0),
            help="Total orders submitted to Alpaca"
        )

    with col4:
        avg_duration = metrics_data.get("rebalance_duration_seconds_avg", 0)
        st.metric(
            "Avg Rebalance Time",
            f"{avg_duration:.1f}s",
            help="Average time to complete rebalance"
        )

    # Charts...

except FileNotFoundError:
    st.warning("No metrics data available yet. Metrics will appear after first rebalance.")
```

---

## Verification Strategy

**Metrics collection verified when:**
- [ ] `monitoring/metrics.json` created after first rebalance
- [ ] Metrics increment correctly
- [ ] Dashboard displays metrics
- [ ] Health checks run without errors

---

## Results Criteria

- [ ] All operations instrumented with metrics
- [ ] Metrics visible in dashboard
- [ ] Health checks detect AutoPilot failures
- [ ] Alert thresholds configured

---

**Status:** Ready for implementation
**Next Document:** 05-backup-disaster-recovery.md
