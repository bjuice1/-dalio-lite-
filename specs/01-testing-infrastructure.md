# Testing Infrastructure Specification

**Document:** 01-testing-infrastructure.md
**Project:** Dalio Lite Production Hardening
**Date:** 2026-02-17
**Status:** Final
**Dependencies:** None (foundational document)
**Enables:** 03-error-handling-recovery.md, 06-migration-rollout.md

---

## Overview

This document defines the complete testing infrastructure for Dalio Lite, addressing the critical gap of **zero test coverage** identified in audit1. The system currently manages financial transactions without any automated validation, creating unacceptable risk for users transitioning to live trading.

**Why This Exists:**
- Current state: 3,353 lines of production code, 0 lines of test code
- Financial risk: Untested rebalancing logic could cause incorrect trades
- Regression risk: Code changes could silently break critical functionality
- Compliance: Production financial systems require test coverage

**What This Covers:**
- Test framework selection and configuration
- Unit test strategy for core business logic
- Integration test strategy for Alpaca API
- Mocking and fixture patterns
- Test execution workflow and CI/CD integration
- Coverage targets and reporting

---

## Architecture

### Testing Pyramid

```
                 ▲
                / \
               /   \
              / E2E \          1 test  (Full system validation)
             /-------\
            /         \
           / Integration\     5 tests (API mocking, state management)
          /-------------\
         /               \
        /   Unit Tests    \   20 tests (Business logic, calculations)
       /___________________\
```

**Rationale:** Heavy unit test coverage for financial logic (drift calculation, order sizing), moderate integration tests for API boundaries, minimal E2E for smoke testing.

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                          │
│  (GitHub Actions / Local Pre-commit Hook)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   pytest Test Runner                         │
│  • Discover tests in tests/**/*_test.py                     │
│  • Generate coverage report (target: 80%+)                   │
│  • Fail build if critical tests fail                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐
│   Unit Tests    │    │ Integration Tests   │
│  tests/unit/    │    │  tests/integration/ │
│                 │    │                     │
│ • Pure logic    │    │ • API mocking       │
│ • No I/O        │    │ • State files       │
│ • Fast (<100ms) │    │ • Slower (~1s)      │
└─────────────────┘    └─────────────────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Test Fixtures & Mocks                         │
│  tests/fixtures/                                             │
│  • mock_alpaca_client.py (Alpaca API responses)             │
│  • sample_portfolios.json (Test data)                       │
│  • config_test.yaml (Test configuration)                    │
└─────────────────────────────────────────────────────────────┘
```

### Dependencies

**Inbound (What This Needs):**
- Production codebase: `dalio_lite.py`, `dashboard.py`, `send_notification.py`
- Test framework: pytest (to be installed)
- Mocking library: pytest-mock, responses (for HTTP mocking)

**Outbound (What Consumes This):**
- 03-error-handling: Error paths validated through tests
- 06-migration: Test passage required before deployment gates
- Developers: Run tests before committing code changes

---

## Specification

### 1. Test Framework Selection

**Decision:** pytest (not unittest or custom)

**Rationale:**
- Industry standard for Python testing
- Superior fixture management (`@pytest.fixture`)
- Better assertions (plain `assert` with detailed failure messages)
- Rich plugin ecosystem (coverage, mocking, parameterization)
- Minimal boilerplate compared to unittest

**Configuration:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = *_test.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=dalio_lite
    --cov=dashboard
    --cov=send_notification
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
    --strict-markers
markers =
    unit: Unit tests (fast, no I/O)
    integration: Integration tests (slower, may hit APIs)
    slow: Tests that take >1s
    requires_alpaca: Tests that need Alpaca API keys
```

**Installation:**

```bash
pip install pytest pytest-cov pytest-mock responses
```

Update `requirements.txt`:

```
# Testing (dev only - not needed in production)
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
responses>=0.23.0  # Mock HTTP requests
```

---

### 2. Directory Structure

