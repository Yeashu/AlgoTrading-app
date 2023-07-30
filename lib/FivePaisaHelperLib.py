import sys
import os
from threading import Lock
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from typing import List, Dict
import datetime
import pandas as pd
from py5paisa import FivePaisaClient
from csv import reader
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from lib.A_utils import convert_date_string

class FivePaisaWrapper:
    def __init__(
        self,
        APP_NAME: str,
        APP_SOURCE: int,
        USER_ID: str,
        PASSWORD: str,
        USER_KEY: str,
        ENCRYPTION_KEY: str,
        client_code: int,
        pin: int,
    ) -> None:
        """
        Initializes the FivePaisaWrapper object with the provided credentials and client information.

        Args:
            APP_NAME (str): The name of the 5paisa application.
            APP_SOURCE (int): The source ID of the application.
            USER_ID (str): The user ID of the user.
            PASSWORD (str): The password of the user.
            USER_KEY (str): The user key of the user.
            ENCRYPTION_KEY (str): The encryption key of the user.
            client_code (int): The client code associated with the user.
            pin (int): The PIN associated with the user.
        """
        self.cred = {
            "APP_NAME": APP_NAME,
            "APP_SOURCE": APP_SOURCE,
            "USER_ID": USER_ID,
            "PASSWORD": PASSWORD,
            "USER_KEY": USER_KEY,
            "ENCRYPTION_KEY": ENCRYPTION_KEY,
        }
        self.client = FivePaisaClient(cred=self.cred)
        self.client_code = client_code
        self.pin = pin
        self.symbol2scrip: Dict[str, str] = {}
        self.lock = Lock()

    def load_conv_dict(self, filepath: str) -> None:
        """
        Loads a dictionary mapping symbols to scrip codes from a CSV file.

        Args:
            filepath (str): The file path of the CSV file containing the symbol to scrip code mapping.
        """
        dictionary: Dict[str, str] = {}
        with open(filepath, "r") as csvfile:
            csv_reader = reader(csvfile)
            for row in csv_reader:
                key = row[0]
                value = row[1]
                dictionary[key] = value
        self.symbol2scrip = dictionary

    def login(self, totp: str) -> None:
        """
        Logs in to the 5paisa API with the provided TOTP and PIN.

        Args:
            totp (str): The TOTP (Time-based One-Time Password) for authentication.
        """
        self.client.get_totp_session(client_code=self.client_code, totp=totp, pin=self.pin)

    def _download_data(
        self,
        symbol: str,
        interval: str,
        start: str,
        end: str,
        Exch: str,
        ExchangeSegment: str,
        downloadedDataFrames: Dict[str, pd.DataFrame],
    ) -> None:
        """
        Private helper method to download data for a single symbol.

        Args:
            symbol (str): The symbol for which to download data.
            interval (str): The time interval of data (e.g., '1min', '5min', 'day').
            start (str): Start date of the data in 'YYYY-MM-DD' format.
            end (str): End date of the data in 'YYYY-MM-DD' format.
            Exch (str): The exchange code.
            ExchangeSegment (str): The exchange segment code.
            downloadedDataFrames (Dict[str, pd.DataFrame]): A dictionary to store the downloaded data for each symbol.
        """
        try:
            scrip = self.symbol2scrip[symbol]
        except KeyError:
            print(f'{symbol} does not exist in the Scrip Dict')
            return
        data = self.client.historical_data(
            Exch=Exch,
            ExchangeSegment=ExchangeSegment,
            ScripCode=scrip,
            time=interval,
            From=start,
            To=end,
        )

        if not data.empty:
            data.set_index("Datetime", inplace=True)
            data.index = pd.to_datetime(data.index)

        # Use lock to ensure thread safety when accessing shared resource
        with self.lock:
            if symbol in downloadedDataFrames:
                # If data for this symbol already exists, append new data
                downloadedDataFrames[symbol] = pd.concat(
                    [downloadedDataFrames[symbol], data]
                )
            else:
                # If this is the first batch of data for this symbol, just assign it
                downloadedDataFrames[symbol] = data

    def download(
        self,
        symbols: List[str],
        interval: str,
        start: str,
        end: str,
        Exch: str = "N",
        ExchangeSegment: str = "C",
        verbose: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """
        Download historical data for given symbols over a specified time range.

        Args:
            symbols (List[str]): List of symbols to download data for.
            interval (str): The time interval of data (e.g., '1min', '5min', 'day').
            start (str): Start date of the data in 'YYYY-MM-DD' format.
            end (str): End date of the data in 'YYYY-MM-DD' format.
            Exch (str, optional): The exchange code. Defaults to "N".
            ExchangeSegment (str, optional): The exchange segment code. Defaults to "C".
            verbose (bool, optional): If True, print progress information. Defaults to True.

        Returns:
            Dict[str, pd.DataFrame]: A dictionary containing the downloaded data for each symbol.
        """
        downloadedDataFrames: Dict[str, pd.DataFrame] = {}

        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = []
            for symbol in symbols:
                futures.append(
                    executor.submit(
                        self._download_data,
                        symbol,
                        interval,
                        start,
                        end,
                        Exch,
                        ExchangeSegment,
                        downloadedDataFrames,
                    )
                )

            if verbose:
                with tqdm(
                    total=len(futures),
                    ncols=80,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
                ) as pbar:
                    for future in futures:
                        future.result()
                        pbar.update(1)
            else:
                for future in futures:
                    future.result()

        return downloadedDataFrames

    def download_intraday_data(
        self,
        symbols: List[str],
        interval: str,
        start: datetime.datetime,
        end: datetime.datetime,
        Exch: str = "N",
        ExchangeSegment: str = "C",
        verbose: bool = True,
        batch_size: int = 175,
    ) -> Dict[str, pd.DataFrame]:
        """
        Download intraday data for given symbols over a specified time range.

        Args:
            symbols (List[str]): List of symbols to download data for.
            interval (str): The time interval of data (e.g., '1min', '5min', 'day').
            start (datetime.datetime): Start date and time of the data.
            end (datetime.datetime): End date and time of the data.
            Exch (str, optional): The exchange code. Defaults to "N".
            ExchangeSegment (str, optional): The exchange segment code. Defaults to "C".
            verbose (bool, optional): If True, print progress information. Defaults to True.
            batch_size (int, optional): The number of days to download data in each batch. Defaults to 175.

        Returns:
            Dict[str, pd.DataFrame]: A dictionary containing the downloaded intraday data for each symbol.
        """
        downloadedDataFrames: Dict[str, pd.DataFrame] = {}

        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = []
            for symbol in symbols:
                current_start = start
                while current_start < end:
                    current_end = current_start + datetime.timedelta(days=batch_size)
                    if current_end > end:
                        current_end = end

                    futures.append(
                        executor.submit(
                            self._download_data,
                            symbol,
                            interval,
                            current_start.strftime("%Y-%m-%d"),
                            current_end.strftime("%Y-%m-%d"),
                            Exch,
                            ExchangeSegment,
                            downloadedDataFrames,
                        )
                    )

                    current_start = current_end + datetime.timedelta(days=1)

            if verbose:
                with tqdm(
                    total=len(futures),
                    ncols=80,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
                ) as pbar:
                    for future in futures:
                        future.result()
                        pbar.update(1)
            else:
                for future in futures:
                    future.result()

        for symbol, df in downloadedDataFrames.items():
            # Sort the DataFrame by index (datetime) in ascending order
            downloadedDataFrames[symbol] = df.drop_duplicates().sort_index()

        return downloadedDataFrames

    def get_live_data(self, symbols: List[str]) -> Dict:
        """
        Retrieves live market data for the given symbols.

        Args:
            symbols (List[str]): List of symbols to retrieve live market data for.

        Returns:
            Dict: A dictionary containing the live market data for each symbol.
        """
        req = [
            {"Exchange": "N", "ExchangeType": "C", "Symbol": symbol}
            for symbol in symbols
        ]
        _data = self.client.fetch_market_depth_by_symbol(req)
        data = {}
        for i, symbol in enumerate(symbols):
            data[symbol] = _data["Data"][i]
        data["Time"] = convert_date_string(_data["TimeStamp"])

        return data

    def get_current_price(self, symbols: List[str]) -> Dict[str, float]:
        """
        Retrieves the current price for the given symbols.

        Args:
            symbols (List[str]): List of symbols to retrieve the current price for.

        Returns:
            Dict[str, float]: A dictionary containing the current price for each symbol.
        """
        ldata = self.get_live_data(symbols=symbols)
        del ldata["Time"]
        lprice = {}
        for symbol, data in ldata.items():
            lprice[symbol] = data["LastTradedPrice"]
        return lprice
