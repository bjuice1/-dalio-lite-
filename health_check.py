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

    def _check_circuit_breaker(self) -> Dict:
        """Check if circuit breaker has triggered recently."""
        try:
            metrics_file = Path("monitoring/metrics.json")
            with open(metrics_file, 'r') as f:
                data = json.load(f)

            triggered_count = data.get("circuit_breaker_triggered", 0)

            if triggered_count > 0:
                return {
                    "status": "critical",
                    "message": f"Circuit breaker triggered {triggered_count} times"
                }
            else:
                return {
                    "status": "healthy",
                    "message": "No circuit breaker activations"
                }

        except Exception as e:
            return {"status": "warning", "message": f"Check failed: {e}"}

    def _check_api_errors(self) -> Dict:
        """Check API error rate."""
        try:
            metrics_file = Path("monitoring/metrics.json")
            with open(metrics_file, 'r') as f:
                data = json.load(f)

            api_errors = data.get("api_errors", 0)
            api_calls = data.get("api_calls_total", 1)  # Avoid division by zero

            error_rate = (api_errors / api_calls) * 100

            if error_rate > 10:
                return {
                    "status": "critical",
                    "message": f"API error rate: {error_rate:.1f}% ({api_errors}/{api_calls})"
                }
            elif error_rate > 5:
                return {
                    "status": "warning",
                    "message": f"API error rate: {error_rate:.1f}% ({api_errors}/{api_calls})"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"API error rate: {error_rate:.1f}% ({api_errors}/{api_calls})"
                }

        except Exception as e:
            return {"status": "warning", "message": f"Check failed: {e}"}

    def _check_drift(self) -> Dict:
        """Check portfolio drift."""
        try:
            metrics_file = Path("monitoring/metrics.json")
            with open(metrics_file, 'r') as f:
                data = json.load(f)

            drift_max_pct = data.get("drift_max_pct", 0)
            days_since_rebalance = data.get("days_since_rebalance", 0)

            if drift_max_pct > 15:
                return {
                    "status": "warning",
                    "message": f"Max drift: {drift_max_pct:.1f}% (should rebalance)"
                }
            elif days_since_rebalance > 60:
                return {
                    "status": "warning",
                    "message": f"{days_since_rebalance} days since last rebalance"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"Drift: {drift_max_pct:.1f}%, Last rebalance: {days_since_rebalance} days ago"
                }

        except Exception as e:
            return {"status": "warning", "message": f"Check failed: {e}"}


# Global instance
health = HealthChecker()