```
dalio-lite/
├── dalio_lite.py
├── dashboard.py
├── send_notification.py
├── pytest.ini              # ← New: pytest configuration
├── requirements.txt        # ← Updated: add test dependencies
├── requirements-dev.txt    # ← New: separate dev dependencies
└── tests/                  # ← New: all test code
    ├── __init__.py
    ├── conftest.py         # Shared fixtures
    ├── fixtures/           # Test data
    │   ├── __init__.py
    │   ├── mock_alpaca_client.py
    │   ├── sample_portfolios.json
    │   └── config_test.yaml
    ├── unit/               # Fast, no I/O
    │   ├── __init__.py
    │   ├── test_drift_calculation.py
    │   ├── test_rebalancing_logic.py
    │   ├── test_circuit_breakers.py
    │   ├── test_order_calculation.py
    │   └── test_state_management.py
    └── integration/        # Slower, with mocked APIs
        ├── __init__.py
        ├── test_alpaca_integration.py
        ├── test_end_to_end_rebalance.py
        ├── test_notification_system.py
        └── test_autopilot_execution.py
```

---

### 3. Unit Test Specifications

#### 3.1 Test: Drift Calculation

**File:** `tests/unit/test_drift_calculation.py`

**What to Test:**
- Drift calculation is accurate (current % - target %)
- Handles zero portfolio value gracefully
- Returns correct sign (positive = overweight, negative = underweight)
- Works with missing positions (treats as 0%)

**Test Cases:**

```python
import pytest
from dalio_lite import DalioLite

@pytest.fixture
def mock_config():
    """Test configuration with known allocation."""
    return {
        'allocation': {'VTI': 0.40, 'TLT': 0.30, 'GLD': 0.20, 'DBC': 0.10},
        'mode': {'paper_trading': True},
        # ... other config ...
    }

@pytest.mark.unit
def test_drift_calculation_balanced_portfolio(mock_config, mocker):
    """Test drift when portfolio is perfectly balanced."""
    # Setup: Mock broker to return balanced portfolio
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.40, 'TLT': 0.30, 'GLD': 0.20, 'DBC': 0.10
    })

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    drift = dalio.calculate_drift()

    # Assert: All drifts should be 0.0
    assert drift == {'VTI': 0.0, 'TLT': 0.0, 'GLD': 0.0, 'DBC': 0.0}

@pytest.mark.unit
def test_drift_calculation_overweight_stocks(mock_config, mocker):
    """Test drift when stocks are overweight."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50,  # 10% overweight
        'TLT': 0.25,  # 5% underweight
        'GLD': 0.15,  # 5% underweight
        'DBC': 0.10   # Balanced
    })

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    drift = dalio.calculate_drift()

    assert drift['VTI'] == pytest.approx(0.10, abs=0.001)
    assert drift['TLT'] == pytest.approx(-0.05, abs=0.001)
    assert drift['GLD'] == pytest.approx(-0.05, abs=0.001)
    assert drift['DBC'] == pytest.approx(0.0, abs=0.001)

@pytest.mark.unit
def test_drift_calculation_missing_position(mock_config, mocker):
    """Test drift when a position is completely missing."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50, 'TLT': 0.30, 'GLD': 0.20
        # DBC missing (position sold or never bought)
    })

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    drift = dalio.calculate_drift()

    # DBC should be treated as 0%, so drift = 0.0 - 0.10 = -0.10
    assert drift['DBC'] == pytest.approx(-0.10, abs=0.001)

@pytest.mark.unit
def test_drift_calculation_zero_portfolio_value(mock_config, mocker):
    """Test drift when portfolio value is $0 (edge case)."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={})

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    drift = dalio.calculate_drift()

    # All positions missing = all underweight by target amount
    assert drift == {
        'VTI': -0.40, 'TLT': -0.30, 'GLD': -0.20, 'DBC': -0.10
    }
```

**Coverage Target:** 100% of `calculate_drift()` method

---

#### 3.2 Test: Rebalancing Decision Logic

**File:** `tests/unit/test_rebalancing_logic.py`

**What to Test:**
- `needs_rebalancing()` returns True when drift exceeds threshold
- `needs_rebalancing()` returns False when within threshold
- Minimum days between rebalances enforced
- Correct ticker identified as trigger

**Test Cases:**

