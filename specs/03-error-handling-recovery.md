# Error Handling & Recovery Specification

**Document:** 03-error-handling-recovery.md
**Project:** Dalio Lite Production Hardening
**Date:** 2026-02-17
**Status:** Final
**Dependencies:** 01-testing-infrastructure.md (error paths must be testable)
**Enables:** 04-observability-monitoring.md (error metrics), 07-production-checklist.md (error handling validation)

---

## Overview

This document defines comprehensive error handling and recovery mechanisms for Dalio Lite, addressing the **critical gap** identified in audit1 where order execution ignores failures and can leave portfolios in unintended states.

**Why This Exists:**
- Current state: Partial rebalance failures go undetected
- Risk: Portfolio left in limbo (e.g., sold VTI but failed to buy TLT = unintended 30% cash position)
- Financial impact: Misallocated portfolio for 30+ days until next rebalance
- Audit1 severity: Medium (error handling insufficient)

**What This Covers:**
- Order execution error detection and propagation
- Partial failure recovery strategies
- Transaction logging for audit trail
- Retry logic with exponential backoff
- User notification on failures
- Reconciliation procedures

**What This Does NOT Cover:**
- Network retry logic (handled by Alpaca SDK)
- Alpaca API outage compensation (out of our control)
- Market-wide circuit breakers (handled by exchanges)

---

## Architecture

### Error Taxonomy

```
Portfolio Rebalancing Errors
│
├─ PRE-EXECUTION ERRORS (Fail Fast)
│  ├─ Configuration Error (invalid allocation)
│  ├─ API Authentication Error (bad keys)
│  ├─ Circuit Breaker Triggered (risk limit exceeded)
│  └─ Lock Acquisition Timeout (concurrency conflict)
│      → Response: Abort, log, notify user
│
├─ EXECUTION ERRORS (Recoverable)
│  ├─ Single Order Failure
│  │  ├─ Insufficient Buying Power
│  │  ├─ Symbol Not Found (ticker delisted)
│  │  ├─ Market Closed
│  │  └─ Rate Limit (429 Too Many Requests)
│  │      → Response: Retry with backoff or skip order
│  │
│  └─ Partial Rebalance Failure
│      ├─ Sells Succeeded, Buys Failed
│      ├─ Some Buys Succeeded, Others Failed
│      └─ Orders Accepted but Not Filled
│          → Response: Log transaction, attempt completion, notify user
│
└─ POST-EXECUTION ERRORS (Audit)
   ├─ State Save Failure (disk full)
   ├─ Notification Send Failure (email down)
   └─ Reconciliation Mismatch (expected vs actual)
       → Response: Log error, manual review required
```

---

### Recovery Strategy Flow

```
┌──────────────────────────┐
│  Rebalance Initiated     │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  Pre-Flight Checks       │
│  • Config valid?         │
│  • API accessible?       │
│  • Circuit breakers OK?  │
└────────────┬─────────────┘
             │
     [PASS]  │  [FAIL] ──────────► Abort, Log, Notify
             ▼
┌──────────────────────────┐
│  Begin Transaction Log   │
│  transaction_id: UUID    │
│  timestamp: now          │
│  target_orders: [...]    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  Execute SELL Orders     │
│  (free up cash first)    │
└────────────┬─────────────┘
             │
     [SUCCESS]│  [FAILURE]
             │         │
             │         ▼
             │    ┌───────────────────┐
             │    │ Retry (3x)        │
             │    │ with backoff      │
             │    └────────┬──────────┘
             │             │
             │    [STILL FAIL]────► Log, Notify, Continue with Buys Anyway
             │                      (cash available from successful sells)
             ▼
┌──────────────────────────┐
│  Execute BUY Orders      │
│  (use freed cash)        │
└────────────┬─────────────┘
             │
     [SUCCESS]│  [FAILURE]
             │         │
             │         ▼
             │    ┌───────────────────┐
             │    │ Retry (3x)        │
             │    │ with backoff      │
             │    └────────┬──────────┘
             │             │
             │    [STILL FAIL]────► Log, Notify, Mark Incomplete
             │                      (reconcile on next run)
             ▼
┌──────────────────────────┐
│  Reconciliation Check    │
│  • Expected vs Actual    │
│  • All orders filled?    │
│  • Drift within bounds?  │
└────────────┬─────────────┘
             │
     [MATCH] │  [MISMATCH]────► Log Warning, Notify User
             ▼                   (manual review required)
┌──────────────────────────┐
│  Update State & Notify   │
│  • Save last_rebalance   │
│  • Send success email    │
│  • Close transaction log │
└──────────────────────────┘
```

