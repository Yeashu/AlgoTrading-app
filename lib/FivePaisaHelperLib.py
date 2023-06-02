import datetime
import threading
import time
import pandas as pd
from py5paisa import FivePaisaClient
from csv import reader


class FivePaisaWrapper:
    """
    A class that wraps the functionality of the py5paisa library for accessing and downloading data from the 5paisa API.

    Attributes:
        cred (dict): A dictionary containing the user credentials.
        client (FivePaisaClient): An instance of the FivePaisaClient class for interacting with the 5paisa API.
        client_code (int): The client code associated with the user.
        pin (int): The PIN associated with the user.
        symbol2scrip (dict): A dictionary mapping symbols to scrip codes.

    Methods:
        __init__(self, APP_NAME, APP_SOURCE, USER_ID, PASSWORD, USER_KEY, ENCRYPTION_KEY, client_code, pin):
            Initializes the FivePaisaWrapper object with the provided credentials and client information.

        load_conv_dict(self, filepath):
            Loads a dictionary mapping symbols to scrip codes from a CSV file.

        login(self, totp):
            Logs in to the 5paisa API with the provided TOTP and PIN.

        logged_in(self):
            Checks if the user is logged in to the 5paisa API.

        scrip_download(self, Exch, ExchangeSegment, ScripCode, interval, start, end):
            Downloads historical data for a specific scrip from the 5paisa API.

        download(self, symbols, interval, start, end, Exch='N', ExchangeSegment='C'):
            Downloads historical data for multiple symbols from the 5paisa API.

        download_intraday_data(self, symbols, interval, start, end, Exch='N', ExchangeSegment='C'):
            Downloads intraday data for multiple symbols from the 5paisa API in batches of 5 months.
    """
    apiRate = 500
    calls_per_minute = 0

    def __init__(self, APP_NAME: str, APP_SOURCE: int, USER_ID: str, PASSWORD: str, USER_KEY: str, ENCRYPTION_KEY: str,
                 client_code: int, pin: int):
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
            "ENCRYPTION_KEY": ENCRYPTION_KEY
        }
        self.client = FivePaisaClient(cred=self.cred)
        self.client_code = client_code
        self.pin = pin
        self.symbol2scrip = {}

    def load_conv_dict(self, filepath):
        """
        Loads a dictionary mapping symbols to scrip codes from a CSV file.

        Args:
            filepath (str): The file path of the CSV file containing the symbol to scrip code mapping.
        """
        # Load the dictionary from the CSV file
        dictionary = {}
        with open(filepath, 'r') as csvfile:
            csv_reader = reader(csvfile)
            for row in csv_reader:
                key = row[0]
                value = row[1]
                dictionary[key] = value
        self.symbol2scrip = dictionary

    def login(self, totp: str):
        """
        Logs in to the 5paisa API with the provided TOTP and PIN.

        Args:
            totp (int): The TOTP (Time-based One-Time Password) for authentication.
        """
        self.client.get_totp_session(client_code=self.client_code, totp=totp, pin=self.pin)

    def logged_in(self):
        """
        Checks if the user is logged in to the 5paisa API.

        Returns:
            bool: True if the user is logged in, False otherwise.
        """
        if 40 < len(self.client.Login_check()):
            return False
        else:
            return True

    def scrip_download(self, Exch, ExchangeSegment, ScripCode, interval, start, end):
        """
        Downloads historical data for a specific scrip from the 5paisa API.

        Args:
            Exch (str): The exchange of the scrip.
            ExchangeSegment (str): The exchange segment of the scrip.
            ScripCode (int): The scrip code of the scrip.
            interval (str): The time interval for the historical data.
            start (str): The start date for the historical data.
            end (str): The end date for the historical data.

        Returns:
            pandas.DataFrame: The downloaded historical data as a DataFrame.
        """

        return self.client.historical_data(Exch=Exch, ExchangeSegment=ExchangeSegment, ScripCode=ScripCode,
                                           time=interval, From=start, To=end)

    def download(self, symbols: list, interval, start, end, Exch='N', ExchangeSegment='C', resetRate: bool = True, verbose: bool = True):
        """
        Downloads data for the given symbols and time range from the specified exchange uses multithreading.
        
        Args:
            symbols (list): List of symbols to download data for.
            interval: Interval of data (e.g., '1min', '5min', 'day').
            start: Start date of the data in the format 'YYYY-MM-DD'.
            end: End date of the data in the format 'YYYY-MM-DD'.
            Exch (str, optional): Exchange code. Default is 'N'.
            ExchangeSegment (str, optional): Exchange segment code. Default is 'C'.
            resetRate (bool, optional): Whether to reset the API call rate counter. Default is True.
            verbose (bool, optional): Whether to print progress information. Default is True.
        
        Returns:
            dict: A dictionary containing the downloaded data for each symbol.
        """
        
        if resetRate:
            self.calls_per_minute = 0
        downloadedDataFrames = {}
        lock = threading.Lock()  # we are not locking for data as each worker function modifies a unique key of the dict
    
        def download_data(symbol):
            nonlocal downloadedDataFrames
    
            # Implement API call limit
            if self.calls_per_minute >= self.apiRate:
                time.sleep(60)  # Pause for 60 seconds (1 minute)
                self.calls_per_minute = 0
    
            if verbose:
                print(f'Downloading {symbol} data')
    
            scrip = self.symbol2scrip[symbol]
            data = self.scrip_download(Exch=Exch, ExchangeSegment=ExchangeSegment, ScripCode=scrip,
                                       interval=interval, start=start, end=end)
    
            # Set date column as index
            data.set_index('Datetime', inplace=True)
    
            # Not locking but can Acquire lock to update the shared downloadedDataFrames dictionary here 
            downloadedDataFrames[symbol] = data
    
            lock.acquire()
            try:
                self.calls_per_minute += 1
            finally:
                lock.release()
    
        if verbose:
            print(f'Downloading data for {len(symbols)} symbols')
    
        threads = []
        for symbol in symbols:
            # Spawn a thread to download data for each symbol
            thread = threading.Thread(target=download_data, args=(symbol,))
            thread.start()
            threads.append(thread)
    
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
    
        return downloadedDataFrames


    def download_intraday_data(self, symbols: list, interval, start: datetime.datetime, end: datetime.datetime, Exch='N', ExchangeSegment='C', verbose: bool = True, resetRate: bool = True):
        """
        Downloads intraday data for the given symbols and time range from the specified exchange.

        Args:
            symbols (list): List of symbols to download data for.
            interval: Interval of data (e.g., '1min', '5min', 'day').
            start (datetime.datetime): Start date and time of the data.
            end (datetime.datetime): End date and time of the data.
            Exch (str, optional): Exchange code. Default is 'N'.
            ExchangeSegment (str, optional): Exchange segment code. Default is 'C'.
            verbose (bool, optional): Whether to print progress information. Default is True.
            resetRate (bool, optional): Whether to reset the API call rate counter. Default is True.

        Returns:
            dict: A dictionary containing the downloaded intraday data for each symbol.
        """
        if resetRate:
            self.calls_per_minute = 0
        downloadedDataFrames = {}
        lock = threading.Lock()  # Lock to synchronize access to downloadedDataFrames

        def download_data(symbol, current_start, current_end):
            """
            Downloads intraday data for a symbol within a given time range.

            Args:
                symbol (str): The symbol for which to download data.
                current_start (datetime.datetime): The start date and time of the current batch.
                current_end (datetime.datetime): The end date and time of the current batch.
            """
            nonlocal downloadedDataFrames
            nonlocal lock

            # Implement API call limit
            if self.calls_per_minute >= self.apiRate:
                if verbose:
                    print('API limit reached. Waiting for 60 seconds...')
                time.sleep(60)  # Pause for 60 seconds (1 minute)
                self.calls_per_minute = 0

            # Download historical data for the current batch
            scrip = self.symbol2scrip[symbol]
            data = self.scrip_download(Exch=Exch, ExchangeSegment=ExchangeSegment, ScripCode=scrip,
                                       interval=interval, start=current_start.strftime("%Y-%m-%d"),
                                       end=current_end.strftime("%Y-%m-%d"))
            self.calls_per_minute += 1

            # Set date column as index
            data.set_index('Datetime', inplace=True)
            data.index = pd.to_datetime(data.index)

            # Store the downloaded data in a local dictionary
            local_dict = {symbol: data}

            # Acquire lock to update the shared downloadedDataFrames dictionary
            lock.acquire()
            try:
                for key, value in local_dict.items():
                    if key not in downloadedDataFrames:
                        downloadedDataFrames[key] = value
                    else:
                        # Concatenate the data if the symbol already exists in the dictionary
                        downloadedDataFrames[key] = pd.concat([downloadedDataFrames[key], value])
            finally:
                lock.release()

        if verbose:
            print(f'Downloading data for {len(symbols)} symbols')

        threads = []
        for symbol in symbols:
            # Split the date range into batches of 5 months
            current_start = start
            if verbose:
                print(f'Downloading {symbol} data')

            while current_start < end:
                current_end = current_start + datetime.timedelta(days=175)
                if current_end > end:
                    current_end = end

                # Spawn a thread to download data for the current batch
                thread = threading.Thread(target=download_data, args=(symbol, current_start, current_end))
                thread.start()
                threads.append(thread)

                # Increment the current_start for the next batch
                current_start = current_end + datetime.timedelta(days=1)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Sort the downloaded data by index (Datetime)
        for symbol, df in downloadedDataFrames.items():
            downloadedDataFrames[symbol] = df.sort_index()

        return downloadedDataFrames