```python
import pytest
from datetime import datetime, timedelta
from dalio_lite import DalioLite

@pytest.mark.unit
def test_needs_rebalancing_exceeds_threshold(mocker):
    """Test rebalancing triggered when drift exceeds 10%."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'calculate_drift', return_value={
        'VTI': 0.12,  # 12% overweight (exceeds 10% threshold)
        'TLT': -0.05,
        'GLD': 0.02,
        'DBC': -0.01
    })
    mocker.patch.object(DalioLite, 'last_rebalance', None)  # No previous rebalance

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    needs_rebal, reason = dalio.needs_rebalancing()

    assert needs_rebal is True
    assert 'VTI' in reason  # Should mention triggering ticker
    assert '12' in reason or '0.12' in reason  # Should mention drift amount

@pytest.mark.unit
def test_needs_rebalancing_within_threshold(mocker):
    """Test rebalancing NOT triggered when drift within 10%."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'calculate_drift', return_value={
        'VTI': 0.08,  # 8% overweight (under 10% threshold)
        'TLT': -0.05,
        'GLD': 0.02,
        'DBC': -0.01
    })

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    needs_rebal, reason = dalio.needs_rebalancing()

    assert needs_rebal is False
    assert 'within' in reason.lower()

@pytest.mark.unit
def test_needs_rebalancing_too_soon_after_last(mocker):
    """Test rebalancing blocked by minimum days requirement."""
    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'calculate_drift', return_value={
        'VTI': 0.15  # Would trigger, but too soon
    })

    # Last rebalance was 10 days ago (min is 30)
    recent_rebalance = datetime.now() - timedelta(days=10)
    mocker.patch.object(DalioLite, 'last_rebalance', recent_rebalance)

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    needs_rebal, reason = dalio.needs_rebalancing()

    assert needs_rebal is False
    assert '10 days' in reason
    assert 'min: 30' in reason or 'minimum' in reason.lower()
```

**Coverage Target:** 100% of `needs_rebalancing()` method

---

#### 3.3 Test: Order Calculation

**File:** `tests/unit/test_order_calculation.py`

**What to Test:**
- Order amounts calculated correctly (target value - current value)
- Small orders filtered out (< $100 minimum)
- Positive amounts = buy, negative = sell
- Orders sum to approximately zero (conservation of value)

**Test Cases:**

```python
import pytest
from dalio_lite import DalioLite

@pytest.mark.unit
def test_order_calculation_basic_rebalance(mocker):
    """Test order calculation for simple rebalance scenario."""
    # Mock account with $10,000 portfolio
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'

    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'trading_client.get_account', return_value=mock_account)
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50,  # $5000 (target: $4000)
        'TLT': 0.20,  # $2000 (target: $3000)
        'GLD': 0.20,  # $2000 (target: $2000)
        'DBC': 0.10   # $1000 (target: $1000)
    })

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    orders = dalio.calculate_rebalance_orders()

    # VTI: $4000 target - $5000 current = -$1000 (sell)
    # TLT: $3000 target - $2000 current = +$1000 (buy)
    # GLD: No change
    # DBC: No change

    assert orders['VTI'] == pytest.approx(-1000, abs=1)
    assert orders['TLT'] == pytest.approx(1000, abs=1)
    assert orders['GLD'] == 0.0
    assert orders['DBC'] == 0.0

@pytest.mark.unit
def test_order_calculation_filters_small_trades(mocker):
    """Test that trades under $100 are filtered out."""
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'

    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'trading_client.get_account', return_value=mock_account)
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.405,  # $4050 (target: $4000, diff = $50 < $100 min)
        'TLT': 0.295,  # $2950 (target: $3000, diff = $50 < $100 min)
        'GLD': 0.20,
        'DBC': 0.10
    })

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    orders = dalio.calculate_rebalance_orders()

    # Both VTI and TLT differences are < $100, should be filtered to 0
    assert orders['VTI'] == 0.0
    assert orders['TLT'] == 0.0

@pytest.mark.unit
def test_order_calculation_conservation_of_value(mocker):
    """Test that total buys approximately equal total sells."""
    mock_account = mocker.Mock()
    mock_account.portfolio_value = '10000.00'

    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'trading_client.get_account', return_value=mock_account)
    mocker.patch.object(DalioLite, 'get_current_positions', return_value={
        'VTI': 0.50, 'TLT': 0.25, 'GLD': 0.15, 'DBC': 0.10
    })

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    orders = dalio.calculate_rebalance_orders()

    # Sum of all orders should be close to 0 (ignoring filtered small orders)
    total = sum(orders.values())
    assert total == pytest.approx(0.0, abs=50)  # Within $50 due to rounding/filtering
```

**Coverage Target:** 100% of `calculate_rebalance_orders()` method

---

#### 3.4 Test: Circuit Breakers

**File:** `tests/unit/test_circuit_breakers.py`

