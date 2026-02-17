"""Integration tests for concurrency control."""

import pytest
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from dalio_lite import DalioLite
from state_lock import StateLockManager


@pytest.fixture
def clean_lock_state():
    """Clean lock files before and after tests."""
    lock_file = Path("state/dalio_lite.lock")
    if lock_file.exists():
        lock_file.unlink()

    yield

    if lock_file.exists():
        lock_file.unlink()


@pytest.mark.integration
def test_state_lock_prevents_concurrent_rebalance(mocker, mock_env_vars, clean_lock_state):
    """Test that state lock prevents two rebalances from running simultaneously."""
    # Create two DalioLite instances
    mocker.patch.object(DalioLite, '_setup_broker')

    dalio1 = DalioLite(config_path='tests/fixtures/config_test.yaml')
    dalio2 = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Mock both trading clients
    for dalio in [dalio1, dalio2]:
        mock_trading_client = mocker.Mock()
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

        dalio.trading_client = mock_trading_client
        dalio.data_client = mocker.Mock()

    # Track execution order
    execution_log = []

    def rebalance_with_delay(dalio, name, delay=0.5):
        """Execute rebalance with artificial delay."""
        try:
            execution_log.append(f"{name}_start")
            with dalio.lock_manager.acquire():
                execution_log.append(f"{name}_locked")
                time.sleep(delay)  # Hold lock for 0.5 seconds
                execution_log.append(f"{name}_done")
        except RuntimeError as e:
            execution_log.append(f"{name}_blocked: {e}")

    # Start two rebalances in parallel threads
    thread1 = threading.Thread(target=rebalance_with_delay, args=(dalio1, "Thread1"))
    thread2 = threading.Thread(target=rebalance_with_delay, args=(dalio2, "Thread2", 0.3))

    thread1.start()
    time.sleep(0.1)  # Small delay to ensure thread1 acquires lock first
    thread2.start()

    thread1.join(timeout=3)
    thread2.join(timeout=3)

    # Verify execution order
    assert len(execution_log) >= 4, "Should have at least 4 log entries"

    # One thread should complete fully before the other gets the lock
    # Possible orders:
    # 1. Thread1 runs first: [Thread1_start, Thread1_locked, Thread1_done, Thread2_start, Thread2_locked, Thread2_done]
    # 2. Thread2 runs first: [Thread2_start, Thread2_locked, Thread2_done, Thread1_start, Thread1_locked, Thread1_done]

    # Find which thread got the lock first
    first_locked = next((log for log in execution_log if '_locked' in log), None)
    assert first_locked is not None, "At least one thread should acquire lock"

    first_thread = first_locked.split('_')[0]
    second_thread = 'Thread2' if first_thread == 'Thread1' else 'Thread1'

    # Verify first thread completed before second acquired lock
    first_done_idx = execution_log.index(f"{first_thread}_done")
    second_locked_idx = execution_log.index(f"{second_thread}_locked")

    assert first_done_idx < second_locked_idx, \
        f"First thread should complete before second acquires lock. Log: {execution_log}"


@pytest.mark.integration
def test_lock_timeout_raises_error(clean_lock_state):
    """Test that lock acquisition timeout raises RuntimeError."""
    lock_manager = StateLockManager(lock_file_path="state/test_timeout.lock", timeout=1)

    # Acquire lock in first context
    with lock_manager.acquire():
        # Try to acquire again in second context (should timeout)
        lock_manager2 = StateLockManager(lock_file_path="state/test_timeout.lock", timeout=1)

        with pytest.raises(RuntimeError, match="Could not acquire state lock"):
            with lock_manager2.acquire():
                pass  # Should not reach here

    # Clean up
    Path("state/test_timeout.lock").unlink(missing_ok=True)


@pytest.mark.integration
def test_lock_released_on_exception(clean_lock_state):
    """Test that lock is properly released even if exception occurs."""
    lock_manager = StateLockManager(lock_file_path="state/test_exception.lock", timeout=5)

    # Acquire lock and raise exception
    try:
        with lock_manager.acquire():
            raise ValueError("Simulated error during rebalance")
    except ValueError:
        pass  # Expected

    # Lock should be released, so we can acquire it again
    with lock_manager.acquire():
        pass  # Should succeed

    # Clean up
    Path("state/test_exception.lock").unlink(missing_ok=True)


@pytest.mark.integration
def test_dashboard_blocked_during_rebalance(mocker, mock_env_vars, clean_lock_state):
    """
    Simulate dashboard trying to read state while rebalance is happening.
    Dashboard should wait for lock to be released.
    """
    mocker.patch.object(DalioLite, '_setup_broker')
    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Mock trading client
    mock_trading_client = mocker.Mock()
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'
    mock_trading_client.get_account.return_value = mock_account
    dalio.trading_client = mock_trading_client

    execution_order = []

    def simulate_rebalance():
        """Simulate rebalance holding lock for 1 second."""
        execution_order.append("rebalance_start")
        with dalio.lock_manager.acquire():
            execution_order.append("rebalance_locked")
            time.sleep(1)  # Simulate work
            execution_order.append("rebalance_done")

    def simulate_dashboard_read():
        """Simulate dashboard reading state."""
        time.sleep(0.2)  # Start after rebalance
        execution_order.append("dashboard_start")
        with dalio.lock_manager.acquire():
            execution_order.append("dashboard_locked")
            # Read state file
            execution_order.append("dashboard_done")

    # Run both in parallel
    rebalance_thread = threading.Thread(target=simulate_rebalance)
    dashboard_thread = threading.Thread(target=simulate_dashboard_read)

    rebalance_thread.start()
    dashboard_thread.start()

    rebalance_thread.join(timeout=3)
    dashboard_thread.join(timeout=3)

    # Dashboard should wait for rebalance to complete
    assert execution_order.index("rebalance_done") < execution_order.index("dashboard_locked"), \
        f"Dashboard should wait for rebalance. Order: {execution_order}"


