import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)
import datetime
import unittest
from unittest.mock import MagicMock, patch
from backend.paper import PaperTradingBroker


class PaperTradingBrokerTests(unittest.TestCase):
    def setUp(self):
        self.balance = 100000.0
        self.totp = "123456"
        self.broker = PaperTradingBroker(self.balance, self.totp)

    def test_buy_stock_sufficient_balance(self):
        symbol = "AAPL"
        quantity = 10
        stop_loss = 150.0
        limit = 160.0
        price = 155.0
        expected_holdings = {symbol: quantity}
        expected_balance = self.balance - (price * quantity)

        # Mock get_stock_price method to return a fixed price
        self.broker.get_stock_price = MagicMock(return_value=price)
        self.broker.get_market_status = MagicMock(return_value='Open')

        # Call the buy_stock method
        self.broker.buy_stock(symbol, quantity, stop_loss, limit)

        #holdings, and balance
        self.assertEqual(self.broker.holdings, expected_holdings)
        self.assertEqual(self.broker.balance, expected_balance)

    def test_buy_stock_insufficient_balance(self):
        symbol = "AAPL"
        quantity = 10
        stop_loss = 150.0
        limit = 160.0
        price = 155.0

        # Set the balance to a lower value than required
        self.broker.balance = price * (quantity - 1)

        # Call the buy_stock method
        order_ids = self.broker.buy_stock(symbol, quantity, stop_loss, limit)

        # Assert that the order was not placed due to insufficient balance
        self.assertEqual(order_ids, [])

    def test_sell_stock_valid_holding(self):
        symbol = "AAPL"
        quantity = 5
        stop_loss = 150.0
        limit = 160.0
        price = 165.0
        expected_holdings = {}
        expected_balance = self.balance + (price * quantity)

        # Set initial holdings for testing
        self.broker.holdings = {symbol: quantity}

        # Mock get_stock_price method to return a fixed price
        self.broker.get_stock_price = MagicMock(return_value=price)
        self.broker.get_market_status = MagicMock(return_value='Open')

        # Call the sell_stock method
        result = self.broker.sell_stock(symbol, quantity, stop_loss, limit)

        # Assert the result, holdings, and balance
        self.assertTrue(result)
        self.assertEqual(self.broker.holdings, expected_holdings)
        self.assertEqual(self.broker.balance, expected_balance)

    def test_sell_stock_invalid_holding(self):
        symbol = "AAPL"
        quantity = 5
        stop_loss = 150.0
        limit = 160.0
        price = 165.0

        # Call the sell_stock method without holdings
        self.broker.get_stock_price = MagicMock(return_value=price)
        result = self.broker.sell_stock(symbol, quantity, stop_loss, limit)

        # Assert that the order was not placed due to invalid holdings
        self.assertFalse(result)

    def test_get_stock_price(self):
        symbol = "AAPL"
        expected_price = 150.0

        # Mock get_current_price method to return a fixed price
        self.broker.DataFeed.get_current_price = MagicMock(return_value={symbol: expected_price})

        # Call the get_stock_price method
        price = self.broker.get_stock_price(symbol)

        # Assert the returned price
        self.assertEqual(price, expected_price)

    def test_get_account_balance(self):
        # Call the get_account_balance method
        balance = self.broker.get_account_balance()

        # Assert the account balance
        self.assertEqual(balance, self.balance)

    def test_get_portfolio_holdings(self):
        expected_holdings = {"AAPL": 10, "GOOG": 5}

        # Set the holdings for testing
        self.broker.holdings = expected_holdings

        # Call the get_portfolio_holdings method
        holdings = self.broker.get_portfolio_holdings()

        # Assert the returned holdings
        self.assertEqual(holdings, expected_holdings)

    def test_place_order(self):
        # first make place_order work 
        # second order are randomly generated it is never gonna work
        symbol = "AAPL"
        quantity = 10
        order_type = "buy"
        price = 155.0
        stop_loss = 150.0
        limit = 160.0
        expected_order_ids = ["1"]

        # Mock execute_order method
        self.broker.execute_order = MagicMock()

        # Call the place_order method
        order_ids = self.broker.place_order(symbol, quantity, order_type, price, stop_loss, limit)

        # Assert the order IDs
        self.assertEqual(order_ids, expected_order_ids)

    def test_execute_order_market_closed(self):
        # Mock get_market_status method to return "Closed"
        self.broker.get_market_status = MagicMock(return_value="Closed")

        # Mock execute_order method
        self.broker.execute_order = MagicMock()

        self.broker.get_stock_price = MagicMock(return_value=122)
        self.broker.buy_stock("APPL",10)

        # Call the execute_order method
        self.broker.execute_order()

        # Assert that execute_order does not execute order when market is closed
        self.assertFalse(len(self.broker.executed_orders))

    def test_cancel_order(self):
        order_id = "1"

        # Set initial orders for testing
        self.broker.orders = [{"id": order_id, "symbol": "AAPL", "quantity": 10, "price": 155.0, "type": "buy", "status": "open"}]

        # Call the cancel_order method
        result = self.broker.cancel_order(order_id)

        # Assert the result and orders
        self.assertTrue(result)
        self.assertEqual(len(self.broker.orders), 0)

    def test_get_order_status_open_order(self):
        order_id = "1"
        expected_status = "Open"

        # Set initial orders for testing
        self.broker.orders = [{"id": order_id, "symbol": "AAPL", "quantity": 10, "price": 155.0, "type": "buy", "status": "open"}]

        # Call the get_order_status method
        status = self.broker.get_order_status(order_id)

        # Assert the returned status
        self.assertEqual(status, expected_status)

    def test_get_order_status_filled_order(self):
        order_id = "1"
        expected_status = "Filled"

        # Set initial executed orders for testing
        self.broker.executed_orders = [{"id": order_id, "symbol": "AAPL", "quantity": 10, "price": 155.0, "type": "buy", "status": "filled"}]

        # Call the get_order_status method
        status = self.broker.get_order_status(order_id)

        # Assert the returned status
        self.assertEqual(status, expected_status)

    def test_get_order_status_nonexistent_order(self):
        order_id = "999"
        expected_status = "Order with this order_id does not exist"

        # Call the get_order_status method
        status = self.broker.get_order_status(order_id)

        # Assert the returned status
        self.assertEqual(status, expected_status)

    def test_get_available_assets(self):
        expected_assets = ["AAPL", "GOOG", "MSFT"]

        # Mock symbol2scrip attribute
        self.broker.DataFeed.symbol2scrip = {i:j for j,i in enumerate(expected_assets)}

        # Call the get_available_assets method
        assets = self.broker.get_available_assets()

        # Assert the returned assets
        self.assertEqual(assets, expected_assets)

    def test_get_market_status_open_market(self):
        # Mock datetime.now().time() to return a time within market hours
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now().time.return_value = datetime.time(10, 0, 0)  # Simulate market open time

            # Call the get_market_status method
            status = self.broker.get_market_status()

            # Assert the returned market status
            self.assertEqual(status, "Open")

    def test_get_market_status_closed_market(self):
        # Mock datetime.now().time() to return a time outside market hours
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now().time.return_value = datetime.time(18, 0, 0)  # Simulate market closed time

            # Call the get_market_status method
            status = self.broker.get_market_status()

            # Assert the returned market status
            self.assertEqual(status, "Closed")

    def test_str(self):
        expected_str = f"Paper Trading Broker with balance: {self.balance} and holdings: {self.broker.holdings}"

        # Call the __str__ method
        broker_str = str(self.broker)

        # Assert the returned string
        self.assertEqual(broker_str, expected_str)


if __name__ == "__main__":
    unittest.main()