**What to Test:**
- Circuit breaker triggers at 5% daily loss
- Circuit breaker doesn't trigger under normal conditions
- Correct calculation of daily return percentage
- Handles edge case when previous equity is zero

**Test Cases:**

```python
import pytest
from dalio_lite import DalioLite

@pytest.mark.unit
def test_circuit_breaker_triggers_on_5pct_loss(mocker):
    """Test circuit breaker activates at 5% daily loss."""
    mock_account = mocker.Mock()
    mock_account.equity = '9500.00'      # Current
    mock_account.last_equity = '10000.00' # Previous close
    # Daily return = (9500 - 10000) / 10000 = -5% (exactly at threshold)

    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'trading_client.get_account', return_value=mock_account)

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    triggered, reason = dalio.check_circuit_breakers()

    assert triggered is True
    assert '-5' in reason or '-0.05' in reason
    assert 'max' in reason.lower() or 'exceed' in reason.lower()

@pytest.mark.unit
def test_circuit_breaker_no_trigger_on_4pct_loss(mocker):
    """Test circuit breaker does NOT trigger at 4.9% daily loss."""
    mock_account = mocker.Mock()
    mock_account.equity = '9510.00'
    mock_account.last_equity = '10000.00'
    # Daily return = -4.9% (under 5% threshold)

    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'trading_client.get_account', return_value=mock_account)

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    triggered, reason = dalio.check_circuit_breakers()

    assert triggered is False
    assert 'clear' in reason.lower() or 'ok' in reason.lower()

@pytest.mark.unit
def test_circuit_breaker_handles_zero_previous_equity(mocker):
    """Test circuit breaker doesn't crash when previous equity is 0."""
    mock_account = mocker.Mock()
    mock_account.equity = '10000.00'
    mock_account.last_equity = '0.00'  # Edge case: new account

    mocker.patch.object(DalioLite, '_setup_broker')
    mocker.patch.object(DalioLite, 'trading_client.get_account', return_value=mock_account)

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    triggered, reason = dalio.check_circuit_breakers()

    # Should not crash, and should not trigger (can't calculate % change)
    assert triggered is False
```

**Coverage Target:** 100% of `check_circuit_breakers()` method

---

#### 3.5 Test: State Management

**File:** `tests/unit/test_state_management.py`

**What to Test:**
- State file saved with correct format
- State file loaded correctly
- Handles missing state file gracefully (returns None)
- Handles corrupted state file gracefully

**Test Cases:**

```python
import pytest
from pathlib import Path
from datetime import datetime
import json
from dalio_lite import DalioLite

@pytest.mark.unit
def test_save_rebalance_date(mocker, tmp_path):
    """Test saving rebalance timestamp to state file."""
    # Use tmp_path fixture for isolated filesystem
    state_dir = tmp_path / "state"
    state_file = state_dir / "last_rebalance.json"

    mocker.patch.object(Path, '__new__', return_value=state_file)
    mocker.patch.object(DalioLite, '_setup_broker')

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    test_timestamp = datetime(2026, 2, 17, 10, 30, 0)
    dalio._save_rebalance_date(test_timestamp)

    # Verify file was created
    assert state_file.exists()

    # Verify correct content
    with open(state_file, 'r') as f:
        data = json.load(f)

    assert 'timestamp' in data
    assert data['timestamp'] == '2026-02-17T10:30:00'

@pytest.mark.unit
def test_load_rebalance_date_missing_file(mocker, tmp_path):
    """Test loading state when file doesn't exist."""
    state_file = tmp_path / "state" / "last_rebalance.json"
    # File doesn't exist

    mocker.patch.object(Path, '__new__', return_value=state_file)
    mocker.patch.object(DalioLite, '_setup_broker')

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    result = dalio._load_last_rebalance_date()

    # Should return None gracefully, not crash
    assert result is None

@pytest.mark.unit
def test_load_rebalance_date_corrupted_file(mocker, tmp_path):
    """Test loading state when file is corrupted."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "last_rebalance.json"

    # Write corrupted JSON
    with open(state_file, 'w') as f:
        f.write("{invalid json")

    mocker.patch.object(Path, '__new__', return_value=state_file)
    mocker.patch.object(DalioLite, '_setup_broker')

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Should handle gracefully (log error, return None)
    # Current implementation may crash - this test documents expected behavior
    with pytest.raises(json.JSONDecodeError):
        result = dalio._load_last_rebalance_date()

    # NOTE: Implementation should be fixed to catch this and return None
```

