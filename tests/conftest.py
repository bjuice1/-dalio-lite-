"""Shared pytest fixtures for all tests."""

import pytest
import os
from pathlib import Path
from tests.fixtures.mock_alpaca_client import MockTradingClient, MockDataClient


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv('ALPACA_API_KEY', 'test_key_123')
    monkeypatch.setenv('ALPACA_SECRET_KEY', 'test_secret_456')


@pytest.fixture
def test_config_path():
    """Return path to test configuration."""
    return 'tests/fixtures/config_test.yaml'


@pytest.fixture
def mock_alpaca_clients(mocker):
    """Mock both Alpaca clients (trading and data)."""
    mock_trading = MockTradingClient(api_key='test', secret_key='test', paper=True)
    mock_data = MockDataClient()

    mocker.patch('dalio_lite.TradingClient', return_value=mock_trading)
    mocker.patch('dalio_lite.StockHistoricalDataClient', return_value=mock_data)

    return mock_trading, mock_data


@pytest.fixture
def clean_state_dir(tmp_path):
    """Provide clean temporary state directory for tests."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton state between tests."""
    # Add any singleton reset logic here
    yield
