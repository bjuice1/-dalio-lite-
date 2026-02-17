"""Unit tests for drift calculation logic."""

import pytest
from dalio_lite import DalioLite


@pytest.fixture
def mock_dalio(mocker, mock_env_vars):
    """Create DalioLite instance with mocked broker."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, '_load_last_rebalance_date', return_value=None)
    return DalioLite(config_path='tests/fixtures/config_test.yaml')


@pytest.mark.unit
def test_drift_calculation_balanced_portfolio(mock_dalio, mocker):
    """Test drift when portfolio is perfectly balanced."""
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.40, 'TLT': 0.30, 'GLD': 0.20, 'DBC': 0.10
    })

    drift = mock_dalio.calculate_drift()

    assert drift == {'VTI': 0.0, 'TLT': 0.0, 'GLD': 0.0, 'DBC': 0.0}


@pytest.mark.unit
def test_drift_calculation_overweight_stocks(mock_dalio, mocker):
    """Test drift when stocks are overweight."""
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50,  # 10% overweight
        'TLT': 0.25,  # 5% underweight
        'GLD': 0.15,  # 5% underweight
        'DBC': 0.10   # Balanced
    })

    drift = mock_dalio.calculate_drift()

    assert drift['VTI'] == pytest.approx(0.10, abs=0.001)
    assert drift['TLT'] == pytest.approx(-0.05, abs=0.001)
    assert drift['GLD'] == pytest.approx(-0.05, abs=0.001)
    assert drift['DBC'] == pytest.approx(0.0, abs=0.001)


@pytest.mark.unit
def test_drift_calculation_missing_position(mock_dalio, mocker):
    """Test drift when a position is completely missing."""
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50, 'TLT': 0.30, 'GLD': 0.20
        # DBC missing (position sold or never bought)
    })

    drift = mock_dalio.calculate_drift()

    # DBC should be treated as 0%, so drift = 0.0 - 0.10 = -0.10
    assert drift['DBC'] == pytest.approx(-0.10, abs=0.001)


@pytest.mark.unit
def test_drift_calculation_zero_portfolio_value(mock_dalio, mocker):
    """Test drift when portfolio value is $0 (edge case)."""
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={})

    drift = mock_dalio.calculate_drift()

    # All positions missing = all underweight by target amount
    assert drift == {
        'VTI': -0.40, 'TLT': -0.30, 'GLD': -0.20, 'DBC': -0.10
    }