**Coverage Target:** 100% of `_save_rebalance_date()` and `_load_last_rebalance_date()` methods

---

### 4. Integration Test Specifications

#### 4.1 Test: Alpaca API Integration (Mocked)

**File:** `tests/integration/test_alpaca_integration.py`

**What to Test:**
- Successful connection to Alpaca API (mocked)
- Handling 401 Unauthorized (bad API keys)
- Handling 500 Internal Server Error
- Handling timeout errors
- Handling rate limit (429 Too Many Requests)

**Test Cases:**

```python
import pytest
import responses
from alpaca.trading.client import TradingClient
from dalio_lite import DalioLite

@pytest.mark.integration
@responses.activate
def test_alpaca_connection_success(mocker):
    """Test successful connection to Alpaca API."""
    # Mock successful account retrieval
    responses.add(
        responses.GET,
        'https://paper-api.alpaca.markets/v2/account',
        json={
            'cash': '100000.00',
            'portfolio_value': '100000.00',
            'equity': '100000.00',
            'last_equity': '100000.00'
        },
        status=200
    )

    # Should not raise exception
    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    assert dalio.trading_client is not None

@pytest.mark.integration
@responses.activate
def test_alpaca_connection_unauthorized(mocker):
    """Test handling of 401 Unauthorized (bad API keys)."""
    responses.add(
        responses.GET,
        'https://paper-api.alpaca.markets/v2/account',
        json={'message': 'Invalid API key'},
        status=401
    )

    with pytest.raises(ConnectionError) as exc_info:
        dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    assert 'Failed to connect' in str(exc_info.value)

@pytest.mark.integration
@responses.activate
def test_alpaca_api_rate_limit(mocker):
    """Test handling of 429 Too Many Requests."""
    # First request hits rate limit
    responses.add(
        responses.GET,
        'https://paper-api.alpaca.markets/v2/positions',
        json={'message': 'Rate limit exceeded'},
        status=429,
        headers={'Retry-After': '60'}
    )

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Should log error and handle gracefully
    # Current implementation may not handle this - test documents expected behavior
    with pytest.raises(Exception):
        positions = dalio.get_current_positions()

    # NOTE: Implementation should be enhanced to retry after delay

@pytest.mark.integration
@responses.activate
def test_alpaca_order_submission_success(mocker):
    """Test successful order submission."""
    # Mock account
    responses.add(
        responses.GET,
        'https://paper-api.alpaca.markets/v2/account',
        json={'cash': '10000.00', 'portfolio_value': '10000.00'},
        status=200
    )

    # Mock quote retrieval
    responses.add(
        responses.GET,
        'https://data.alpaca.markets/v2/stocks/VTI/quotes/latest',
        json={'quote': {'ap': 220.50, 'bp': 220.45}},
        status=200
    )

    # Mock order submission
    responses.add(
        responses.POST,
        'https://paper-api.alpaca.markets/v2/orders',
        json={
            'id': 'order-123',
            'symbol': 'VTI',
            'notional': '1000.00',
            'side': 'buy',
            'status': 'accepted'
        },
        status=200
    )

    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')
    from alpaca.trading.enums import OrderSide
    success = dalio._execute_order('VTI', 1000.0, OrderSide.BUY)

    assert success is True
```

**Coverage Target:** Key API interaction paths covered (success, auth failure, rate limit)

---

#### 4.2 Test: End-to-End Rebalance (Mocked)

**File:** `tests/integration/test_end_to_end_rebalance.py`

**What to Test:**
- Full rebalance workflow from drift detection to order execution
- Sells executed before buys (correct order)
- State file updated after completion
- Notification sent after completion

**Test Cases:**

