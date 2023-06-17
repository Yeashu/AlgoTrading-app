from abc import ABC, abstractmethod


class Broker(ABC):
    @abstractmethod
    def buy_stock(self, symbol: str, quantity: int, stop_loss: float) -> bool:
        """Buy a specified quantity of a stock with an optional stop-loss price."""

    @abstractmethod
    def sell_stock(self, symbol: str, quantity: int, stop_loss: float) -> bool:
        """Sell a specified quantity of a stock with an optional stop-loss price."""

    @abstractmethod
    def get_stock_price(self, symbol: str) -> float:
        """Get the current price of a stock."""

    @abstractmethod
    def get_account_balance(self) -> float:
        """Get the current account balance."""

    @abstractmethod
    def get_portfolio_holdings(self) -> dict:
        """Get the current holdings in the portfolio."""

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str,
        price: float,
        stop_loss: float,
    ) -> bool:
        """Place an order to buy or sell a stock with optional stop-loss price."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a previously placed order."""

    @abstractmethod
    def get_order_status(self, order_id: str) -> str:
        """Get the status of a placed order."""

    @abstractmethod
    def get_available_assets(self) -> list:
        """Get the list of available tradable assets."""

    @abstractmethod
    def get_market_status(self) -> str:
        """Get the current market status (e.g., open, closed, pre-market, etc.)."""
    
    @abstractmethod
    def get_account_summary(self) -> dict:
        """Get the summary of the account."""

    @abstractmethod
    def get_open_orders(self) -> list:
        """Get the list of open orders that have not been executed or canceled."""

    @abstractmethod
    def get_order_history(
        self, start_date: str, end_date: str, symbol: str = None
    ) -> list:
        """Get the list of orders that have been executed or canceled in the past."""

    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the broker object."""
