"""Unit tests for order calculation logic."""

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
def test_order_calculation_basic_rebalance(mock_dalio, mocker):
    """Test order calculation for simple rebalance scenario."""
    # Mock account with $10,000 portfolio
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'

    mocker.patch.object(mock_dalio, 'trading_client')
    mock_dalio.trading_client.get_account = mocker.Mock(return_value=mock_account)

    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50,  # $5000 (target: $4000)
        'TLT': 0.20,  # $2000 (target: $3000)
        'GLD': 0.20,  # $2000 (target: $2000)
        'DBC': 0.10   # $1000 (target: $1000)
    })

    orders = mock_dalio.calculate_rebalance_orders()

    # VTI: $4000 target - $5000 current = -$1000 (sell)
    # TLT: $3000 target - $2000 current = +$1000 (buy)
    # GLD: No change
    # DBC: No change

    assert orders['VTI'] == pytest.approx(-1000, abs=1)
    assert orders['TLT'] == pytest.approx(1000, abs=1)
    assert orders['GLD'] == 0.0
    assert orders['DBC'] == 0.0


@pytest.mark.unit
def test_order_calculation_filters_small_trades(mock_dalio, mocker):
    """Test that trades under $100 are filtered out."""
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'

    mocker.patch.object(mock_dalio, 'trading_client')
    mock_dalio.trading_client.get_account = mocker.Mock(return_value=mock_account)

    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.405,  # $4050 (target: $4000, diff = $50 < $100 min)
        'TLT': 0.295,  # $2950 (target: $3000, diff = $50 < $100 min)
        'GLD': 0.20,
        'DBC': 0.10
    })

    orders = mock_dalio.calculate_rebalance_orders()

    # Both VTI and TLT differences are < $100, should be filtered to 0
    assert orders['VTI'] == 0.0
    assert orders['TLT'] == 0.0


@pytest.mark.unit
def test_order_calculation_conservation_of_value(mock_dalio, mocker):
    """Test that total buys approximately equal total sells."""
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'

    mocker.patch.object(mock_dalio, 'trading_client')
    mock_dalio.trading_client.get_account = mocker.Mock(return_value=mock_account)

    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50, 'TLT': 0.25, 'GLD': 0.15, 'DBC': 0.10
    })

    orders = mock_dalio.calculate_rebalance_orders()

    # Sum of all orders should be close to 0 (ignoring filtered small orders)
    total = sum(orders.values())
    assert total == pytest.approx(0.0, abs=50)  # Within $50 due to rounding/filtering