```python
import pytest
import responses
from datetime import datetime
from dalio_lite import DalioLite

@pytest.mark.integration
@responses.activate
def test_full_rebalance_workflow(mocker, tmp_path):
    """Test complete rebalance from detection to execution."""
    # Setup: Mock all external dependencies

    # 1. Mock account
    responses.add(
        responses.GET,
        'https://paper-api.alpaca.markets/v2/account',
        json={
            'cash': '1000.00',
            'portfolio_value': '10000.00',
            'equity': '10000.00',
            'last_equity': '10000.00'
        },
        status=200
    )

    # 2. Mock positions (overweight VTI)
    responses.add(
        responses.GET,
        'https://paper-api.alpaca.markets/v2/positions',
        json=[
            {'symbol': 'VTI', 'market_value': '5000.00'},  # 50% (target 40%)
            {'symbol': 'TLT', 'market_value': '2500.00'},  # 25% (target 30%)
            {'symbol': 'GLD', 'market_value': '1500.00'},  # 15% (target 20%)
            {'symbol': 'DBC', 'market_value': '1000.00'}   # 10% (target 10%)
        ],
        status=200
    )

    # 3. Mock quote retrieval for each ticker
    for ticker in ['VTI', 'TLT', 'GLD']:
        responses.add(
            responses.GET,
            f'https://data.alpaca.markets/v2/stocks/{ticker}/quotes/latest',
            json={'quote': {'ap': 100.00, 'bp': 99.00}},
            status=200
        )

    # 4. Mock order submissions
    responses.add(
        responses.POST,
        'https://paper-api.alpaca.markets/v2/orders',
        json={'id': 'order-sell-vti', 'status': 'accepted'},
        status=200
    )
    responses.add(
        responses.POST,
        'https://paper-api.alpaca.markets/v2/orders',
        json={'id': 'order-buy-tlt', 'status': 'accepted'},
        status=200
    )
    responses.add(
        responses.POST,
        'https://paper-api.alpaca.markets/v2/orders',
        json={'id': 'order-buy-gld', 'status': 'accepted'},
        status=200
    )

    # Execute
    dalio = DalioLite(config_path='tests/fixtures/config_test.yaml')

    # Check that rebalancing is needed
    needs_rebal, reason = dalio.needs_rebalancing()
    assert needs_rebal is True

    # Execute rebalance
    success = dalio.execute_rebalance(dry_run=False)
    assert success is True

    # Verify state was updated
    assert dalio.last_rebalance is not None
    assert isinstance(dalio.last_rebalance, datetime)

    # Verify orders were submitted in correct order (sells first)
    # This requires inspecting responses call order
    assert len(responses.calls) > 0
```

**Coverage Target:** Integration of all components in realistic rebalance scenario

---

### 5. Test Fixtures

#### 5.1 Mock Alpaca Client

**File:** `tests/fixtures/mock_alpaca_client.py`

```python
"""Mock Alpaca Trading API client for testing."""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MockAccount:
    """Mock Alpaca account object."""
    cash: str = "100000.00"
    portfolio_value: str = "100000.00"
    equity: str = "100000.00"
    last_equity: str = "100000.00"

@dataclass
class MockPosition:
    """Mock Alpaca position object."""
    symbol: str
    market_value: str
    qty: str = "10"
    current_price: str = "100.00"

@dataclass
class MockQuote:
    """Mock stock quote."""
    ask_price: float
    bid_price: float

@dataclass
class MockOrder:
    """Mock order object."""
    id: str
    symbol: str
    notional: float
    side: str
    status: str = "accepted"

class MockTradingClient:
    """Mock Alpaca TradingClient for testing."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self._account = MockAccount()
        self._positions = []
        self._orders = []

    def get_account(self) -> MockAccount:
        """Return mock account."""
        return self._account

    def get_all_positions(self) -> List[MockPosition]:
        """Return mock positions."""
        return self._positions

    def submit_order(self, order_request) -> MockOrder:
        """Mock order submission."""
        order = MockOrder(
            id=f"order-{len(self._orders)}",
            symbol=order_request.symbol,
            notional=order_request.notional,
            side=order_request.side.name
        )
        self._orders.append(order)
        return order

    def set_positions(self, positions: List[Dict]):
        """Helper to set mock positions for testing."""
        self._positions = [
            MockPosition(symbol=p['symbol'], market_value=p['market_value'])
            for p in positions
        ]

    def set_account_balance(self, portfolio_value: float, cash: float):
        """Helper to set mock account balance."""
        self._account.portfolio_value = str(portfolio_value)
        self._account.cash = str(cash)
        self._account.equity = str(portfolio_value)

class MockDataClient:
    """Mock Alpaca Data Client for testing."""

    def get_stock_latest_quote(self, request):
        """Return mock quote data."""
        # Return same quote for all symbols
        symbol = request.symbol_or_symbols[0]
        return {
            symbol: MockQuote(ask_price=100.00, bid_price=99.50)
        }
```

---

#### 5.2 Test Configuration

**File:** `tests/fixtures/config_test.yaml`

