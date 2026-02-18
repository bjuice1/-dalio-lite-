"""System monitoring dashboard page."""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta
from health_check import health

# Import error handling and trust indicators
from error_handler import translate_exception, handle_error_display
from trust_indicators import render_trust_bar

st.set_page_config(page_title="Monitoring", page_icon="📊", layout="wide")

# Trust indicators
render_trust_bar()

st.title("📊 System Monitoring")

st.markdown("""
Monitor the health and performance of Dalio Lite's automated rebalancing system.
This page shows operational metrics, health checks, and system status.
""")

# Health check section
st.header("🏥 Health Status")

try:
    status, checks = health.check_all()

    # Status badge
    if status == "healthy":
        st.success("✅ **System Healthy** - All checks passing")
    elif status == "warning":
        st.warning("⚠️ **Warnings Detected** - Some issues require attention")
    else:
        st.error("🔴 **Critical Issues** - Immediate action required")

    # Health check details in columns
    st.subheader("Health Check Details")

    check_items = list(checks.items())
    # Split into rows of 3 columns each
    for i in range(0, len(check_items), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(check_items):
                check_name, check_result = check_items[i + j]
                with col:
                    status_icon = {
                        "healthy": "✅",
                        "warning": "⚠️",
                        "critical": "🔴"
                    }[check_result["status"]]

                    st.metric(
                        label=check_name.replace("_", " ").title(),
                        value=status_icon,
                        help=check_result["message"]
                    )
                    st.caption(check_result["message"])

except Exception as e:
    message, severity = translate_exception(e, context="Running health check")
    handle_error_display(message, severity)

st.divider()

# Metrics section
st.header("📈 Operational Metrics")

try:
    metrics_file = Path("monitoring/metrics.json")

    if not metrics_file.exists():
        st.warning("⚠️ No metrics data available yet. Metrics will appear after the first rebalance operation.")
    else:
        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)

        # Last updated
        last_updated = metrics_data.get("last_updated", "Unknown")
        st.caption(f"📅 Last updated: {last_updated}")

        # Key metrics in columns
        st.subheader("Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_rebalances = metrics_data.get("rebalance_total", 0)
            st.metric(
                label="Total Rebalances",
                value=total_rebalances,
                help="Total rebalancing operations attempted"
            )

        with col2:
            success = metrics_data.get("rebalance_success", 0)
            total = max(metrics_data.get("rebalance_total", 1), 1)
            success_rate = (success / total) * 100

            delta_color = "normal" if success_rate >= 80 else "inverse"
            st.metric(
                label="Success Rate",
                value=f"{success_rate:.1f}%",
                delta=f"{success}/{total}",
                help="Percentage of successful rebalances"
            )

        with col3:
            orders_executed = metrics_data.get("orders_executed", 0)
            orders_success = metrics_data.get("orders_success", 0)
            st.metric(
                label="Orders Executed",
                value=orders_executed,
                delta=f"{orders_success} succeeded",
                help="Total orders submitted to Alpaca"
            )

        with col4:
            avg_duration = metrics_data.get("rebalance_duration_seconds_avg", 0)
            st.metric(
                label="Avg Rebalance Time",
                value=f"{avg_duration:.1f}s",
                help="Average time to complete rebalancing operation"
            )

        st.divider()

        # Portfolio metrics
        st.subheader("Portfolio Health")
        col1, col2, col3 = st.columns(3)

        with col1:
            portfolio_value = metrics_data.get("portfolio_value_usd", 0)
            st.metric(
                label="Portfolio Value",
                value=f"${portfolio_value:,.2f}",
                help="Current total portfolio value"
            )

        with col2:
            drift_max_pct = metrics_data.get("drift_max_pct", 0)
            st.metric(
                label="Max Drift",
                value=f"{drift_max_pct:.2f}%",
                help="Maximum deviation from target allocation"
            )

        with col3:
            days_since = metrics_data.get("days_since_rebalance", 0)
            st.metric(
                label="Days Since Rebalance",
                value=days_since,
                help="Days since last successful rebalance"
            )

        st.divider()

        # API and System metrics
        st.subheader("API & System Performance")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            api_calls = metrics_data.get("api_calls_total", 0)
            st.metric(
                label="Total API Calls",
                value=api_calls,
                help="Total calls to Alpaca API"
            )

        with col2:
            api_errors = metrics_data.get("api_errors", 0)
            error_rate = (api_errors / max(api_calls, 1)) * 100
            st.metric(
                label="API Error Rate",
                value=f"{error_rate:.1f}%",
                delta=f"{api_errors} errors",
                delta_color="inverse" if error_rate > 5 else "normal",
                help="Percentage of failed API calls"
            )

        with col3:
            circuit_breaker = metrics_data.get("circuit_breaker_triggered", 0)
            st.metric(
                label="Circuit Breaker",
                value=circuit_breaker,
                delta="Triggered!" if circuit_breaker > 0 else "Normal",
                delta_color="inverse" if circuit_breaker > 0 else "normal",
                help="Number of times circuit breaker has activated"
            )

        with col4:
            lock_time_avg = metrics_data.get("lock_acquisition_time_ms_avg", 0)
            st.metric(
                label="Avg Lock Time",
                value=f"{lock_time_avg:.1f}ms",
                help="Average time to acquire state lock (concurrency)"
            )

        st.divider()

        # Detailed metrics table
        with st.expander("📋 View All Metrics (Raw Data)"):
            st.json(metrics_data, expanded=False)

        # Performance histograms
        st.subheader("Performance Distribution")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Rebalance Duration**")
            if "rebalance_duration_seconds_p50" in metrics_data:
                p50 = metrics_data.get("rebalance_duration_seconds_p50", 0)
                p95 = metrics_data.get("rebalance_duration_seconds_p95", 0)
                p99 = metrics_data.get("rebalance_duration_seconds_p99", 0)

                st.write(f"- **P50 (median):** {p50:.1f}s")
                st.write(f"- **P95:** {p95:.1f}s")
                st.write(f"- **P99:** {p99:.1f}s")
            else:
                st.caption("Not enough data yet")

        with col2:
            st.markdown("**Order Execution Time**")
            if "order_execution_duration_ms_p50" in metrics_data:
                p50 = metrics_data.get("order_execution_duration_ms_p50", 0)
                p95 = metrics_data.get("order_execution_duration_ms_p95", 0)
                p99 = metrics_data.get("order_execution_duration_ms_p99", 0)

                st.write(f"- **P50 (median):** {p50:.0f}ms")
                st.write(f"- **P95:** {p95:.0f}ms")
                st.write(f"- **P99:** {p99:.0f}ms")
            else:
                st.caption("Not enough data yet")

except FileNotFoundError:
    st.warning("⚠️ No metrics data available yet. Metrics will appear after the first rebalance operation.")
except Exception as e:
    message, severity = translate_exception(e, context="Loading metrics data")
    handle_error_display(message, severity)

st.divider()

# Transaction log section
st.header("📜 Recent Transactions")

try:
    transactions_dir = Path("state/transactions")

    if not transactions_dir.exists() or not list(transactions_dir.glob("*.json")):
        st.info("No transaction logs available yet. Transactions will be logged during rebalancing operations.")
    else:
        # Get most recent transaction logs
        log_files = sorted(
            transactions_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:10]  # Show last 10 transactions

        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    tx = json.load(f)

                # Transaction header
                status_icon = {
                    "completed": "✅",
                    "partial": "⚠️",
                    "failed": "🔴",
                    "in_progress": "🔄"
                }.get(tx.get("status", "unknown"), "❓")

                timestamp = tx.get("timestamp", "Unknown")
                operation = tx.get("operation", "Unknown")

                with st.expander(f"{status_icon} {operation} - {timestamp}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Target Orders**")
                        target_orders = tx.get("target_orders", {})
                        if target_orders:
                            for ticker, amount in target_orders.items():
                                side = "BUY" if amount > 0 else "SELL"
                                st.write(f"- {ticker}: {side} ${abs(amount):.2f}")
                        else:
                            st.caption("No target orders")

                    with col2:
                        st.markdown("**Executed Orders**")
                        executed_orders = tx.get("executed_orders", [])
                        if executed_orders:
                            for order in executed_orders:
                                status_emoji = "✅" if order.get("status") == "success" else "🔴"
                                ticker = order.get("ticker", "?")
                                side = order.get("side", "?")
                                amount = order.get("amount_usd", 0)
                                st.write(f"- {status_emoji} {ticker}: {side} ${abs(amount):.2f}")
                        else:
                            st.caption("No executed orders")

                    # Reconciliation notes
                    if tx.get("reconciliation_notes"):
                        st.markdown("**Reconciliation Notes**")
                        st.text(tx["reconciliation_notes"])

                    # Transaction ID
                    st.caption(f"Transaction ID: {tx.get('transaction_id', 'Unknown')}")

            except Exception as e:
                message, severity = translate_exception(e, context=f"Reading transaction log {log_file.name}")
                handle_error_display(message, severity)

except Exception as e:
    message, severity = translate_exception(e, context="Loading transaction logs")
    handle_error_display(message, severity)

st.divider()

# Footer
st.caption("""
💡 **About Monitoring**: This dashboard provides real-time insights into Dalio Lite's operation.
Health checks run automatically and alert you to issues. Transaction logs provide an audit trail
for all rebalancing operations.
""")

st.caption("""
🔄 **Refresh**: This page auto-refreshes with Streamlit's rerun mechanism.
For manual refresh, use the refresh button in your browser or press 'R' in the Streamlit interface.
""")
