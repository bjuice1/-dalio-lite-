"""
Dalio Lite - Simplified All Weather Portfolio Automation

A learning-focused, production-ready implementation of Ray Dalio's All Weather
portfolio strategy for small accounts ($10K-50K).

Core Philosophy:
- Simple beats complex
- Discipline beats emotion
- Learning beats returns (at this scale)

Author: Built for educational purposes
License: MIT
"""

import os
import yaml
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Production hardening imports
from state_lock import StateLockManager
from metrics_collector import metrics
from backup_manager import BackupManager
from transaction_log import TransactionLogger
from enum import Enum
from dataclasses import dataclass

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestQuoteRequest
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("⚠️  alpaca-py not installed. Run: pip install alpaca-py")


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

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'ticker': self.ticker,
            'side': self.side,
            'amount_usd': self.amount_usd,
            'status': self.status.value,
            'order_id': self.order_id,
            'error_message': self.error_message,
            'retry_count': self.retry_count
        }


class DalioLite:
    """
    Simplified All Weather portfolio manager

    Implements:
    - Static allocation with drift-based rebalancing
    - Risk management (circuit breakers, position limits)
    - Paper trading safety
    - Performance tracking
    """

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize Dalio Lite system"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_broker()
        self.last_rebalance = self._load_last_rebalance_date()

        # Initialize production hardening systems
        self.lock_manager = StateLockManager(
            lock_file_path="state/dalio_lite.lock",
            timeout=30
        )

        self.backup_manager = BackupManager(
            backup_dir="backups",
            retention_days=30,
            cloud_enabled=False
        )

        self.transaction_logger = TransactionLogger(
            log_dir="state/transactions"
        )

        self.logger.info("="*60)
        self.logger.info("DALIO LITE INITIALIZED")
        self.logger.info(f"Mode: {'PAPER TRADING' if self.config['mode']['paper_trading'] else 'LIVE TRADING'}")
        self.logger.info(f"Target Allocation: {self.config['allocation']}")
        self.logger.info(f"Concurrency control: ENABLED (lock timeout: 30s)")
        self.logger.info(f"Metrics collection: ENABLED")
        self.logger.info(f"Automatic backups: ENABLED (30-day retention)")
        self.logger.info(f"Transaction logging: ENABLED")
        self.logger.info("="*60)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Validate allocation sums to 1.0
        total = sum(config['allocation'].values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Allocation must sum to 1.0, got {total}")

        return config

    def _setup_logging(self):
        """Configure logging"""
        log_level = getattr(logging, self.config['logging']['level'])
        log_file = self.config['logging']['file']

        # Create logs directory
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        # Configure logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _setup_broker(self):
        """Initialize broker connection (Alpaca)"""
        if not ALPACA_AVAILABLE:
            raise ImportError("alpaca-py required. Install: pip install alpaca-py")

        # Get API keys from environment
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')

        if not api_key or not secret_key:
            raise ValueError(
                "Alpaca API keys not found. Set environment variables:\n"
                "  export ALPACA_API_KEY='your_key'\n"
                "  export ALPACA_SECRET_KEY='your_secret'\n"
                "Get free paper trading keys at: https://alpaca.markets"
            )

        # Initialize clients
        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=self.config['mode']['paper_trading']
        )

        self.data_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key
        )

        # Verify connection
        try:
            account = self.trading_client.get_account()
            self.logger.info(f"Connected to Alpaca: ${float(account.cash):.2f} cash, "
                           f"${float(account.portfolio_value):.2f} total value")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Alpaca: {e}")

    def _load_last_rebalance_date(self) -> Optional[datetime]:
        """Load last rebalance timestamp from state file"""
        state_file = Path("state/last_rebalance.json")
        if state_file.exists():
            with open(state_file, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data['timestamp'])
        return None

    def _save_rebalance_date(self, timestamp: datetime):
        """Save rebalance timestamp to state file (atomic write with backup)"""
        state_file = Path("state/last_rebalance.json")
        temp_file = Path("state/.last_rebalance.json.tmp")

        # Ensure directory exists
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first (atomic operation)
        with open(temp_file, 'w') as f:
            json.dump({'timestamp': timestamp.isoformat()}, f)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk

        # Atomic rename (replaces old file)
        temp_file.replace(state_file)

        # Create backup
        self.backup_manager.backup_state_file(str(state_file))

        self.logger.debug(f"State saved and backed up: {timestamp.isoformat()}")

    def get_current_positions(self) -> Dict[str, float]:
        """
        Get current portfolio positions as % of total value

        Returns:
            Dict mapping ticker -> percentage (0.0 to 1.0)
        """
        account = self.trading_client.get_account()
        portfolio_value = float(account.portfolio_value)

        if portfolio_value == 0:
            self.logger.warning("Portfolio value is $0 - no positions")
            return {}

        positions = self.trading_client.get_all_positions()

        current = {}
        for position in positions:
            ticker = position.symbol
            value = float(position.market_value)
            pct = value / portfolio_value
            current[ticker] = pct

        # Add tickers we track but don't have positions in
        for ticker in self.config['allocation'].keys():
            if ticker not in current:
                current[ticker] = 0.0

        return current

    def calculate_drift(self) -> Dict[str, float]:
        """
        Calculate drift from target allocation

        Returns:
            Dict mapping ticker -> drift amount (negative = underweight)
        """
        current = self.get_current_positions()
        target = self.config['allocation']

        drift = {}
        for ticker, target_pct in target.items():
            current_pct = current.get(ticker, 0.0)
            drift[ticker] = current_pct - target_pct

        return drift

    def needs_rebalancing(self) -> Tuple[bool, str]:
        """
        Check if portfolio needs rebalancing

        Returns:
            (needs_rebalance: bool, reason: str)
        """
        # Check minimum time between rebalances
        if self.last_rebalance:
            min_days = self.config['rebalancing']['min_days_between']
            days_since = (datetime.now() - self.last_rebalance).days
            if days_since < min_days:
                return False, f"Only {days_since} days since last rebalance (min: {min_days})"

        # Check drift threshold
        drift = self.calculate_drift()
        max_drift = max(abs(d) for d in drift.values())
        threshold = self.config['rebalancing']['drift_threshold']

        if max_drift > threshold:
            # Find which ticker(s) triggered
            triggers = [t for t, d in drift.items() if abs(d) > threshold]
            return True, f"Drift {max_drift:.1%} exceeds threshold {threshold:.1%} ({', '.join(triggers)})"

        return False, f"All positions within {threshold:.1%} of target (max drift: {max_drift:.1%})"

    def calculate_rebalance_orders(self) -> Dict[str, float]:
        """
        Calculate orders needed to rebalance to target allocation

        Returns:
            Dict mapping ticker -> $ amount to buy (positive) or sell (negative)
        """
        account = self.trading_client.get_account()
        portfolio_value = float(account.portfolio_value)

        current = self.get_current_positions()
        target = self.config['allocation']

        orders = {}
        for ticker, target_pct in target.items():
            current_pct = current.get(ticker, 0.0)

            # Calculate target $ value
            target_value = portfolio_value * target_pct
            current_value = portfolio_value * current_pct

            # Order amount (positive = buy, negative = sell)
            order_amount = target_value - current_value

            # Filter out tiny orders
            min_trade = self.config['rebalancing']['min_trade_usd']
            if abs(order_amount) < min_trade:
                order_amount = 0.0

            orders[ticker] = order_amount

        return orders

    def execute_rebalance(self, dry_run: bool = False) -> bool:
        """
        Execute rebalancing orders (with concurrency control and metrics)

        Args:
            dry_run: If True, calculate but don't execute orders

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        metrics.increment("rebalance_total")

        # Check if lock already held (called from run_daily_check)
        if self.lock_manager.is_locked:
            # Lock already held (nested call)
            return self._execute_rebalance_impl(dry_run, start_time)
        else:
            # Lock not held (direct call from Dashboard)
            try:
                with self.lock_manager.acquire():
                    return self._execute_rebalance_impl(dry_run, start_time)
            except RuntimeError as e:
                self.logger.error(f"Rebalance aborted: {e}")
                metrics.increment("rebalance_failed")
                metrics.flush()
                return False

    def _execute_rebalance_impl(self, dry_run: bool = False, start_time: float = None) -> bool:
        """Internal implementation of rebalance (called within lock context)"""
        if start_time is None:
            start_time = time.time()

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
        tx_id = self.transaction_logger.begin_transaction(
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
                    self.transaction_logger.record_order(tx_id, result.to_dict())

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
                    self.transaction_logger.record_order(tx_id, result.to_dict())

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

                self.transaction_logger.complete_transaction(tx_id, "completed", reconciliation_notes)

                metrics.increment("rebalance_success")
                duration = time.time() - start_time
                metrics.record_duration("rebalance_duration_seconds", duration)
                self._update_metrics()
                metrics.flush()

                self.logger.info("✅ Rebalance COMPLETE - All orders succeeded")
                self._notify("Portfolio rebalanced successfully")

            else:
                # Partial failure
                self.transaction_logger.complete_transaction(tx_id, "partial", reconciliation_notes)

                metrics.increment("rebalance_partial")
                metrics.flush()

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

            self.transaction_logger.complete_transaction(
                tx_id,
                "failed",
                f"Unexpected error: {e}"
            )

            metrics.increment("rebalance_failed")
            metrics.flush()

            self._notify(
                f"❌ Rebalance failed: {e}. "
                f"Transaction ID: {tx_id}. "
                f"Manual review required."
            )

            return False

    def _reconcile_orders(
        self,
        target_orders: Dict[str, float],
        results: List[OrderResult]
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

    def _update_metrics(self):
        """Update gauge metrics with current state"""
        try:
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
        except Exception as e:
            self.logger.warning(f"Failed to update metrics: {e}")

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
        """
        start_time = time.time()
        last_error = None

        metrics.increment("orders_executed")
        metrics.increment("api_calls_total")

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

                metrics.increment("orders_success")
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_duration("order_execution_duration_ms", duration_ms)

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
        metrics.increment("orders_failed")
        metrics.increment("api_errors")

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

        # Non-retryable patterns (check first - takes precedence)
        non_retryable_patterns = [
            "401", "403", "404", "400",
            "insufficient", "invalid symbol"
        ]

        if any(pattern in error_str for pattern in non_retryable_patterns):
            return False

        # Retryable patterns
        retryable_patterns = [
            "timeout", "503", "500", "502", "429",
            "connection", "network"
        ]

        if any(pattern in error_str for pattern in retryable_patterns):
            return True

        # Default: assume retryable (conservative approach)
        return True

    def check_circuit_breakers(self) -> Tuple[bool, str]:
        """
        Check risk management circuit breakers (with metrics)

        Returns:
            (triggered: bool, reason: str)
        """
        account = self.trading_client.get_account()
        triggered = False
        reason = "All circuit breakers clear"

        # Check drawdown from high water mark (simplified - just check vs. initial)
        # In production, track high water mark over time
        equity = float(account.equity)
        initial_equity = float(account.last_equity)  # Previous day close

        if initial_equity > 0:
            daily_return = (equity - initial_equity) / initial_equity
            max_daily_loss = self.config['risk']['max_daily_loss']

            if daily_return <= -max_daily_loss:
                triggered = True
                reason = f"Daily loss {daily_return:.1%} exceeds max {max_daily_loss:.1%}"

        if triggered:
            metrics.increment("circuit_breaker_triggered")

        return triggered, reason

    def run_daily_check(self, dry_run: bool = False):
        """
        Main entry point - run daily portfolio check (with concurrency control)

        This should be called by a cron job or scheduler daily
        """
        # Record AutoPilot execution
        metrics.set_timestamp("autopilot_last_run")

        # Acquire lock before any state operations
        try:
            with self.lock_manager.acquire():
                self._run_daily_check_impl(dry_run)

        except RuntimeError as e:
            # Lock acquisition failed (timeout)
            self.logger.error(f"Daily check aborted: {e}")
            self._notify(f"Daily check failed: {e}")
            metrics.increment("daily_check_failed")
            return

        finally:
            # Always flush metrics
            metrics.flush()

    def _run_daily_check_impl(self, dry_run: bool = False):
        """Internal implementation of daily check (called within lock context)"""
        self.logger.info("\n" + "="*60)
        self.logger.info(f"DAILY CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.logger.info("="*60)

        # 1. Check circuit breakers
        triggered, reason = self.check_circuit_breakers()
        if triggered:
            self.logger.warning(f"🛑 CIRCUIT BREAKER TRIGGERED: {reason}")
            self.logger.warning("Halting rebalancing. Manual review required.")
            self._notify(f"Circuit breaker triggered: {reason}")
            return
        else:
            self.logger.info(f"✓ Risk check: {reason}")

        # 2. Get current state
        current = self.get_current_positions()
        self.logger.info("\nCurrent Allocation:")
        for ticker, pct in current.items():
            target_pct = self.config['allocation'][ticker]
            drift = pct - target_pct
            self.logger.info(f"  {ticker}: {pct:6.1%} (target: {target_pct:.1%}, drift: {drift:+.1%})")

        # 3. Check if rebalancing needed
        needs_rebal, reason = self.needs_rebalancing()
        self.logger.info(f"\nRebalance Check: {reason}")

        if needs_rebal:
            self.logger.info("🔄 Rebalancing required")
            self.execute_rebalance(dry_run=dry_run)
            self._notify("Portfolio rebalanced")
        else:
            self.logger.info("✓ No rebalancing needed")

        self.logger.info("="*60 + "\n")

    def _notify(self, message: str):
        """Send notification"""
        if not self.config['notifications']['enabled']:
            return

        method = self.config['notifications']['method']

        if method == 'console':
            print(f"\n📢 NOTIFICATION: {message}\n")
        elif method == 'file':
            with open('notifications.log', 'a') as f:
                f.write(f"{datetime.now().isoformat()} | {message}\n")
        elif method == 'email':
            # Send email notification
            try:
                from send_notification import send_daily_summary, send_circuit_breaker_alert
                account = self.trading_client.get_account()
                portfolio_value = float(account.portfolio_value)
                daily_change = ((float(account.equity) - float(account.last_equity)) /
                               float(account.last_equity) * 100) if float(account.last_equity) > 0 else 0

                if "rebalanced" in message.lower():
                    send_daily_summary("healthy", portfolio_value, daily_change, rebalanced=True)
                elif "circuit breaker" in message.lower():
                    send_circuit_breaker_alert(message)
                else:
                    send_daily_summary("healthy", portfolio_value, daily_change, rebalanced=False)
            except Exception as e:
                self.logger.warning(f"Failed to send email notification: {e}")

    def generate_performance_report(self) -> dict:
        """Generate performance metrics"""
        account = self.trading_client.get_account()

        report = {
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': float(account.portfolio_value),
            'cash': float(account.cash),
            'equity': float(account.equity),
            'positions': self.get_current_positions(),
        }

        # Save report
        report_file = Path(f"reports/report_{datetime.now().strftime('%Y%m%d')}.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Performance report saved: {report_file}")

        return report


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Dalio Lite - Simplified All Weather Portfolio')
    parser.add_argument('--dry-run', action='store_true', help='Calculate but do not execute orders')
    parser.add_argument('--force-rebalance', action='store_true', help='Force rebalancing regardless of drift')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    args = parser.parse_args()

    # Initialize system
    dalio = DalioLite()

    if args.report:
        report = dalio.generate_performance_report()
        print(json.dumps(report, indent=2))
    elif args.force_rebalance:
        dalio.execute_rebalance(dry_run=args.dry_run)
    else:
        dalio.run_daily_check(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