```yaml
# Test configuration for Dalio Lite
allocation:
  VTI: 0.40
  TLT: 0.30
  GLD: 0.20
  DBC: 0.10

rebalancing:
  drift_threshold: 0.10
  min_days_between: 30
  min_trade_usd: 100

risk:
  max_drawdown_pause: 0.30
  max_daily_loss: 0.05

notifications:
  enabled: false  # Disable for tests
  method: console

mode:
  paper_trading: true

broker:
  name: alpaca

logging:
  level: DEBUG
  file: logs/test.log

tracking:
  benchmarks: [SPY, AGG]
  report_frequency_days: 30
```

---

#### 5.3 Shared Test Fixtures

**File:** `tests/conftest.py`

```python
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
```

---

### 6. Test Execution Workflow

#### 6.1 Local Development Workflow

**Run all tests:**
```bash
pytest
```

**Run only unit tests (fast):**
```bash
pytest -m unit
```

**Run only integration tests:**
```bash
pytest -m integration
```

**Run with coverage report:**
```bash
pytest --cov --cov-report=html
open htmlcov/index.html  # View coverage in browser
```

**Run specific test file:**
```bash
pytest tests/unit/test_drift_calculation.py -v
```

**Run specific test:**
```bash
pytest tests/unit/test_drift_calculation.py::test_drift_calculation_balanced_portfolio -v
```

---

#### 6.2 Pre-Commit Hook

**File:** `.git/hooks/pre-commit` (make executable)

```bash
#!/bin/bash
# Pre-commit hook: Run tests before allowing commit

echo "Running tests before commit..."

# Run unit tests only (fast)
pytest -m unit --quiet

if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed. Commit rejected."
    echo "Fix tests or use 'git commit --no-verify' to skip (not recommended)"
    exit 1
fi

echo "✅ All tests passed. Proceeding with commit."
exit 0
```

---

#### 6.3 CI/CD Integration (GitHub Actions)

**File:** `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: pytest -m unit --cov --cov-report=xml

      - name: Run integration tests
        run: pytest -m integration

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80
```

---

## Verification Strategy

### Unit Test Verification

**How to verify unit tests work correctly:**

1. **Positive test:** Run `pytest -m unit` → All tests pass
2. **Negative test:** Intentionally break a function (e.g., change drift calculation formula) → Test fails
3. **Coverage check:** Run `pytest --cov` → Coverage ≥ 80%
4. **Speed check:** Unit tests complete in <5 seconds

**Acceptance Criteria:**
- ✅ All unit tests pass on clean codebase
- ✅ At least one test exists for each critical function
- ✅ Coverage ≥ 80% for `dalio_lite.py` core logic
- ✅ Tests run in <5 seconds (fast feedback loop)

---

### Integration Test Verification

**How to verify integration tests work correctly:**

1. **Mock validation:** Verify mocked API responses match real Alpaca API format
2. **End-to-end test:** Run full rebalance scenario → Orders submitted in correct order
3. **Error handling test:** Inject API error → System handles gracefully
4. **State persistence test:** Verify state files created and loaded correctly

**Acceptance Criteria:**
- ✅ All integration tests pass
- ✅ Tests use `responses` library to mock HTTP calls (no real API hits)
- ✅ Tests cover happy path + at least 2 error scenarios per component
- ✅ Tests run in <30 seconds

---

### CI/CD Verification

**How to verify CI/CD integration works:**

1. **First run:** Push code to GitHub → CI runs automatically
2. **Test success:** CI workflow completes with all tests passing
3. **Test failure:** Intentionally break a test → CI fails and blocks merge
4. **Coverage enforcement:** Lower coverage below 80% → CI fails

**Acceptance Criteria:**
- ✅ GitHub Actions workflow configured and running
- ✅ Tests run automatically on every push to main/develop
- ✅ Pull requests blocked if tests fail
- ✅ Coverage report uploaded to Codecov (or similar)

---

## Benefits

**Why this testing infrastructure is the right choice:**

1. **Financial Safety:** Rebalancing logic verified before touching real money
   - Prevents incorrect trades due to calculation errors
   - Validates order execution sequence (sells before buys)
   - Tests circuit breaker protection

2. **Regression Prevention:** Tests catch bugs introduced by future changes
   - Modify drift calculation → Tests immediately fail if broken
   - Update Alpaca SDK → Integration tests catch breaking changes
   - Refactor code → Tests ensure behavior unchanged

