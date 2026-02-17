"""Integration tests for error handling and recovery."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock
from dalio_lite import DalioLite, OrderStatus, OrderSide
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide as AlpacaOrderSide


@pytest.fixture
def dalio_with_failing_api(mocker, mock_env_vars):
    """Create DalioLite with API that fails intermittently."""
    mocker.patch.object(DalioLite, '_setup_broker')

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Mock trading client
    mock_trading_client = mocker.Mock()
    mock_data_client = mocker.Mock()

    # Mock account
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'
    mock_account.equity = '10000.00'
    mock_account.last_equity = '10000.00'
    mock_trading_client.get_account.return_value = mock_account

    # Mock positions (trigger rebalance)
    def create_mock_position(symbol, qty, market_value):
        pos = mocker.Mock()
        pos.symbol = symbol
        pos.qty = str(qty)
        pos.market_value = str(market_value)
        return pos

    mock_positions = [
        create_mock_position('VTI', 50, 5500),  # Overweight
        create_mock_position('TLT', 15, 2000),
        create_mock_position('GLD', 20, 2000),
        create_mock_position('DBC', 10, 500)
    ]
    mock_trading_client.get_all_positions.return_value = mock_positions

    # Mock current prices (need to support subscripting: quotes[ticker])
    def mock_get_stock_latest_quote(request):
        quotes_dict = {}
        symbols = request.symbol_or_symbols if hasattr(request, 'symbol_or_symbols') else [request]

        for symbol in symbols:
            quote = mocker.Mock()
            prices = {'VTI': 110.0, 'TLT': 133.33, 'GLD': 100.0, 'DBC': 50.0}
            quote.ask_price = prices.get(symbol, 100.0)
            quote.bid_price = prices.get(symbol, 100.0)
            quotes_dict[symbol] = quote

        return quotes_dict

    mock_data_client.get_stock_latest_quote.side_effect = mock_get_stock_latest_quote

    dalio.trading_client = mock_trading_client
    dalio.data_client = mock_data_client

    return dalio


@pytest.mark.integration
def test_retry_logic_succeeds_after_transient_failure(dalio_with_failing_api):
    """Test that retry logic recovers from transient API failures."""
    dalio = dalio_with_failing_api

    # Mock order submission that fails twice, then succeeds
    call_count = {'count': 0}

    def mock_submit_order_with_retries(order_data):
        call_count['count'] += 1

        if call_count['count'] <= 2:
            # First two attempts fail
            raise Exception("API temporarily unavailable")

        # Third attempt succeeds
        order = Mock()
        order.id = f"order_{order_data.symbol}_success"
        order.symbol = order_data.symbol
        order.side = order_data.side
        order.status = 'filled'
        return order

    dalio.trading_client.submit_order.side_effect = mock_submit_order_with_retries

    # Execute single order with retry
    result = dalio._execute_order('VTI', 1000.0, OrderSide.BUY, max_retries=3)

    # Should eventually succeed after retries
    assert result.status == OrderStatus.SUCCESS
    assert result.retry_count == 2, "Should succeed on 3rd attempt (retry count 2)"
    assert call_count['count'] == 3, "Should make 3 API calls total"


@pytest.mark.integration
def test_retry_logic_fails_after_max_attempts(dalio_with_failing_api):
    """Test that retry logic gives up after max attempts."""
    dalio = dalio_with_failing_api

    # Mock order submission that always fails
    def mock_submit_order_always_fails(order_data):
        raise Exception("API endpoint not found (permanent failure)")

    dalio.trading_client.submit_order.side_effect = mock_submit_order_always_fails

    # Execute single order with retry
    result = dalio._execute_order('VTI', 1000.0, OrderSide.BUY, max_retries=3)

    # Should fail after all retries exhausted
    assert result.status == OrderStatus.FAILED
    assert result.retry_count == 3, "Should attempt all 3 retries"
    assert result.error_message is not None
    assert "not found" in result.error_message.lower()


@pytest.mark.integration
def test_partial_failure_handling_in_rebalance(dalio_with_failing_api):
    """Test that rebalance handles partial failures gracefully."""
    dalio = dalio_with_failing_api

    # Mock order submission: VTI succeeds, TLT fails, others succeed
    def mock_submit_order_partial_failure(order_data):
        order = Mock()
        order.symbol = order_data.symbol
        order.side = order_data.side
        order.status = 'filled'

        # TLT always fails
        if order_data.symbol == 'TLT':
            raise Exception("Insufficient buying power")

        # Others succeed
        order.id = f"order_{order_data.symbol}_success"
        return order

    dalio.trading_client.submit_order.side_effect = mock_submit_order_partial_failure

    # Execute rebalance
    result = dalio.execute_rebalance(dry_run=False)

    # Should return False (not all orders succeeded)
    assert result is False, "Rebalance should report partial failure"

    # Check transaction log
    tx_dir = Path("state/transactions")
    tx_files = sorted(tx_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert len(tx_files) > 0

    with open(tx_files[0], 'r') as f:
        tx = json.load(f)

    # Status should be "partial"
    assert tx['status'] == 'partial'

    # Should have both successful and failed orders
    succeeded = [o for o in tx['executed_orders'] if o['status'] == 'success']
    failed = [o for o in tx['executed_orders'] if o['status'] == 'failed']

    assert len(succeeded) > 0, "Some orders should succeed"
    assert len(failed) > 0, "Some orders should fail"

    # TLT should be in failed orders
    tlt_failed = any(o['ticker'] == 'TLT' and o['status'] == 'failed' for o in tx['executed_orders'])
    assert tlt_failed, "TLT order should have failed"


@pytest.mark.integration
def test_reconciliation_detects_execution_mismatch(dalio_with_failing_api):
    """Test that reconciliation properly identifies execution mismatches."""
    dalio = dalio_with_failing_api

    # Mock: All orders fail
    def mock_submit_order_all_fail(order_data):
        raise Exception("Market closed")

    dalio.trading_client.submit_order.side_effect = mock_submit_order_all_fail

    # Execute rebalance
    dalio.execute_rebalance(dry_run=False)

    # Check transaction log reconciliation notes
    tx_dir = Path("state/transactions")
    tx_files = sorted(tx_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert len(tx_files) > 0

    with open(tx_files[0], 'r') as f:
        tx = json.load(f)

    # Reconciliation notes should mention failures
    notes = tx.get('reconciliation_notes', '')
    assert 'failed' in notes.lower() or 'no execution' in notes.lower()


@pytest.mark.integration
def test_exponential_backoff_timing(dalio_with_failing_api, mocker):
    """Test that retry logic uses exponential backoff."""
    import time

    dalio = dalio_with_failing_api

    # Track sleep calls
    sleep_calls = []
    original_sleep = time.sleep

    def mock_sleep(seconds):
        sleep_calls.append(seconds)
        # Don't actually sleep in tests
        pass

    mocker.patch('time.sleep', side_effect=mock_sleep)

    # Mock order submission that always fails
    def mock_submit_order_always_fails(order_data):
        raise Exception("Temporary failure")

    dalio.trading_client.submit_order.side_effect = mock_submit_order_always_fails

    # Execute order with retries
    dalio._execute_order('VTI', 1000.0, OrderSide.BUY, max_retries=3)

    # Should have exponential backoff: 1s, 2s, 4s
    assert len(sleep_calls) == 3, "Should sleep 3 times (between 4 attempts)"
    assert sleep_calls[0] == 1, "First backoff should be 1s"
    assert sleep_calls[1] == 2, "Second backoff should be 2s"
    assert sleep_calls[2] == 4, "Third backoff should be 4s"


@pytest.mark.integration
def test_transaction_log_records_retry_count(dalio_with_failing_api):
    """Test that transaction log includes retry counts."""
    dalio = dalio_with_failing_api

    # Mock: Fail once, then succeed
    call_count = {'count': 0}

    def mock_submit_order_retry_once(order_data):
        call_count['count'] += 1
        if call_count['count'] == 1:
            raise Exception("Temporary error")

        order = Mock()
        order.id = f"order_{order_data.symbol}_success"
        order.symbol = order_data.symbol
        order.side = order_data.side
        order.status = 'filled'
        return order

    dalio.trading_client.submit_order.side_effect = mock_submit_order_retry_once

    # Execute rebalance
    dalio.execute_rebalance(dry_run=False)

    # Check transaction log
    tx_dir = Path("state/transactions")
    tx_files = sorted(tx_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    with open(tx_files[0], 'r') as f:
        tx = json.load(f)

    # Find orders that had retries
    retried_orders = [o for o in tx['executed_orders'] if o.get('retry_count', 0) > 0]

    # At least one order should show retry count
    assert len(retried_orders) > 0, "Transaction log should record retry counts"


@pytest.mark.integration
def test_error_metrics_tracked(dalio_with_failing_api):
    """Test that failed orders are tracked in metrics."""
    dalio = dalio_with_failing_api

    # Mock: All orders fail
    def mock_submit_order_all_fail(order_data):
        raise Exception("API error")

    dalio.trading_client.submit_order.side_effect = mock_submit_order_all_fail

    # Execute rebalance
    dalio.execute_rebalance(dry_run=False)

    # Check metrics
    metrics_file = Path("monitoring/metrics.json")
    assert metrics_file.exists()

    with open(metrics_file, 'r') as f:
        metrics_data = json.load(f)

    # Should track failures
    assert metrics_data.get('orders_failed', 0) > 0, "Failed orders should be tracked"
    assert metrics_data.get('rebalance_failed', 0) > 0 or \
           metrics_data.get('rebalance_partial', 0) > 0, "Failed rebalance should be tracked"


@pytest.mark.integration
def test_is_retryable_error_logic(dalio_with_failing_api):
    """Test that _is_retryable_error correctly classifies errors."""
    dalio = dalio_with_failing_api

    # Retryable errors (network, timeout, rate limit)
    retryable_errors = [
        Exception("Connection timeout"),
        Exception("429 Too Many Requests"),
        Exception("Service temporarily unavailable"),
        Exception("Network error")
    ]

    for error in retryable_errors:
        assert dalio._is_retryable_error(error), \
            f"Should be retryable: {error}"

    # Non-retryable errors (auth, validation, not found)
    non_retryable_errors = [
        Exception("401 Unauthorized"),
        Exception("403 Forbidden"),
        Exception("400 Bad Request"),
        Exception("Invalid symbol"),
        Exception("Insufficient funds")
    ]

    for error in non_retryable_errors:
        assert not dalio._is_retryable_error(error), \
            f"Should NOT be retryable: {error}"


@pytest.mark.integration
def test_transaction_recovery_after_crash(dalio_with_failing_api):
    """
    Test that incomplete transactions can be identified for recovery.
    (In a real system, you'd have a recovery process for 'in_progress' transactions)
    """
    dalio = dalio_with_failing_api

    # Create an incomplete transaction manually
    from transaction_log import TransactionLogger

    logger = TransactionLogger()
    tx_id = logger.begin_transaction(
        operation="rebalance",
        target_orders={'VTI': -1000.0, 'TLT': 1000.0}
    )

    # Simulate crash - transaction left in "in_progress" state
    # (In reality, rebalance would crash before calling complete_transaction)

    # Later: Check for incomplete transactions
    tx_file = Path(f"state/transactions/{tx_id}.json")
    assert tx_file.exists()

    with open(tx_file, 'r') as f:
        tx = json.load(f)

    assert tx['status'] == 'in_progress', "Transaction should be incomplete"
    assert len(tx['executed_orders']) == 0, "No orders should be executed yet"

    # In a production system, you'd have a recovery process that:
    # 1. Finds all "in_progress" transactions
    # 2. Checks which orders actually executed
    # 3. Reconciles and completes or aborts the transaction


@pytest.mark.integration
def test_dry_run_does_not_execute_orders(dalio_with_failing_api):
    """Test that dry_run=True prevents actual order execution."""
    dalio = dalio_with_failing_api

    # Track if submit_order was called
    submit_order_called = {'called': False}

    def mock_submit_order_track(order_data):
        submit_order_called['called'] = True
        order = Mock()
        order.id = "should_not_be_called"
        return order

    dalio.trading_client.submit_order.side_effect = mock_submit_order_track

    # Execute rebalance in dry run mode
    dalio.execute_rebalance(dry_run=True)

    # Submit order should NOT be called
    assert not submit_order_called['called'], "Orders should not be executed in dry run mode"

    # Should still log plan but not execute
    # (Check logs would be ideal, but we can verify no transaction log was created for actual orders)