---

## Specification

### 1. Enhanced Order Execution with Error Handling

**Current Implementation (Unsafe):**

```python
# dalio_lite.py:310-337 (BEFORE)
def _execute_order(self, ticker: str, amount_usd: float, side: OrderSide) -> bool:
    try:
        # ... order submission logic ...
        return True
    except Exception as e:
        self.logger.error(f"✗ Order failed: {side.name} {ticker} - {e}")
        return False  # ← Return value IGNORED by caller!
```

**New Implementation (Safe):**

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time

class OrderStatus(Enum):
    """Order execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"

@dataclass
class OrderResult:
    """Result of order execution attempt."""
    ticker: str
    side: str  # "buy" or "sell"
    amount_usd: float
    status: OrderStatus
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

def _execute_order(
    self,
    ticker: str,
    amount_usd: float,
    side: OrderSide,
    max_retries: int = 3
) -> OrderResult:
    """
    Execute a single market order with retry logic.

    Args:
        ticker: Stock symbol (e.g., "VTI")
        amount_usd: Dollar amount to trade
        side: OrderSide.BUY or OrderSide.SELL
        max_retries: Number of retry attempts (default: 3)

    Returns:
        OrderResult with status and details

    Raises:
        Never raises - all errors captured in OrderResult
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            # Get current price
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=[ticker])
            quotes = self.data_client.get_stock_latest_quote(quote_request)
            price = float(quotes[ticker].ask_price if side == OrderSide.BUY else quotes[ticker].bid_price)

            # Create order request
            order_data = MarketOrderRequest(
                symbol=ticker,
                notional=amount_usd,
                side=side,
                time_in_force=TimeInForce.DAY
            )

            # Submit order
            order = self.trading_client.submit_order(order_data)

            self.logger.info(
                f"✓ Order SUCCESS: {side.name} ${amount_usd:.2f} of {ticker} "
                f"(order_id: {order.id}, attempt: {attempt + 1}/{max_retries + 1})"
            )

            return OrderResult(
                ticker=ticker,
                side=side.name,
                amount_usd=amount_usd,
                status=OrderStatus.SUCCESS,
                order_id=order.id,
                retry_count=attempt
            )

        except Exception as e:
            last_error = str(e)
            self.logger.warning(
                f"✗ Order FAILED: {side.name} {ticker} - {e} "
                f"(attempt: {attempt + 1}/{max_retries + 1})"
            )

            # Check if error is retryable
            if self._is_retryable_error(e):
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    backoff = 2 ** attempt
                    self.logger.info(f"Retrying in {backoff}s...")
                    time.sleep(backoff)
                    continue
            else:
                # Non-retryable error (e.g., symbol not found)
                self.logger.error(f"Non-retryable error, skipping retries")
                break

    # All retries exhausted or non-retryable error
    return OrderResult(
        ticker=ticker,
        side=side.name,
        amount_usd=amount_usd,
        status=OrderStatus.FAILED,
        error_message=last_error,
        retry_count=max_retries
    )

def _is_retryable_error(self, error: Exception) -> bool:
    """
    Determine if an API error is retryable.

    Retryable errors:
    - Network timeouts
    - 5xx server errors
    - 429 rate limit
    - Temporary API unavailability

    Non-retryable errors:
    - 401 unauthorized (bad API keys)
    - 404 symbol not found
    - 400 bad request (invalid order)
    - Insufficient buying power
    """
    error_str = str(error).lower()

    # Retryable patterns
    retryable_patterns = [
        "timeout",
        "503",  # Service unavailable
        "500",  # Internal server error
        "502",  # Bad gateway
        "429",  # Too many requests
        "connection",
        "network"
    ]

    # Non-retryable patterns
    non_retryable_patterns = [
        "401",  # Unauthorized
        "403",  # Forbidden
        "404",  # Not found
        "400",  # Bad request
        "insufficient",  # Insufficient buying power
        "invalid symbol"
    ]

    # Check non-retryable first (takes precedence)
    if any(pattern in error_str for pattern in non_retryable_patterns):
        return False

    # Check retryable
    if any(pattern in error_str for pattern in retryable_patterns):
        return True

    # Default: assume retryable (conservative approach)
    return True
