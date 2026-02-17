"""Integration tests for full rebalance flow."""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dalio_lite import DalioLite, OrderStatus
from metrics_collector import metrics
from transaction_log import TransactionLogger


@pytest.fixture
def clean_integration_state():
    """Clean up state files before and after integration tests."""
    state_dir = Path("state")
    monitoring_dir = Path("monitoring")
    backups_dir = Path("backups")

    # Clean before test (including subdirectories like state/transactions)
    if state_dir.exists():
        for f in state_dir.glob("**/*"):
            if f.is_file():
                f.unlink()
    if monitoring_dir.exists():
        for f in monitoring_dir.glob("**/*"):
            if f.is_file():
                f.unlink()

    yield

    # Clean after test (optional - comment out to inspect test artifacts)
    # for directory in [state_dir, monitoring_dir]:
    #     if directory.exists():
    #         for f in directory.glob("**/*"):
    #             if f.is_file():
    #                 f.unlink()


@pytest.fixture
def dalio_with_mocked_api(mocker, mock_env_vars, clean_integration_state):
    """Create DalioLite with mocked Alpaca API for integration testing."""
    # Mock the broker setup to avoid real API calls
    mocker.patch.object(DalioLite, '_setup_broker')

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Create mock trading client
    mock_trading_client = mocker.Mock()
    mock_data_client = mocker.Mock()

    # Mock account
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'
    mock_account.equity = '10000.00'
    mock_account.last_equity = '10000.00'
    mock_account.cash = '0.00'
    mock_trading_client.get_account.return_value = mock_account

    # Mock positions (portfolio drift scenario)
    def create_mock_position(symbol, qty, market_value):
        pos = mocker.Mock()
        pos.symbol = symbol
        pos.qty = str(qty)
        pos.market_value = str(market_value)
        return pos

    # Overweight VTI, underweight TLT (triggers rebalance)
    mock_positions = [
        create_mock_position('VTI', 50, 5500),   # 55% (target: 40%)
        create_mock_position('TLT', 15, 2000),   # 20% (target: 30%)
        create_mock_position('GLD', 20, 2000),   # 20% (target: 20%)
        create_mock_position('DBC', 10, 500)     # 5% (target: 10%)
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

    # Mock order submission (all successful)
    def mock_submit_order(order_data):
        order = mocker.Mock()
        order.id = f"order_{order_data.symbol}_{int(time.time() * 1000)}"
        order.symbol = order_data.symbol
        order.side = order_data.side
        # Get price from prices dict directly
        prices = {'VTI': 110.0, 'TLT': 133.33, 'GLD': 100.0, 'DBC': 50.0}
        price = prices.get(order_data.symbol, 100.0)
        order.qty = order_data.notional / price if hasattr(order_data, 'notional') else order_data.qty
        order.filled_avg_price = price
        order.status = 'filled'
        return order

    mock_trading_client.submit_order.side_effect = mock_submit_order

    dalio.trading_client = mock_trading_client
    dalio.data_client = mock_data_client

    return dalio


@pytest.mark.integration
def test_full_rebalance_flow_success(dalio_with_mocked_api):
    """
    Test complete rebalance flow with all systems:
    - State locking
    - Transaction logging
    - Metrics collection
    - Order execution
    - Backup creation
    """
    dalio = dalio_with_mocked_api

    # Execute rebalance
    result = dalio.execute_rebalance(dry_run=False)

    assert result is True, "Rebalance should succeed"

    # Verify transaction log was created
    tx_dir = Path("state/transactions")
    assert tx_dir.exists(), "Transaction directory should exist"

    tx_files = list(tx_dir.glob("*.json"))
    assert len(tx_files) >= 1, "At least one transaction log should exist"

    # Load and verify transaction log
    with open(tx_files[0], 'r') as f:
        tx_data = json.load(f)

    assert tx_data['operation'] == 'rebalance'
    assert tx_data['status'] == 'completed'
    assert 'transaction_id' in tx_data
    assert 'timestamp' in tx_data
    assert 'target_orders' in tx_data
    assert 'executed_orders' in tx_data
    assert len(tx_data['executed_orders']) > 0

    # Verify all orders succeeded
    for order in tx_data['executed_orders']:
        assert order['status'] == 'success', f"Order {order['ticker']} should succeed"

    # Verify metrics were collected
    metrics_file = Path("monitoring/metrics.json")
    assert metrics_file.exists(), "Metrics file should exist"

    with open(metrics_file, 'r') as f:
        metrics_data = json.load(f)

    assert metrics_data['rebalance_total'] >= 1
    assert metrics_data['rebalance_success'] >= 1
    assert metrics_data['orders_executed'] > 0
    assert metrics_data['orders_success'] > 0
    assert 'rebalance_duration_seconds_avg' in metrics_data

    # Verify state was saved
    state_file = Path("state/last_rebalance.json")
    assert state_file.exists(), "Rebalance state should be saved"

    with open(state_file, 'r') as f:
        state_data = json.load(f)

    assert 'timestamp' in state_data

    # Verify backup was created
    backup_dir = Path("backups")
    assert backup_dir.exists(), "Backup directory should exist"

    backup_files = list(backup_dir.glob("last_rebalance_*.json"))
    assert len(backup_files) >= 1, "At least one backup should exist"

    # Verify backup checksum exists
    checksum_files = list(backup_dir.glob("*.sha256"))
    assert len(checksum_files) >= 1, "Backup checksums should exist"


@pytest.mark.integration
def test_rebalance_with_drift_threshold(dalio_with_mocked_api, mocker):
    """Test that rebalance only happens when drift exceeds threshold."""
    dalio = dalio_with_mocked_api

    # Mock balanced portfolio (no drift)
    def create_mock_position(symbol, qty, market_value):
        pos = mocker.Mock()
        pos.symbol = symbol
        pos.qty = str(qty)
        pos.market_value = str(market_value)
        return pos

    # Perfectly balanced portfolio
    balanced_positions = [
        create_mock_position('VTI', 40, 4000),  # 40%
        create_mock_position('TLT', 30, 3000),  # 30%
        create_mock_position('GLD', 20, 2000),  # 20%
        create_mock_position('DBC', 10, 1000)   # 10%
    ]

    dalio.trading_client.get_all_positions.return_value = balanced_positions

    # Check if rebalancing is needed (returns tuple: (bool, str))
    needs_rebalance, reason = dalio.needs_rebalancing()

    assert needs_rebalance is False, f"Should not rebalance when within threshold: {reason}"


@pytest.mark.integration
def test_circuit_breaker_prevents_rebalance(dalio_with_mocked_api, mocker):
    """Test that circuit breaker prevents rebalancing during large losses."""
    dalio = dalio_with_mocked_api

    # Create new mock account with 5% daily loss (triggers circuit breaker)
    mock_account_cb = mocker.Mock()
    mock_account_cb.equity = '9500.00'      # Current
    mock_account_cb.last_equity = '10000.00'  # Previous close
    mock_account_cb.portfolio_value = '9500.00'
    mock_account_cb.cash = '0.00'

    # Update the mock to return circuit breaker account
    dalio.trading_client.get_account.return_value = mock_account_cb

    # Circuit breaker check should trigger
    triggered, reason = dalio.check_circuit_breakers()
    assert triggered is True, f"Circuit breaker should trigger: {reason}"
    assert '-5' in reason or '-0.05' in reason, "Reason should mention 5% loss"

    # run_daily_check should be blocked by circuit breaker (not execute_rebalance, which is forced)
    # Note: run_daily_check returns None when circuit breaker triggers
    dalio.run_daily_check(dry_run=False)  # Should exit early due to circuit breaker

    # Verify metrics show circuit breaker was triggered
    metrics_file = Path("monitoring/metrics.json")
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)

        assert metrics_data.get('circuit_breaker_triggered', 0) >= 1, "Circuit breaker metric should increment"