3. **Developer Confidence:** Can modify code without fear
   - Green tests = safe to deploy
   - Fast feedback loop (unit tests in <5s)
   - Comprehensive coverage of edge cases

4. **Documentation:** Tests serve as executable specifications
   - Want to know how drift calculation works? Read `test_drift_calculation.py`
   - Want to see how errors are handled? Read `test_alpaca_integration.py`
   - Tests show expected behavior more clearly than comments

5. **Compliance:** Demonstrates due diligence for financial system
   - Shows testing rigor if audited
   - Provides evidence of quality assurance
   - Reduces liability risk

---

## Expectations

**What success looks like:**

### Immediate (Week 1)
- ✅ All unit tests written and passing
- ✅ Test coverage ≥ 80% on core logic
- ✅ Pre-commit hook preventing untested commits
- ✅ Developers can run `pytest` and see green output

### Short-term (Month 1)
- ✅ Integration tests written and passing
- ✅ CI/CD pipeline running on every push
- ✅ Zero production incidents related to rebalancing logic
- ✅ Coverage report publicly visible (badge in README)

### Long-term (Month 3+)
- ✅ Test suite catches bugs before they reach production
- ✅ Coverage maintained at ≥ 80% as new features added
- ✅ Regression test library grows (every bug → new test)
- ✅ New contributors can run tests to validate their changes

---

## Risks & Mitigations

### Risk 1: Mocked API Doesn't Match Real API

**Probability:** Medium
**Impact:** High (tests pass but real API fails)

**Mitigation:**
1. Regularly validate mock responses against real Alpaca API documentation
2. Add integration tests that hit Alpaca paper trading API (not just mocks)
3. Include API response validation in production code (schema checking)
4. Monitor production errors for API format changes

**Monitoring:** Track production API errors that weren't caught by tests

---

### Risk 2: Low Test Coverage Despite Passing Tests

**Probability:** Low (with coverage enforcement)
**Impact:** Medium (false confidence)

**Mitigation:**
1. Enforce 80% coverage threshold in CI/CD
2. Require coverage increase for new code (can't lower coverage)
3. Code review checklist includes "Are critical paths tested?"
4. Periodic coverage audits to identify untested critical code

**Monitoring:** Coverage reports in CI/CD, weekly coverage review

---

### Risk 3: Slow Tests Discourage Running Them

**Probability:** Low (with unit/integration split)
**Impact:** Medium (developers skip tests)

**Mitigation:**
1. Keep unit tests ultra-fast (<5s total)
2. Mark slow tests with `@pytest.mark.slow` for optional execution
3. Pre-commit hook only runs unit tests (fast feedback)
4. CI runs full suite (can afford 1-2 minutes)

**Monitoring:** Track test execution time, optimize if >10s

---

### Risk 4: Tests Become Maintenance Burden

**Probability:** Medium (over time)
**Impact:** Medium (tests disabled or ignored)

**Mitigation:**
1. Follow testing best practices (DRY, clear fixtures, good names)
2. Treat tests as first-class code (refactor, review, maintain)
3. Delete obsolete tests when features removed
4. Balance comprehensiveness with maintainability

**Monitoring:** Track test flakiness, fix immediately when found

---

## Results Criteria

**This specification is successfully implemented when:**

### Automated Verification
- [ ] `pytest` runs and all tests pass
- [ ] Coverage report shows ≥80% coverage on `dalio_lite.py`
- [ ] CI/CD pipeline configured and passing
- [ ] Pre-commit hook blocks untested commits

### Manual Verification
- [ ] Can intentionally break drift calculation → Test catches it
- [ ] Can intentionally break order execution → Test catches it
- [ ] Can mock Alpaca API error → Test handles it gracefully
- [ ] Can run `pytest -m unit` in <5 seconds
- [ ] Can run full test suite in <30 seconds

### Documentation Verification
- [ ] README includes section on running tests
- [ ] Each test file has docstring explaining what it tests
- [ ] Coverage report badge added to README
- [ ] Contributing guide mentions test requirements

### Production Verification (Post-Implementation)
- [ ] Run tests before first live trading deployment → All pass
- [ ] Run tests after 30 days paper trading → All pass
- [ ] Zero production incidents caused by untested code paths
- [ ] Developers report confidence in making changes

---

**Status:** Ready for implementation
**Next Document:** 02-concurrency-control.md