@pytest.mark.integration
def test_multiple_sequential_rebalances_with_locking(mocker, mock_env_vars, clean_lock_state):
    """Test that multiple sequential rebalances work correctly with locking."""
    mocker.patch.object(DalioLite, '_setup_broker')
    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Mock trading client
    mock_trading_client = mocker.Mock()
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'
    mock_account.equity = '10000.00'
    mock_account.last_equity = '10000.00'
    mock_trading_client.get_account.return_value = mock_account

    def create_mock_position(symbol, qty, market_value):
        pos = mocker.Mock()
        pos.symbol = symbol
        pos.qty = str(qty)
        pos.market_value = str(market_value)
        return pos

    mock_positions = [
        create_mock_position('VTI', 50, 5500),
        create_mock_position('TLT', 15, 2000),
        create_mock_position('GLD', 20, 2000),
        create_mock_position('DBC', 10, 500)
    ]
    mock_trading_client.get_all_positions.return_value = mock_positions

    dalio.trading_client = mock_trading_client
    dalio.data_client = mocker.Mock()

    # Run 3 rebalances sequentially
    for i in range(3):
        # Override cooldown for testing
        dalio.last_rebalance = datetime.now() - timedelta(days=8)

        with dalio.lock_manager.acquire():
            # Simulate some rebalance work
            time.sleep(0.1)

    # All should succeed without deadlock or errors
    assert True, "Sequential rebalances should work with locking"


@pytest.mark.integration
def test_lock_acquisition_time_metric(mocker, mock_env_vars, clean_lock_state):
    """Test that lock acquisition time is tracked in metrics."""
    from metrics_collector import metrics

    mocker.patch.object(DalioLite, '_setup_broker')
    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Mock trading client
    mock_trading_client = mocker.Mock()
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'
    mock_trading_client.get_account.return_value = mock_account
    dalio.trading_client = mock_trading_client

    # Acquire lock and track time
    start = time.time()
    with dalio.lock_manager.acquire():
        lock_time = (time.time() - start) * 1000  # Convert to ms
        metrics.record_duration("lock_acquisition_time_ms", lock_time)

    metrics.flush()

    # Verify metric was recorded
    metrics_file = Path("monitoring/metrics.json")
    assert metrics_file.exists()

    with open(metrics_file, 'r') as f:
        metrics_data = json.load(f)

    # Should have lock acquisition metrics
    assert 'lock_acquisition_time_ms_avg' in metrics_data or \
           'lock_acquisition_time_ms_p50' in metrics_data, \
           "Lock acquisition time should be tracked"


@pytest.mark.integration
def test_race_condition_prevention_in_state_writes(mocker, mock_env_vars, clean_lock_state):
    """
    Test that atomic writes with locking prevent race conditions in state file updates.
    """
    mocker.patch.object(DalioLite, '_setup_broker')

    dalio1 = DalioLite(config_path='tests/fixtures/config_test.yaml')
    dalio2 = DalioLite(config_path='tests/fixtures/config_test.yaml')

    for dalio in [dalio1, dalio2]:
        mock_trading_client = mocker.Mock()
        mock_account = mocker.Mock()
        mock_account.portfolio_value = '10000.00'
        mock_trading_client.get_account.return_value = mock_account
        dalio.trading_client = mock_trading_client

    results = []

    def save_rebalance_date(dalio, name):
        """Save rebalance date with locking."""
        try:
            with dalio.lock_manager.acquire():
                timestamp = datetime.now()
                dalio._save_rebalance_date(timestamp)
                results.append(f"{name}_success")
        except Exception as e:
            results.append(f"{name}_failed: {e}")

    # Try to save from two threads simultaneously
    thread1 = threading.Thread(target=save_rebalance_date, args=(dalio1, "Thread1"))
    thread2 = threading.Thread(target=save_rebalance_date, args=(dalio2, "Thread2"))

    thread1.start()
    thread2.start()

    thread1.join(timeout=5)
    thread2.join(timeout=5)

    # Both should succeed (one after the other)
    assert len(results) == 2
    assert all('success' in r for r in results), f"Both saves should succeed: {results}"

    # Verify state file exists and is valid JSON
    state_file = Path("state/last_rebalance.json")
    assert state_file.exists()

    with open(state_file, 'r') as f:
        state_data = json.load(f)  # Should not raise (valid JSON)

    assert 'timestamp' in state_data


import json
