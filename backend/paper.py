import uuid
from broker import Broker
from ApiKeys.secrets5p import (
    APP_NAME,
    APP_SOURCE,
    PASSWORD,
    ENCRYPTION_KEY,
    USER_ID,
    USER_KEY,
    client_code,
    Pin,
)
from lib.FivePaisaHelperLib import FivePaisaWrapper

class PaperTradingBroker(Broker):
    def __init__(self,balance: int,totp: str):
        self.name = 'Paper Trading'
        self.holdings = {} # The current portfolio holdings as a dictionary of symbol: quantity pairs
        self.orders = [] # The list of open orders as order objects
        self.ExecutedOrders = [] # The list for executed order
        self.balance = 100000.0  # Initial account balance for paper trading
        #Using five paisa for live data
        self.DataFeed = FivePaisaWrapper(
            APP_NAME=APP_NAME,
            APP_SOURCE=APP_SOURCE,
            USER_KEY=USER_KEY,
            USER_ID=USER_ID,
            PASSWORD=PASSWORD,
            ENCRYPTION_KEY=ENCRYPTION_KEY,
            client_code=client_code,
            pin=Pin,
        )
        self.DataFeed.load_conv_dict(
            "/home/yeashu/project/AlgoTrading app/scrips/symbols2Scip.csv"
        )
        self.DataFeed.login(totp)

        
    def buy_stock(self, symbol: str, quantity: int, stop_loss: float=None, Limit: float=None):
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

        if Limit:
            cost = quantity*Limit
            # Create an order object with the details
            order = {
                "id": str(uuid.uuid4()), # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": Limit,
                "type": "limit_buy",
                "status": "open",
            }
        else:
            # Create an order object with the details
            order = {
                "id": str(uuid.uuid4()), # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "type": "buy",
                "status": "open",
            }

        # Append the order to the list of orders
        self.orders.append(order)
        orderIds = [order["id"]]

        # Deduct the cost from the balance
        self.balance -= cost

        # Print a confirmation message
        print(f"Placed a buy order for {quantity} shares of {symbol} at ${price:.2f} per share")

        if stop_loss:
            order = {
                "id": str(uuid.uuid4()), # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": stop_loss,
                "type": "sl_sell",
                "status": "open",
            }
            self.orders.append(order)
            print(f"Placed a Sl Sell order for {quantity} shares of {symbol} at ${price:.2f} per share")
            orderIds.append(order["id"])

        return orderIds


    def sell_stock(self, symbol: str, quantity: int, stop_loss: float=None, Limit:float=None):
        """Sell a specified quantity of a stock with an optional stop-loss price.

        Args:
            symbol (str): The symbol of the stock to sell.
            quantity (int): The number of shares to sell.
            stop_loss (float): The price at which to buy back the stock if it rises above this level.

        Returns:
            bool: True if the order was placed successfully, False otherwise.
        """
        # Get the current price of the stock
        price = self.get_stock_price(symbol)

        # Check if the price is valid
        if price <= 0:
            print(f"Invalid price for {symbol}")
            return False

        # Check if the holdings are sufficient
        if symbol not in self.holdings or quantity > self.holdings[symbol]:
            print(f"Insufficient holdings to sell {quantity} shares of {symbol}")
            return False

        if Limit:
            cost = quantity*Limit
            # Create an order object with the details
            order = {
                "id": str(uuid.uuid4()), # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": Limit,
                "type": "limit_sell",
                "status": "open",
            }
        else:
            # Create an order object with the details
            order = {
                "id": str(uuid.uuid4()), # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "type": "sell",
                "status": "open",
            }
        # Append the order to the list of orders
        self.orders.append(order)
        self.holdings[symbol] -= quantity

        # Print a confirmation message
        print(f"Placed a sell order for {quantity} shares of {symbol} at ${price:.2f} per share")

        if stop_loss:
            order = {
                "id": str(uuid.uuid4()), # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": stop_loss,
                "type": "sl_buy",
                "status": "open",
            }
            self.orders.append(order)
            print(f"Placed a Sl Sell order for {quantity} shares of {symbol} at ${price:.2f} per share")
        
        return True

    def get_stock_price(self, symbol: str = '',symbols:list = []) -> float|dict:
        # Uses 5paisa for live data     
        if symbol:
            price = self.DataFeed.get_current_price(symbol)[symbol]
            return price
        else:
            prices = self.DataFeed.get_current_price(symbols)
            return prices

    def get_account_balance(self) -> float:
        # Return the current account balance in paper trading
        return self.balance

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
        stop_loss: float = None,
        limit: float = None,
    ):
        """Place an order to buy or sell a stock with optional stop-loss and limit prices.

        Args:
            symbol (str): The symbol of the stock to buy or sell.
            quantity (int): The number of shares to buy or sell.
            order_type (str): The type of the order, either 'buy' or 'sell'.
            price (float): The price at which to place the order.
            stop_loss (float, optional): The price at which to exit the position if it goes against the order.
            limit (float, optional): The price at which to execute the order (for limit orders).

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
        
        if limit:
            order = {
                "id": str(uuid.uuid4()),  # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": limit,
                "type": "limit_"+order_type,
                "status": "open",
            }
            print(f"Placed a Limit order for {quantity} shares of {symbol} at ${limit:.2f} per share")
        
        else:
            # Create an order object with the details
            order = {
                "id": str(uuid.uuid4()),  # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "type": order_type,
                "status": "open",
            }
            print(f"Placed a {order_type} order for {quantity} shares of {symbol} at ${price:.2f} per share")

        # Append the order to the list of orders
        self.orders.append(order)
        order_ids = [order["id"]]

        # Print a confirmation message

        if stop_loss:
            stop_loss_order = {
                "id": str(uuid.uuid4()),  # Generate a unique id for the order
                "symbol": symbol,
                "quantity": quantity,
                "price": stop_loss,
                "type": "sl_sell",
                "status": "open",
            }
            self.orders.append(stop_loss_order)
            print(f"Placed a SL Sell order for {quantity} shares of {symbol} at ${stop_loss:.2f} per share")
            order_ids.append(stop_loss_order["id"])


        return order_ids



    def cancel_order(self, order_id: str) -> bool:
        # Cancel an order in paper trading
        for order in self.orders:
            if order_id == order['id']:
                if 'sl' in order['type']:
                    self.orders.remove(order)
                    return True
                elif 'buy' in order['type']:
                    self.orders.remove(order)
                    self.balance += order['quantity'] * order['price']
                    return True
                elif 'sell' in order['type']:
                    self.orders.remove(order)
                    self.holdings[order['symbol']] += order['quantity']
                    return True
        
        return False

    def get_order_status(self, order_id: str) -> str:
        # Get the status of an order in paper trading
        # Since it's paper trading, we can assume that all orders are executed instantly
        return "Filled"

    def get_available_assets(self) -> list:
        # Return a list of available tradable assets in paper trading
        # This can be based on a predefined list of assets or simulated data
        return list(self.DataFeed.symbol2scrip.keys())

    def get_market_status(self) -> str:
        # Return the current market status in paper trading
        # This can be based on predefined market hours or simulated data
        return "Open"
