"""Unit tests for circuit breaker logic."""

import pytest
from dalio_lite import DalioLite


@pytest.fixture
def mock_dalio(mocker, mock_env_vars):
    """Create DalioLite instance with mocked broker."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, '_load_last_rebalance_date', return_value=None)
    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Create mock trading_client
    dalio.trading_client = mocker.Mock()

    return dalio


@pytest.mark.unit
def test_circuit_breaker_triggers_on_5pct_loss(mock_dalio):
    """Test circuit breaker activates at 5% daily loss."""
    mock_account = mock_dalio.trading_client.get_account.return_value
    mock_account.equity = '9500.00'      # Current
    mock_account.last_equity = '10000.00' # Previous close
    # Daily return = (9500 - 10000) / 10000 = -5% (exactly at threshold)

    triggered, reason = mock_dalio.check_circuit_breakers()

    assert triggered is True
    assert ('-5' in reason or '-0.05' in reason)
    assert ('max' in reason.lower() or 'exceed' in reason.lower())


@pytest.mark.unit
def test_circuit_breaker_no_trigger_on_4pct_loss(mock_dalio):
    """Test circuit breaker does NOT trigger at 4.9% daily loss."""
    mock_account = mock_dalio.trading_client.get_account.return_value
    mock_account.equity = '9510.00'
    mock_account.last_equity = '10000.00'
    # Daily return = -4.9% (under 5% threshold)

    triggered, reason = mock_dalio.check_circuit_breakers()

    assert triggered is False
    assert ('clear' in reason.lower() or 'ok' in reason.lower() or 'all' in reason.lower())


@pytest.mark.unit
def test_circuit_breaker_handles_zero_previous_equity(mock_dalio):
    """Test circuit breaker doesn't crash when previous equity is 0."""
    mock_account = mock_dalio.trading_client.get_account.return_value
    mock_account.equity = '10000.00'
    mock_account.last_equity = '0.00'  # Edge case: new account

    triggered, reason = mock_dalio.check_circuit_breakers()

    # Should not crash, and should not trigger (can't calculate % change)
    assert triggered is False