```

---

### 2. Transaction Logging

**New Class:** `TransactionLog`

**File:** `transaction_log.py` (new file)

```python
"""Transaction logging for rebalance operations."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import uuid

@dataclass
class TransactionLogEntry:
    """Single transaction log entry."""
    transaction_id: str
    timestamp: str
    operation: str  # "rebalance", "force_rebalance", "autopilot_check"
    target_orders: Dict[str, float]  # ticker -> amount_usd
    executed_orders: List[Dict]  # List of OrderResult dicts
    status: str  # "completed", "partial", "failed", "aborted"
    error_message: Optional[str] = None
    reconciliation_notes: Optional[str] = None

class TransactionLogger:
    """
    Logs all rebalancing operations for audit trail.

    Purpose:
    - Track what was intended vs what actually executed
    - Provide audit trail for financial transactions
    - Enable reconciliation after partial failures
    - Support debugging and root cause analysis
    """

    def __init__(self, log_dir: str = "state/transactions"):
        """
        Initialize transaction logger.

        Args:
            log_dir: Directory to store transaction logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def begin_transaction(
        self,
        operation: str,
        target_orders: Dict[str, float]
    ) -> str:
        """
        Begin a new transaction.

        Args:
            operation: Operation type (e.g., "rebalance")
            target_orders: Intended orders {ticker: amount_usd}

        Returns:
            transaction_id: UUID for this transaction
        """
        transaction_id = str(uuid.uuid4())

        entry = TransactionLogEntry(
            transaction_id=transaction_id,
            timestamp=datetime.now().isoformat(),
            operation=operation,
            target_orders=target_orders,
            executed_orders=[],
            status="in_progress"
        )

        self._save_log(entry)
        return transaction_id

    def record_order(
        self,
        transaction_id: str,
        order_result: 'OrderResult'
    ):
        """
        Record executed order in transaction log.

        Args:
            transaction_id: Transaction UUID
            order_result: Result of order execution
        """
        entry = self._load_log(transaction_id)

        # Append order result
        entry.executed_orders.append({
            'ticker': order_result.ticker,
            'side': order_result.side,
            'amount_usd': order_result.amount_usd,
            'status': order_result.status.value,
            'order_id': order_result.order_id,
            'error_message': order_result.error_message,
            'retry_count': order_result.retry_count,
            'timestamp': datetime.now().isoformat()
        })

        self._save_log(entry)

    def complete_transaction(
        self,
        transaction_id: str,
        status: str,  # "completed", "partial", "failed"
        reconciliation_notes: Optional[str] = None
    ):
        """
        Mark transaction as complete.

        Args:
            transaction_id: Transaction UUID
            status: Final status
            reconciliation_notes: Notes from reconciliation check
        """
        entry = self._load_log(transaction_id)
        entry.status = status
        entry.reconciliation_notes = reconciliation_notes
        self._save_log(entry)

    def _save_log(self, entry: TransactionLogEntry):
        """Save transaction log entry to file."""
        log_file = self.log_dir / f"{entry.transaction_id}.json"

        with open(log_file, 'w') as f:
            json.dump(asdict(entry), f, indent=2)

    def _load_log(self, transaction_id: str) -> TransactionLogEntry:
        """Load transaction log entry from file."""
        log_file = self.log_dir / f"{transaction_id}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        return TransactionLogEntry(**data)

    def get_recent_transactions(self, limit: int = 10) -> List[TransactionLogEntry]:
        """
        Get recent transactions (for dashboard display).

        Args:
            limit: Max number of transactions to return

        Returns:
            List of transactions, newest first
        """
        log_files = sorted(self.log_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

        transactions = []
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
                transactions.append(TransactionLogEntry(**data))
            except Exception:
                continue  # Skip corrupted logs

        return transactions
```

---

### 3. Enhanced Rebalance Execution with Recovery

**Modified Method:** `execute_rebalance()`

```python
def execute_rebalance(self, dry_run: bool = False) -> bool:
    """
    Execute rebalancing with comprehensive error handling.

    Returns:
        True if fully successful, False if any failures
    """
    self.logger.info("="*60)
    self.logger.info("EXECUTING REBALANCE")
    self.logger.info("="*60)

    # Calculate orders
    orders = self.calculate_rebalance_orders()

    # Log plan
    self.logger.info("Rebalance Plan:")
    total_buys = sum(amt for amt in orders.values() if amt > 0)
    total_sells = abs(sum(amt for amt in orders.values() if amt < 0))

    for ticker, amount in orders.items():
        if amount == 0:
            self.logger.info(f"  {ticker}: No change")
        elif amount > 0:
            self.logger.info(f"  {ticker}: BUY ${amount:.2f}")
        else:
            self.logger.info(f"  {ticker}: SELL ${abs(amount):.2f}")

    self.logger.info(f"Total to sell: ${total_sells:.2f}")
    self.logger.info(f"Total to buy: ${total_buys:.2f}")

    if dry_run:
        self.logger.info("DRY RUN - No orders executed")
        return True

    # Begin transaction logging
    tx_logger = TransactionLogger()
    tx_id = tx_logger.begin_transaction(
        operation="rebalance",
        target_orders=orders
    )

    # Track results
    sell_results = []
    buy_results = []
    all_success = True

    try:
        # Execute SELL orders first (free up cash)
        self.logger.info("\n📤 Executing SELL orders...")
        for ticker, amount in sorted(orders.items(), key=lambda x: x[1]):
            if amount < 0:  # Sell
                result = self._execute_order(ticker, abs(amount), OrderSide.SELL)
                sell_results.append(result)
                tx_logger.record_order(tx_id, result)

                if result.status != OrderStatus.SUCCESS:
                    self.logger.error(f"SELL order failed: {ticker}")
                    all_success = False
                    # Continue to next order (don't abort all sells)

        # Execute BUY orders second (use freed cash)
        self.logger.info("\n📥 Executing BUY orders...")
        for ticker, amount in sorted(orders.items(), key=lambda x: x[1], reverse=True):
            if amount > 0:  # Buy
                result = self._execute_order(ticker, amount, OrderSide.BUY)
                buy_results.append(result)
                tx_logger.record_order(tx_id, result)

                if result.status != OrderStatus.SUCCESS:
                    self.logger.error(f"BUY order failed: {ticker}")
                    all_success = False
                    # Continue to next order

        # Reconciliation check
        self.logger.info("\n🔍 Reconciliation Check...")
        reconciliation_notes = self._reconcile_orders(orders, sell_results + buy_results)

        if all_success:
            # Update state only if ALL orders succeeded
            self.last_rebalance = datetime.now()
            self._save_rebalance_date(self.last_rebalance)

            tx_logger.complete_transaction(tx_id, "completed", reconciliation_notes)

            self.logger.info("✅ Rebalance COMPLETE - All orders succeeded")
            self._notify("Portfolio rebalanced successfully")

        else:
            # Partial failure
            tx_logger.complete_transaction(tx_id, "partial", reconciliation_notes)

            self.logger.warning("⚠️ Rebalance PARTIAL - Some orders failed")
            self.logger.warning(f"Transaction ID: {tx_id}")
            self.logger.warning("Review transaction log for details")

            self._notify(
                f"⚠️ Rebalance partially failed. "
                f"Some orders did not execute. "
                f"Transaction ID: {tx_id}. "
                f"Portfolio may require manual adjustment."
            )

            # Don't update last_rebalance (allow retry on next check)

        self.logger.info("="*60)
        return all_success

    except Exception as e:
        # Unexpected error during rebalance
        self.logger.exception(f"❌ Rebalance FAILED with unexpected error: {e}")

        tx_logger.complete_transaction(
            tx_id,
            "failed",
            f"Unexpected error: {e}"
        )

        self._notify(
            f"❌ Rebalance failed: {e}. "
            f"Transaction ID: {tx_id}. "
            f"Manual review required."
        )

        return False

def _reconcile_orders(
    self,
    target_orders: Dict[str, float],
    results: List['OrderResult']
) -> str:
    """
    Reconcile target orders vs actual execution.

    Args:
        target_orders: Intended orders {ticker: amount_usd}
        results: List of OrderResult from execution

    Returns:
        Human-readable reconciliation notes
    """
    notes = []

    # Group results by ticker
    results_by_ticker = {}
    for result in results:
        if result.ticker not in results_by_ticker:
            results_by_ticker[result.ticker] = []
        results_by_ticker[result.ticker].append(result)

    # Check each target order
    for ticker, target_amount in target_orders.items():
        if target_amount == 0:
            continue  # No order needed

        ticker_results = results_by_ticker.get(ticker, [])

        if not ticker_results:
            notes.append(f"❌ {ticker}: No execution (target: ${abs(target_amount):.2f})")

        elif all(r.status == OrderStatus.SUCCESS for r in ticker_results):
            notes.append(f"✅ {ticker}: Success (${abs(target_amount):.2f})")

        else:
            failed = [r for r in ticker_results if r.status == OrderStatus.FAILED]
            notes.append(
                f"⚠️ {ticker}: Partial failure - {len(failed)} orders failed "
                f"(target: ${abs(target_amount):.2f})"
            )

    # Summary
    total_success = sum(1 for r in results if r.status == OrderStatus.SUCCESS)
    total_failed = sum(1 for r in results if r.status == OrderStatus.FAILED)

    summary = f"\n📊 Summary: {total_success} succeeded, {total_failed} failed"
    notes.insert(0, summary)

    return "\n".join(notes)
```

---

### 4. User Notification on Failures

**Enhanced Notification:**

```python
def _notify(self, message: str):
    """Send notification (enhanced with failure context)."""
    if not self.config['notifications']['enabled']:
        return

    method = self.config['notifications']['method']

    if method == 'email':
        try:
            from send_notification import send_rebalance_notification
            account = self.trading_client.get_account()
            portfolio_value = float(account.portfolio_value)

            # Determine notification type from message
            if "failed" in message.lower() or "partial" in message.lower():
                notification_type = "failure"
            elif "circuit breaker" in message.lower():
                notification_type = "circuit_breaker"
            else:
                notification_type = "success"

            send_rebalance_notification(
                notification_type=notification_type,
                message=message,
                portfolio_value=portfolio_value
            )

        except Exception as e:
            self.logger.warning(f"Failed to send email notification: {e}")

    elif method == 'console':
        print(f"\n📢 NOTIFICATION: {message}\n")

    elif method == 'file':
        with open('notifications.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} | {message}\n")
```

**New Email Template (send_notification.py):**

```python
def send_rebalance_notification(
    notification_type: str,  # "success", "failure", "circuit_breaker"
    message: str,
    portfolio_value: float
):
    """Send rebalance notification email."""

    if notification_type == "failure":
        subject = "⚠️ Rebalance Partially Failed"
        body_html = f"""
        <h2 style='color: #f56565;'>⚠️ Rebalance Incomplete</h2>

        <div style='background: #fed7d7; padding: 1rem; border-left: 4px solid #f56565; border-radius: 4px; margin: 1rem 0;'>
            <p style='margin: 0; color: #742a2a;'>{message}</p>
        </div>

        <p><strong>What happened:</strong> Some orders failed to execute. Your portfolio may be temporarily misallocated.</p>

        <p><strong>Current Portfolio Value:</strong> ${portfolio_value:,.2f}</p>

        <p><strong>What to do:</strong></p>
        <ul>
            <li>Review transaction logs in dashboard</li>
            <li>Check if manual rebalancing needed</li>
            <li>System will retry on next daily check</li>
        </ul>

        <p><a href='http://localhost:8502' style='display: inline-block; background: #f56565; color: white;
        padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin-top: 1rem;'>
        View Dashboard</a></p>
        """

    elif notification_type == "success":
        subject = "✅ Rebalance Successful"
        body_html = f"""
        <h2 style='color: #48bb78;'>✅ Rebalance Complete</h2>

        <p>Your portfolio was successfully rebalanced to target allocation.</p>

        <div style='background: white; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <p style='font-size: 1.5rem; margin: 0;'><strong>${portfolio_value:,.2f}</strong></p>
            <p style='color: #718096; margin: 0.25rem 0 0 0;'>Current Portfolio Value</p>
        </div>

        <p><a href='http://localhost:8502' style='display: inline-block; background: #667eea; color: white;
        padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin-top: 1rem;'>
        View Dashboard</a></p>
        """

    else:  # circuit_breaker
        subject = "🛑 Circuit Breaker Triggered"
        body_html = f"""
        <h2 style='color: #f56565;'>⚠️ Circuit Breaker Activated</h2>

        <div style='background: #fed7d7; padding: 1rem; border-left: 4px solid #f56565; border-radius: 4px; margin: 1rem 0;'>
            <p style='margin: 0; color: #742a2a;'>{message}</p>
        </div>

        <p>Rebalancing paused to protect your portfolio during unusual conditions.</p>
        """

    send_email(subject, body_html, to_email=get_user_email())
```

---

## Verification Strategy

### Unit Tests

**Test File:** `tests/unit/test_error_handling.py`

```python
import pytest
from dalio_lite import DalioLite, OrderStatus, OrderResult
from alpaca.trading.enums import OrderSide

@pytest.mark.unit
def test_order_retry_on_timeout(mocker):
    """Test order retries on timeout error."""
    # Mock API to fail twice, then succeed
    call_count = 0

    def mock_submit_order(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("timeout")
        return mocker.Mock(id="order-123", status="accepted")

    mocker.patch('dalio_lite.TradingClient.submit_order', side_effect=mock_submit_order)

    dalio = DalioLite()
    result = dalio._execute_order("VTI", 1000.0, OrderSide.BUY, max_retries=3)

    assert result.status == OrderStatus.SUCCESS
    assert result.retry_count == 2  # Failed twice, succeeded on 3rd attempt
    assert call_count == 3

@pytest.mark.unit
def test_order_gives_up_after_max_retries(mocker):
    """Test order gives up after max retries exhausted."""
    # Mock API to always fail
    mocker.patch('dalio_lite.TradingClient.submit_order', side_effect=Exception("500 server error"))

    dalio = DalioLite()
    result = dalio._execute_order("VTI", 1000.0, OrderSide.BUY, max_retries=3)

    assert result.status == OrderStatus.FAILED
    assert result.retry_count == 3
    assert "500 server error" in result.error_message

@pytest.mark.unit
def test_non_retryable_error_skips_retries(mocker):
    """Test non-retryable error (401 unauthorized) skips retries."""
    # Mock API to return 401
    mocker.patch('dalio_lite.TradingClient.submit_order', side_effect=Exception("401 unauthorized"))

    dalio = DalioLite()
    result = dalio._execute_order("VTI", 1000.0, OrderSide.BUY, max_retries=3)

    assert result.status == OrderStatus.FAILED
    assert result.retry_count == 0  # Didn't retry
    assert "401" in result.error_message
```

---

### Integration Tests

**Test File:** `tests/integration/test_partial_failure_recovery.py`

```python
import pytest
from dalio_lite import DalioLite
from transaction_log import TransactionLogger

@pytest.mark.integration
def test_partial_rebalance_sell_succeeds_buy_fails(mocker):
    """Test that sell succeeds but buy fails - transaction logged."""
    # Mock: Sell succeeds, Buy fails
    def mock_execute_order(ticker, amount, side):
        if side.name == "SELL":
            return OrderResult(ticker, "SELL", amount, OrderStatus.SUCCESS, order_id="sell-123")
        else:  # BUY
            return OrderResult(ticker, "BUY", amount, OrderStatus.FAILED, error_message="insufficient funds")

    mocker.patch.object(DalioLite, '_execute_order', side_effect=mock_execute_order)

    dalio = DalioLite()
    success = dalio.execute_rebalance(dry_run=False)

    # Should return False (partial failure)
    assert success is False

    # Check transaction log
    tx_logger = TransactionLogger()
    recent_tx = tx_logger.get_recent_transactions(limit=1)[0]

    assert recent_tx.status == "partial"
    assert len(recent_tx.executed_orders) > 0
    assert any(order['status'] == 'failed' for order in recent_tx.executed_orders)
```

---

## Benefits

1. **Financial Safety:** Partial failures detected and logged
2. **Audit Trail:** Transaction logs provide complete history
3. **Automatic Recovery:** Retry logic handles transient errors
4. **User Awareness:** Clear notifications on failures
5. **Debuggability:** Detailed logs for root cause analysis

---

## Expectations

### Immediate (Week 1)
- ✅ Enhanced order execution implemented
- ✅ Transaction logging functional
- ✅ Retry logic tested

### Short-term (Month 1)
- ✅ Zero undetected partial failures
- ✅ All failures logged and notified
- ✅ Transaction logs reviewed weekly

### Long-term (Month 3+)
- ✅ Retry logic prevents >90% of transient failures
- ✅ Transaction logs enable debugging
- ✅ User confidence in system reliability

---

## Risks & Mitigations

### Risk 1: Retry Logic Too Aggressive

**Probability:** Low
**Impact:** Medium (API rate limit)

**Mitigation:**
- Max 3 retries (reasonable limit)
- Exponential backoff (1s, 2s, 4s)
- Detect rate limit errors and back off further

---

### Risk 2: Transaction Logs Fill Disk

**Probability:** Medium (over time)
**Impact:** Low (disk space)

**Mitigation:**
- Log rotation (keep last 90 days)
- Compress old logs
- Monitor disk usage

---

## Results Criteria

- [ ] All order failures logged in transaction log
- [ ] Retry logic handles transient errors
- [ ] Partial failures notified to user
- [ ] Transaction logs accessible in dashboard
- [ ] Zero undetected partial rebalance failures

---

**Status:** Ready for implementation
**Next Document:** 04-observability-monitoring.md
