from broker import Broker


class PaperTradingBroker(Broker):
    def __init__(self):
        self.account_balance = 100000.0  # Initial account balance for paper trading
        self.portfolio = {}  # Empty portfolio for paper trading

    def buy_stock(self, symbol: str, quantity: int, stop_loss: float = None) -> bool:
        # Simulate buying a stock in paper trading
        stock_price = self.get_stock_price(symbol)
        total_cost = stock_price * quantity

        if self.account_balance >= total_cost:
            if symbol in self.portfolio:
                self.portfolio[symbol] += quantity
            else:
                self.portfolio[symbol] = quantity

            self.account_balance -= total_cost
            return True
        else:
            return False

    def sell_stock(self, symbol: str, quantity: int, stop_loss: float = None) -> bool:
        # Simulate selling a stock in paper trading
        if symbol in self.portfolio and self.portfolio[symbol] >= quantity:
            stock_price = self.get_stock_price(symbol)
            total_sale = stock_price * quantity

            self.portfolio[symbol] -= quantity
            self.account_balance += total_sale
            return True
        else:
            return False

    def get_stock_price(self, symbol: str) -> float:
        # Simulate getting the stock price in paper trading
        # This can be implemented based on historical or simulated data
        # Implement it
        return -1.0

    def get_account_balance(self) -> float:
        # Return the current account balance in paper trading
        return self.account_balance

    def get_portfolio_holdings(self) -> dict:
        # Return the current portfolio holdings in paper trading
        return self.portfolio

    def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str,
        price: float = -1,
        stop_loss: float = None,
    ) -> bool:
        # Place an order in paper trading
        # Since it's paper trading, the order is considered successful without any actual execution
        return True

    def cancel_order(self, order_id: str) -> bool:
        # Cancel an order in paper trading
        # Since it's paper trading, the order cancellation is always successful
        return True

    def get_order_status(self, order_id: str) -> str:
        # Get the status of an order in paper trading
        # Since it's paper trading, we can assume that all orders are executed instantly
        return "Filled"

    def get_available_assets(self) -> list:
        # Return a list of available tradable assets in paper trading
        # This can be based on a predefined list of assets or simulated data
        return ["AAPL", "GOOG", "MSFT", "AMZN"]

    def get_market_status(self) -> str:
        # Return the current market status in paper trading
        # This can be based on predefined market hours or simulated data
        return "Open"
