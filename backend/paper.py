import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
import datetime
import logging
import uuid
from backend.broker import Broker
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


# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("paper_broker.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class PaperTradingBroker():
    """Paper Trading Broker class for simulating trading operations in a paper trading environment."""

    def __init__(self, balance: float, totp: str):
        """
        Initialize the PaperTradingBroker instance.

        Args:
            balance (float): The initial account balance for paper trading.
            totp (str): The Time-Based One-Time Password (TOTP) for authentication.
        """
        # Initialize instance variables
        self.name = 'Paper Trading'
        self.holdings = {}
        self.orders = [] # list of open orders
        self.executed_orders = []
        self.balance = balance
        self.INITIAL_BALANCE = balance
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
        self.DataFeed.load_conv_dict("/home/yeashu/project/AlgoTrading app/scrips/symbols2Scip.csv")
        self.DataFeed.login(totp)

    def buy_stock(self, symbol: str, quantity: int, stop_loss: float = None, limit: float = None):
        """
        Place a buy order for a specified quantity of a stock.

        Args:
            symbol (str): The symbol of the stock to buy.
            quantity (int): The number of shares to buy.
            stop_loss (float, optional): The price at which to sell the stock if it falls below this level.
            limit (float, optional): The maximum price at which to execute the buy order.

        Returns:
            list: A list of order IDs if the order was placed successfully, an empty list otherwise.
        """
        # Get the current price of the stock
        price = self.get_stock_price(symbol)
        if price <= 0:
            logger.error(f"Invalid price for {symbol}")
            return []


        if limit and limit < price:
            # Place a limit buy order
            cost = quantity * limit
            if cost > self.balance:
                logger.error(f"Insufficient balance to buy {quantity} shares of {symbol}")
                return []
            order = {
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "quantity": quantity,
                "price": limit,
                "type": "limit_buy",
                "status": "open",
            }
            logger.info(f"Placed a Limit Buy order for {quantity} shares of {symbol} at ${limit:.2f} per share")
        else:
            # Calculate the cost of the buy order
            cost = price * quantity
            if cost > self.balance:
                logger.error(f"Insufficient balance to buy {quantity} shares of {symbol}")
                return []
            # Place a regular buy order
            order = {
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "type": "buy",
                "status": "open",
            }
            logger.info(f"Placed a Buy order for {quantity} shares of {symbol} at {price:.2f} per share")

        # Add the order to the list of pending orders
        self.orders.append(order)
        order_ids = [order["id"]]
        self.balance -= cost
        self.execute_order()

        if stop_loss:
            if stop_loss > price:
                logger.error(f"SL_sell price given is greater than market price for {symbol}")
            # Place a stop-loss sell order
            stop_loss_order = {
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "quantity": quantity,
                "price": stop_loss,
                "type": "sl_sell",
                "status": "open",
            }
            self.orders.append(stop_loss_order)
            logger.info(f"Placed a SL Sell order for {quantity} shares of {symbol} at {stop_loss:.2f} per share")
            order_ids.append(stop_loss_order["id"])

        return order_ids

    def sell_stock(self, symbol: str, quantity: int, stop_loss: float = None, limit: float = None):
        """
        Place a sell order for a specified quantity of a stock.

        Args:
            symbol (str): The symbol of the stock to sell.
            quantity (int): The number of shares to sell.
            stop_loss (float, optional): The price at which to buy back the stock if it rises above this level.
            limit (float, optional): The minimum price at which to execute the sell order.

        Returns:
            bool: True if the order was placed successfully, False otherwise.
        """
        # Get the current price of the stock
        price = self.get_stock_price(symbol)
        if price <= 0:
            logger.error(f"Invalid price for {symbol}")
            return False

        if symbol not in self.holdings or quantity > self.holdings[symbol]:
            logger.error(f"Insufficient holdings to sell {quantity} shares of {symbol}")
            return False

        if limit and limit > price:
            # Place a limit sell order
            cost = quantity * limit
            order = {
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "quantity": quantity,
                "price": limit,
                "type": "limit_sell",
                "status": "open",
            }
            logger.info(f"Placed a Limit Sell order for {quantity} shares of {symbol} at ${limit:.2f} per share")
        else:
            # Place a regular sell order
            order = {
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "type": "sell",
                "status": "open",
            }
            logger.info(f"Placed a Sell order for {quantity} shares of {symbol} at {price:.2f} per share")

        # Add the order to the list of pending orders
        self.orders.append(order)
        self.holdings[symbol] -= quantity
        self.execute_order()

        if stop_loss:
            if stop_loss < price:
                logger.error(f"SL_buy price given is less than market price for {symbol}")
            # Place a stop-loss buy order
            stop_loss_order = {
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "quantity": quantity,
                "price": stop_loss,
                "type": "sl_buy",
                "status": "open",
            }
            self.orders.append(stop_loss_order)
            logger.info(f"Placed a SL Buy order for {quantity} shares of {symbol} at {stop_loss:.2f} per share")

        return True

    def get_stock_price(self, symbol: str = '', symbols: list = []):
        """
        Get the current price of a stock.

        Args:
            symbol (str, optional): The symbol of the stock. If not provided, returns the prices for all symbols in the list.
            symbols (list, optional): The list of symbols to retrieve prices for.

        Returns:
            float or dict: The current price of the stock if a symbol is provided, or a dictionary of symbol-price pairs.
        """
        try:
            if symbol:
                price = self.DataFeed.get_current_price([symbol])[symbol]
                return price
            else:
                prices = self.DataFeed.get_current_price(symbols)
                return prices

        except Exception as e:
            logger.error(f"Error occurred while getting stock price: {str(e)}")
            return 0.0

    def get_account_balance(self):
        """
        Get the current account balance in paper trading.

        Returns:
            float: The current account balance.
        """
        return self.balance

    def get_portfolio_holdings(self):
        """
        Get the current holdings in the portfolio.

        Returns:
            dict: A dictionary with the current holdings, as symbol-quantity pairs.
        """
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
        """
        Don`t use yet
        Place an order to buy or sell a stock with optional stop-loss and limit prices.

        Args:
            symbol (str): The symbol of the stock to buy or sell.
            quantity (int): The number of shares to buy or sell.
            order_type (str): The type of the order, either 'buy' or 'sell'.
            price (float): The price at which to place the order.
            stop_loss (float, optional): The price at which to exit the position if it goes against the order.
            limit (float, optional): The price at which to execute the order (for limit orders).

        Returns:
            list: A list of order IDs if the order was placed successfully, an empty list otherwise.
        """
        try:
            if order_type not in ["buy", "sell"]:
                logger.error(f"Invalid order type: {order_type}")
                return []

            if price <= 0:
                logger.error(f"Invalid price for {symbol}")
                return []

            if limit:
                # Place a limit order
                order = {
                    "id": str(uuid.uuid4()),
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": limit,
                    "type": "limit_" + order_type,
                    "status": "open",
                }
                logger.info(f"Placed a Limit {order_type.capitalize()} order for {quantity} shares of {symbol} at ${limit:.2f} per share")
            else:
                # Place a regular order
                order = {
                    "id": str(uuid.uuid4()),
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "type": order_type,
                    "status": "open",
                }
                logger.info(f"Placed a {order_type.capitalize()} order for {quantity} shares of {symbol} at ${price:.2f} per share")

            # Add the order to the list of pending orders
            self.orders.append(order)
            order_ids = [order["id"]]

            if stop_loss:
                # Place a stop-loss order
                stop_loss_order = {
                    "id": str(uuid.uuid4()),
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": stop_loss,
                    "type": "sl_sell" if order_type == "buy" else "sl_buy",
                    "status": "open",
                }
                self.orders.append(stop_loss_order)
                logger.info(
                    f"Placed a SL {'Sell' if order_type == 'buy' else 'Buy'} order for {quantity} shares of {symbol} at ${stop_loss:.2f} per share"
                )
                order_ids.append(stop_loss_order["id"])

            self.execute_order()

            return order_ids

        except ValueError as ve:
            logger.error(f"Invalid order: {str(ve)}")
            return []

        except Exception as e:
            logger.error(f"Error occurred while placing order: {str(e)}")
            return []

    def execute_order(self):
        """
        Execute the pending orders.

        This method executes the pending orders based on the current market conditions.
        """
        try:
            if self.get_market_status() != "Open":
                logger.info("Market is currently closed, orders will be executed when the market opens.")
                return

            for order in self.orders.copy():
                current_price = self.get_stock_price(order["symbol"])

                if order["type"] == "buy":
                    # Execute a buy order
                    #we have already subtracted the price when order was placed
                    if order["symbol"] in self.holdings:
                        self.holdings[order["symbol"]] += order["quantity"]
                    else:
                        self.holdings[order["symbol"]] = order["quantity"]
                    self.orders.remove(order)
                    logger.info(
                        f"Executed Buy order for {order['quantity']} shares of {order['symbol']} at ${order['price']:.2f} per share"
                    )

                elif order["type"] == "sell":
                    # Execute a sell order
                    self.balance += order["quantity"] * order["price"]
                    # holdings are already reduced when order is placed
                    if self.holdings[order['symbol']] == 0:
                        del self.holdings[order['symbol']]
                    self.orders.remove(order)
                    logger.info(
                        f"Executed Sell order for {order['quantity']} shares of {order['symbol']} at ${order['price']:.2f} per share"
                    )

                elif order["type"] == "limit_buy" and current_price <= order["price"]:
                    # Execute a limit buy order if the current price is at or below the limit price
                    # price already subtracted
                    if order["symbol"] in self.holdings:
                        self.holdings[order["symbol"]] += order["quantity"]
                    else:
                        self.holdings[order["symbol"]] = order["quantity"]
                    self.orders.remove(order)
                    logger.info(
                        f"Executed Limit Buy order for {order['quantity']} shares of {order['symbol']} at ${order['price']:.2f} per share"
                    )

                elif order["type"] == "limit_sell" and current_price >= order["price"]:
                    # Execute a limit sell order if the current price is at or above the limit price
                    self.balance += order["quantity"] * order["price"]
                    # holdings already reduced
                    if self.holdings[order['symbol']] == 0:
                        del self.holdings[order['symbol']]
                    self.orders.remove(order)
                    logger.info(
                        f"Executed Limit Sell order for {order['quantity']} shares of {order['symbol']} at ${order['price']:.2f} per share"
                    )

                elif order["type"] == "sl_sell" and current_price <= order["price"]:
                    # Execute a stop-loss sell order if the current price is at or below the stop-loss price
                    self.balance += order["quantity"] * order["price"]
                    self.holdings[order["symbol"]] -= order["quantity"]
                    if self.holdings[order['symbol']] == 0:
                        del self.holdings[order['symbol']]
                    self.orders.remove(order)
                    logger.info(
                        f"Executed SL Sell order for {order['quantity']} shares of {order['symbol']} at ${order['price']:.2f} per share"
                    )

                elif order["type"] == "sl_buy" and current_price >= order["price"]:
                    # Execute a stop-loss buy order if the current price is at or above the stop-loss price
                    self.balance -= order["quantity"] * order["price"]
                    if order["symbol"] in self.holdings:
                        self.holdings[order["symbol"]] += order["quantity"]
                    else:
                        self.holdings[order["symbol"]] = order["quantity"]
                    self.orders.remove(order)
                    logger.info(
                        f"Executed SL Buy order for {order['quantity']} shares of {order['symbol']} at ${order['price']:.2f} per share"
                    )

                if order in self.orders:
                    order["status"] = "open"
                else:
                    order["status"] = "filled"
                    self.executed_orders.append(order)

            logger.info("Checked orders for execution")

        except Exception as e:
            logger.error(f"Error occurred while executing orders: {str(e)}")

    def cancel_order(self, order_id: str):
        """
        Cancel an order.

        Args:
            order_id (str): The ID of the order to cancel.

        Returns:
            bool: True if the order was successfully canceled, False otherwise.
        """
        try:
            for order in self.orders:
                if order_id == order["id"]:
                    if "sl" in order["type"]:
                        # Cancel a stop-loss order
                        self.orders.remove(order)
                        logger.info(f"Cancelled SL order with ID: {order_id}")
                        return True
                    elif "buy" in order["type"]:
                        # Cancel a buy order
                        self.orders.remove(order)
                        self.balance += order["quantity"] * order["price"]
                        logger.info(f"Cancelled Buy order with ID: {order_id}")
                        return True
                    elif "sell" in order["type"]:
                        # Cancel a sell order
                        self.orders.remove(order)
                        self.holdings[order["symbol"]] += order["quantity"]
                        logger.info(f"Cancelled Sell order with ID: {order_id}")
                        return True

            logger.warning(f"Order with ID: {order_id} not found")
            return False

        except Exception as e:
            logger.error(f"Error occurred while canceling order: {str(e)}")
            return False

    def get_order_status(self, order_id: str):
        """
        Get the status of an order.

        Args:
            order_id (str): The ID of the order.

        Returns:
            str: The status of the order ('Open', 'Filled', or an error message).
        """
        try:
            for order in self.orders:
                if order_id == order["id"]:
                    return "Open"

            for order in self.executed_orders:
                if order_id == order["id"]:
                    return "Filled"

            return "Order with this order_id does not exist"

        except Exception as e:
            logger.error(f"Error occurred while getting order status: {str(e)}")
            return "Error occurred while getting order status"

    def get_available_assets(self):
        """
        Get the list of available tradable assets.

        Returns:
            list: A list of available tradable assets.
        """
        try:
            return list(self.DataFeed.symbol2scrip.keys())

        except Exception as e:
            logger.error(f"Error occurred while getting available assets: {str(e)}")
            return []

    def get_market_status(self):
        """
        Get the current market status.

        Returns:
            str: The current market status ('Open' or 'Closed').
        """
        try:
            current_time = datetime.datetime.now().time()
            market_open_time = datetime.time(9, 15)
            market_close_time = datetime.time(15, 30)

            if market_open_time <= current_time <= market_close_time:
                return "Open"
            else:
                return "Closed"

        except Exception as e:
            logger.error(f"Error occurred while getting market status: {str(e)}")
            return "Error occurred while getting market status"
        
    def __str__(self):
        """
        Get the string representation of the PaperTradingBroker object.

        Returns:
            str: The string representation of the PaperTradingBroker object.
        """
        return f"Paper Trading Broker with balance: {self.balance} and holdings: {self.holdings}"
    
    def get_open_orders(self):
        """
        Get the list of open orders.

        Returns:
            list: A list of open orders.
        """
        return self.orders

    def get_order_history(self):
        """
        Get the list of executed orders.

        Returns:
            list: A list of executed orders.
        """
        return self.executed_orders

    def get_account_summary(self):
        """
        Get the summary of the account, including balance, holdings, and portfolio returns.

        Returns:
            dict: A dictionary with the account summary.
        """
        account_balance = self.get_account_balance()
        portfolio_holdings = self.get_portfolio_holdings()
        portfolio_value = sum(
            self.get_stock_price(symbol) * quantity for symbol, quantity in portfolio_holdings.items()
        ) + account_balance
        portfolio_returns = (portfolio_value - self.INITIAL_BALANCE) / self.INITIAL_BALANCE * 100

        account_summary = {
            "balance": account_balance,
            "holdings": portfolio_holdings,
            "portfolio_returns": portfolio_returns,
        }
        return account_summary