@pytest.mark.integration
def test_daily_check_workflow(dalio_with_mocked_api):
    """Test the complete daily check workflow."""
    dalio = dalio_with_mocked_api

    # Run daily check (AutoPilot)
    dalio.run_daily_check(dry_run=False)

    # Verify metrics show AutoPilot ran
    metrics_file = Path("monitoring/metrics.json")
    assert metrics_file.exists()

    with open(metrics_file, 'r') as f:
        metrics_data = json.load(f)

    assert 'autopilot_last_run' in metrics_data

    # Verify timestamp is recent (within last minute)
    last_run = datetime.fromisoformat(metrics_data['autopilot_last_run'])
    now = datetime.now()
    assert (now - last_run).total_seconds() < 60, "AutoPilot should have run recently"


@pytest.mark.integration
def test_rebalance_cooldown_period(dalio_with_mocked_api):
    """Test that rebalancing respects cooldown period."""
    dalio = dalio_with_mocked_api

    # Set last rebalance to yesterday
    dalio.last_rebalance = datetime.now() - timedelta(days=1)
    dalio._save_rebalance_date(dalio.last_rebalance)

    # Try to rebalance again (should be blocked by cooldown)
    needs_rebalance, reason = dalio.needs_rebalancing()

    # With min_days_between_rebalance=30 in test config, should not rebalance after just 1 day
    assert needs_rebalance is False, f"Should respect cooldown period: {reason}"


@pytest.mark.integration
def test_metrics_persistence_across_runs(dalio_with_mocked_api):
    """Test that metrics persist across multiple rebalancing runs."""
    dalio = dalio_with_mocked_api

    # First rebalance
    dalio.execute_rebalance(dry_run=False)

    metrics_file = Path("monitoring/metrics.json")
    with open(metrics_file, 'r') as f:
        first_metrics = json.load(f)

    first_rebalance_total = first_metrics.get('rebalance_total', 0)

    # Second rebalance (force it)
    dalio.last_rebalance = datetime.now() - timedelta(days=8)  # Outside cooldown
    dalio.execute_rebalance(dry_run=False)

    with open(metrics_file, 'r') as f:
        second_metrics = json.load(f)

    second_rebalance_total = second_metrics.get('rebalance_total', 0)

    # Counter should have incremented
    assert second_rebalance_total > first_rebalance_total, "Metrics should persist and increment"


@pytest.mark.integration
def test_transaction_log_contains_all_details(dalio_with_mocked_api):
    """Test that transaction logs capture all execution details."""
    dalio = dalio_with_mocked_api

    # Execute rebalance
    dalio.execute_rebalance(dry_run=False)

    # Find transaction log
    tx_dir = Path("state/transactions")
    tx_files = sorted(tx_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert len(tx_files) > 0

    with open(tx_files[0], 'r') as f:
        tx = json.load(f)

    # Verify structure
    required_fields = [
        'transaction_id',
        'timestamp',
        'operation',
        'target_orders',
        'executed_orders',
        'status',
        'reconciliation_notes'
    ]

    for field in required_fields:
        assert field in tx, f"Transaction log should contain {field}"

    # Verify executed orders have details
    if tx['executed_orders']:
        order = tx['executed_orders'][0]
        assert 'ticker' in order
        assert 'side' in order
        assert 'amount_usd' in order
        assert 'status' in order
        assert 'timestamp' in order
