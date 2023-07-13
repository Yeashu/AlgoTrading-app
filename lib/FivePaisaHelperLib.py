from typing import List, Dict
import datetime
import threading
import time
import pandas as pd
from py5paisa import FivePaisaClient
from csv import reader
from tqdm import tqdm

from lib.A_utils import convert_date_string


class FivePaisaWrapper:
    apiRate: int = 500
    calls_per_minute: int = 0

    def __init__(self, APP_NAME: str, APP_SOURCE: int, USER_ID: str, PASSWORD: str, USER_KEY: str, ENCRYPTION_KEY: str, client_code: int, pin: int) -> None:
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
        self.symbol2scrip = {}

    def load_conv_dict(self, filepath: str) -> None:
        """
        Loads a dictionary mapping symbols to scrip codes from a CSV file.

        Args:
            filepath (str): The file path of the CSV file containing the symbol to scrip code mapping.
        """
        dictionary = {}
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

    def logged_in(self) -> bool:
        """
        Checks if the user is logged in to the 5paisa API.

        Returns:
            bool: True if the user is logged in, False otherwise.
        """
        return len(self.client.Login_check()) <= 40

    def scrip_download(self, Exch: str, ExchangeSegment: str, ScripCode: str, interval: str, start: str, end: str) -> pd.DataFrame:
        """
        Downloads historical data for a specific scrip from the 5paisa API.

        Args:
            Exch (str): The exchange of the scrip.
            ExchangeSegment (str): The exchange segment of the scrip.
            ScripCode (str): The scrip code of the scrip.
            interval (str): The time interval for the historical data.
            start (str): The start date for the historical data.
            end (str): The end date for the historical data.

        Returns:
            pandas.DataFrame: The downloaded historical data as a DataFrame.
        """
        return self.client.historical_data(Exch=Exch, ExchangeSegment=ExchangeSegment, ScripCode=ScripCode, time=interval, From=start, To=end)

    def _download_data(self, symbol: str, interval: str, start: str, end: str, Exch: str, ExchangeSegment: str, downloadedDataFrames: dict, verbose: bool, lock: threading.Lock) -> None:
        """
        Helper method for downloading data for a symbol within a specified time range.

        Args:
            symbol (str): The symbol for which to download data.
            interval (str): Interval of data (e.g., '1min', '5min', 'day').
            start (str): Start date of the data in the format 'YYYY-MM-DD'.
            end (str): End date of the data in the format 'YYYY-MM-DD'.
            Exch (str): Exchange code.
            ExchangeSegment (str): Exchange segment code.
            downloadedDataFrames (dict): Dictionary to store the downloaded data for each symbol.
            verbose (bool): Whether to print progress information.
            lock (threading.Lock): Lock for synchronizing access to the shared downloadedDataFrames dictionary.
        """
        if self.calls_per_minute >= self.apiRate:
            if verbose:
                print("API limit reached. Waiting for 60 seconds...")
            time.sleep(60)
            self.calls_per_minute = 0

        scrip = self.symbol2scrip[symbol]
        data = self.scrip_download(
            Exch=Exch,
            ExchangeSegment=ExchangeSegment,
            ScripCode=scrip,
            interval=interval,
            start=start,
            end=end,
        )

        data.set_index("Datetime", inplace=True)
        data.index = pd.to_datetime(data.index)

        downloadedDataFrames[symbol] = data

        lock.acquire()
        try:
            self.calls_per_minute += 1
        finally:
            lock.release()

    def download(self, symbols: List[str], interval: str, start: str, end: str, Exch: str = "N", ExchangeSegment: str = "C", resetRate: bool = True, verbose: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Downloads data for the given symbols and time range from the specified exchange using multithreading.

        Args:
            symbols (List[str]): List of symbols to download data for.
            interval (str): Interval of data (e.g., '1min', '5min', 'day').
            start (str): Start date of the data in the format 'YYYY-MM-DD'.
            end (str): End date of the data in the format 'YYYY-MM-DD'.
            Exch (str, optional): Exchange code. Default is 'N'.
            ExchangeSegment (str, optional): Exchange segment code. Default is 'C'.
            resetRate (bool, optional): Whether to reset the API call rate counter. Default is True.
            verbose (bool, optional): Whether to print progress information. Default is True.

        Returns:
            Dict[str, pd.DataFrame]: A dictionary containing the downloaded data for each symbol.
        """
        if resetRate:
            self.calls_per_minute = 0
        downloadedDataFrames = {}
        lock = threading.Lock()

        threads = []
        for symbol in symbols:
            thread = threading.Thread(target=self._download_data, args=(symbol, interval, start, end, Exch, ExchangeSegment, downloadedDataFrames, verbose, lock))
            thread.start()
            threads.append(thread)

        if verbose:
            print(f"Downloading data for {len(symbols)} symbols")

        # Use tqdm for progress feedback
        with tqdm(total=len(threads), ncols=80, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
            for thread in threads:
                thread.join()
                pbar.update(1)

        return downloadedDataFrames

    def download_intraday_data(self, symbols: List[str], interval: str, start: datetime.datetime, end: datetime.datetime, Exch: str = "N", ExchangeSegment: str = "C", verbose: bool = True, resetRate: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Downloads intraday data for the given symbols and time range from the specified exchange.

        Args:
            symbols (List[str]): List of symbols to download data for.
            interval (str): Interval of data (e.g., '1min', '5min', 'day').
            start (datetime.datetime): Start date and time of the data.
            end (datetime.datetime): End date and time of the data.
            Exch (str, optional): Exchange code. Default is 'N'.
            ExchangeSegment (str, optional): Exchange segment code. Default is 'C'.
            verbose (bool, optional): Whether to print progress information. Default is True.
            resetRate (bool, optional): Whether to reset the API call rate counter. Default is True.

        Returns:
            Dict[str, pd.DataFrame]: A dictionary containing the downloaded intraday data for each symbol.
        """
        if resetRate:
            self.calls_per_minute = 0
        downloadedDataFrames = {}
        lock = threading.Lock()

        threads = []
        for symbol in symbols:
            current_start = start
            while current_start < end:
                current_end = current_start + datetime.timedelta(days=175)
                if current_end > end:
                    current_end = end

                thread = threading.Thread(target=self._download_data, args=(symbol, interval, current_start.strftime("%Y-%m-%d"), current_end.strftime("%Y-%m-%d"), Exch, ExchangeSegment, downloadedDataFrames, verbose, lock))
                thread.start()
                threads.append(thread)

                current_start = current_end + datetime.timedelta(days=1)

        if verbose:
            print(f"Downloading data for {len(symbols)} symbols")

        # Use tqdm for progress feedback
        with tqdm(total=len(threads), ncols=80, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
            for thread in threads:
                thread.join()
                pbar.update(1)

        for symbol, df in downloadedDataFrames.items():
            downloadedDataFrames[symbol] = df.sort_index()

        return downloadedDataFrames
    
    def get_live_data(self, symbols: List[str]) -> Dict:
        """
        Retrieves live market data for the given symbols.

        Args:
            symbols (List[str]): List of symbols to retrieve live market data for.

        Returns:
            Dict: A dictionary containing the live market data for each symbol.
        """
        req=[{"Exchange":"N","ExchangeType":"C","Symbol":symbol} for symbol in symbols]
        _data = self.client.fetch_market_depth_by_symbol(req)
        data = {}
        for i,symbol in enumerate(symbols):
            data[symbol] = _data['Data'][i]
        data['Time'] = convert_date_string(_data['TimeStamp'])

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
        del ldata['Time']
        lprice = {}
        for symbol , data in ldata.items():
            lprice[symbol] = data['LastTradedPrice']
        return lprice
