import uuid
from broker import Broker


class PaperTradingBroker(Broker):
    def __init__(self):
        self.account_balance = 100000.0  # Initial account balance for paper trading
        self.portfolio = {}  # Empty portfolio for paper trading
        self.orderBook = {}
        self.currentOrderId = 0

    def buy_stock(self, symbol: str, quantity: int, stop_loss: float) -> bool:
        """Buy a specified quantity of a stock with an optional stop-loss price.

        Args:
            symbol (str): The symbol of the stock to buy.
            quantity (int): The number of shares to buy.
            stop_loss (float): The price at which to sell the stock if it falls below this level.

        Returns:
            bool: True if the order was placed successfully, False otherwise.
        """
        # Get the current price of the stock
        price = self.get_stock_price(symbol)

        # Check if the price is valid
        if price <= 0:
            print(f"Invalid price for {symbol}")
            return False

        # Check if the balance is sufficient
        cost = price * quantity
        if cost > self.balance:
            print(f"Insufficient balance to buy {quantity} shares of {symbol}")
            return False

        # Create an order object with the details
        order = {
            "id": str(uuid.uuid4()), # Generate a unique id for the order
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "stop_loss": stop_loss,
            "type": "buy",
            "status": "open",
        }

        # Append the order to the list of orders
        self.orders.append(order)

        # Deduct the cost from the balance
        self.balance -= cost

        # Print a confirmation message
        print(f"Placed a buy order for {quantity} shares of {symbol} at ${price:.2f} per share")

        # Return True
        return True


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
        """Get the current holdings in the portfolio.

        Returns:
            dict: A dictionary with the current holdings, as symbol: quantity pairs.
        """
        # Return the holdings attribute
        return self.holdings


    def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str,
        price: float,
        stop_loss: float,
    ) -> bool:
        """Place an order to buy or sell a stock with optional stop-loss price.

        Args:
            symbol (str): The symbol of the stock to buy or sell.
            quantity (int): The number of shares to buy or sell.
            order_type (str): The type of the order, either 'buy' or 'sell'.
            price (float): The price at which to place the order.
            stop_loss (float): The price at which to exit the position if it goes against the order.

        Returns:
            bool: True if the order was placed successfully, False otherwise.
        """
        # Check if the order_type is valid
        if order_type not in ["buy", "sell"]:
            print(f"Invalid order type: {order_type}")
            return False

        # Check if the price is valid
        if price <= 0:
            print(f"Invalid price for {symbol}")
            return False

        # Create an order object with the details
        order = {
            "id": str(uuid.uuid4()), # Generate a unique id for the order
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "stop_loss": stop_loss,
            "type": order_type,
            "status": "open",
        }

        # Append the order to the list of orders
        self.orders.append(order)

        # Print a confirmation message
        print(f"Placed a {order_type} order for {quantity} shares of {symbol} at ${price:.2f} per share")

        # Return True
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
