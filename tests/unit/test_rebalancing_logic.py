"""Unit tests for rebalancing decision logic."""

import pytest
from datetime import datetime, timedelta
from dalio_lite import DalioLite


@pytest.fixture
def mock_dalio(mocker, mock_env_vars):
    """Create DalioLite instance with mocked broker."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, '_load_last_rebalance_date', return_value=None)
    return DalioLite(config_path='tests/fixtures/config_test.yaml')


@pytest.mark.unit
def test_needs_rebalancing_exceeds_threshold(mock_dalio, mocker):
    """Test rebalancing triggered when drift exceeds 10%."""
    mocker.patch.object(DalioLite, 'calculate_drift', return_value={
        'VTI': 0.12,  # 12% overweight (exceeds 10% threshold)
        'TLT': -0.05,
        'GLD': 0.02,
        'DBC': -0.01
    })

    needs_rebal, reason = mock_dalio.needs_rebalancing()

    assert needs_rebal is True
    assert 'VTI' in reason  # Should mention triggering ticker
    assert ('12' in reason or '0.12' in reason)  # Should mention drift amount


@pytest.mark.unit
def test_needs_rebalancing_within_threshold(mock_dalio, mocker):
    """Test rebalancing NOT triggered when drift within 10%."""
    mocker.patch.object(DalioLite, 'calculate_drift', return_value={
        'VTI': 0.08,  # 8% overweight (under 10% threshold)
        'TLT': -0.05,
        'GLD': 0.02,
        'DBC': -0.01
    })

    needs_rebal, reason = mock_dalio.needs_rebalancing()

    assert needs_rebal is False
    assert 'within' in reason.lower()


@pytest.mark.unit
def test_needs_rebalancing_too_soon_after_last(mock_dalio, mocker):
    """Test rebalancing blocked by minimum days requirement."""
    mocker.patch.object(DalioLite, 'calculate_drift', return_value={
        'VTI': 0.15  # Would trigger, but too soon
    })

    # Last rebalance was 10 days ago (min is 30)
    recent_rebalance = datetime.now() - timedelta(days=10)
    mock_dalio.last_rebalance = recent_rebalance

    needs_rebal, reason = mock_dalio.needs_rebalancing()

    assert needs_rebal is False
    assert '10' in reason
    assert ('30' in reason or 'min' in reason.lower())
