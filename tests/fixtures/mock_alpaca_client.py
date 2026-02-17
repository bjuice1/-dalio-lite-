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
