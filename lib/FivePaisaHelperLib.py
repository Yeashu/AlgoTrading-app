import datetime
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

    def login(self, totp: int):
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

    def download(self, symbols, interval, start, end, Exch='N', ExchangeSegment='C',verbose=True):
        """
        Downloads historical data for multiple symbols from the 5paisa API.

        Args:
            symbols (list): A list of symbols for which to download historical data.
            interval (str): The time interval for the historical data.
            start (str): The start date for the historical data.
            end (str): The end date for the historical data.
            Exch (str, optional): The exchange of the symbols. Defaults to 'N'.
            ExchangeSegment (str, optional): The exchange segment of the symbols. Defaults to 'C'.
            verbose (bool, optional): If true prints the tasks currently performing. Defaults to True

        Returns:
            dict: A Dictionary of downloaded historical data using symbols as keys and DataFrames as values.
        """
        downloadedDataFrames = {}
        for symbol in symbols:
            # Implement API call limit
            if self.calls_per_minute >= 50:
                time.sleep(60)  # Pause for 60 seconds (1 minute)
                self.calls_per_minute = 0
            
            if verbose:
                print(f'Downloading {symbol} data')

            scrip = self.symbol2scrip[symbol]
            downloadedDataFrames[symbol] = self.scrip_download(Exch=Exch, ExchangeSegment=ExchangeSegment,
                                                               ScripCode=scrip, interval=interval,
                                                               start=start, end=end).set_index('Datetime',inplace=True)
            self.calls_per_minute += 1
        return downloadedDataFrames

    def download_intraday_data(self, symbols, interval, start: datetime.datetime, end: datetime.datetime, Exch='N', ExchangeSegment='C',verbose=True):
        """
        Downloads intraday data for multiple symbols from the 5paisa API in batches of 5 months.

        Args:
            symbols (list): A list of symbols for which to download intraday data.
            interval (str): The time interval for the intraday data.
            start (str): The start date for the intraday data.
            end (str): The end date for the intraday data.
            Exch (str, optional): The exchange of the symbols. Defaults to 'N'.
            ExchangeSegment (str, optional): The exchange segment of the symbols. Defaults to 'C'.
            verbose (bool, optional): If true prints the tasks currently performing. Defaults to True

        Returns:
            dict: A Dictionary of downloaded intraday historical data using symbols as keys and DataFrames as values.
        """
        downloadedDataFrames = {}
        for symbol in symbols:
            # Split the date range into batches of 5 months
            current_start = start
            if verbose:
                print(f'Downloading {symbol} data')
            while current_start < end:
                # Implement API call limit
                if self.calls_per_minute >= 50:
                    if verbose:
                        print('Api limit reached waiting for 60sec')
                    time.sleep(60)  # Pause for 60 seconds (1 minute)
                    self.calls_per_minute = 0

                current_end = current_start + datetime.timedelta(days=175)
                if current_end > end:
                    current_end = end

                # Download historical data for the current batch
                scrip = self.symbol2scrip[symbol]
                data = self.scrip_download(Exch=Exch, ExchangeSegment=ExchangeSegment, ScripCode=scrip,
                                           interval=interval, start=current_start.strftime("%Y-%m-%d"),
                                           end=current_end.strftime("%Y-%m-%d"))
                self.calls_per_minute += 1

                #set date column as index
                data.set_index('Datetime',inplace=True)
                # Store the downloaded data
                if symbol not in downloadedDataFrames:
                    downloadedDataFrames[symbol] = data
                else:
                    # Concatenate the data if the symbol already exists in the dictionary
                    downloadedDataFrames[symbol] = pd.concat([downloadedDataFrames[symbol], data])

                # Increment the current_start for the next batch
                current_start = current_end + datetime.timedelta(days=1)

        return downloadedDataFrames
