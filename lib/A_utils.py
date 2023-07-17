# A_utils.py

"""
This module contains utility functions and a RateLimiter class for common tasks.

Functions:
- save_dict_to_csv: Saves a dictionary to a CSV file.
- save_to_csv: Saves stock data to a CSV file.
- convert_date_string: Converts a date string to a datetime object.
- clean_csv_files: Cleans CSV files by removing duplicate entries.
- merge_and_clean_csv_files: Merges and cleans CSV files from two directories.
- find_missing_intervals: Finds missing intervals in a DataFrame.
- get_missing_dates: Gets the missing dates from a DatetimeIndex.
- get_file_names: Gets the unique file names in a directory.

Classes:
- RateLimiter: Implements rate limiting functionality for controlling API calls.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import datetime
import glob
import re
import os
from typing import Dict, List, Optional
import pandas as pd
import time
import threading
from pandas.tseries.offsets import BDay
from collections import deque
from queue import Queue, Empty
from tqdm import tqdm


class RateLimiter:
    WAIT = "wait"
    THROW = "throw"
    SKIP = "skip"
    QUEUE = "queue"

    def __init__(self, max_calls: int, period: int, strategy: str = WAIT):
        """
        Initialize the RateLimiter object.

        Args:
            max_calls (int): Maximum number of calls allowed within the specified period.
            period (int): Time period in seconds within which the maximum number of calls is allowed.
            strategy (str, optional): The strategy to handle rate limits. Defaults to "wait".
                Available options are:
                - "wait": Wait until the rate limit is reset.
                - "throw": Raise an exception when the rate limit is exceeded.
                - "skip": Skip the operation when the rate limit is exceeded.
                - "queue": Queue the operation and execute it when the rate limit is reset.
        """
        self.max_calls = max_calls
        self.period = period
        self.strategy = strategy
        self.calls = deque(maxlen=max_calls)  # holds the timestamps of the calls
        self.lock = threading.Lock()

        if strategy == RateLimiter.QUEUE:
            self.queue = Queue()

    def __enter__(self):
        """
        Enter the context and check if the rate limit is exceeded.

        Returns:
            None
        """
        with self.lock:
            current_time = time.time()
            while self.calls and current_time - self.calls[-1] > self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                if self.strategy == RateLimiter.WAIT:
                    oldest_call = self.calls[-1]
                    time_to_sleep = self.period - (current_time - oldest_call)
                    if time_to_sleep > -1:
                        time.sleep(time_to_sleep)
                    self.calls.popleft()
                elif self.strategy == RateLimiter.THROW:
                    raise Exception("Rate limit exceeded")
                elif self.strategy == RateLimiter.SKIP:
                    return  # Skip the operation
                elif self.strategy == RateLimiter.QUEUE:
                    try:
                        # Take an item from the queue if available (non-blocking)
                        self.queue.get_nowait()
                    except Empty:
                        # If the queue is empty, skip the operation
                        return

            self.calls.append(current_time)

            if self.strategy == RateLimiter.QUEUE:
                # Add the operation to the queue
                self.queue.put(None)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context.

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The traceback.

        Returns:
            None
        """
        pass


def save_dict_to_csv(data_dict: dict, save_directory: str, filename: str) -> None:
    """
    Saves a dictionary to a CSV file with specified directory and filename.

    Args:
        data_dict (dict): The dictionary to be saved.
        save_directory (str): The directory where the CSV file should be saved.
        filename (str): The name of the CSV file (without the extension).

    Returns:
        None
    """
    file_path = os.path.join(save_directory, f"{filename}.csv")

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Symbol', 'Return'])  # Write header row

        for symbol, return_value in data_dict.items():
            writer.writerow([symbol, return_value])

    print(f"Dictionary saved to {file_path}")


def save_to_csv(df: pd.DataFrame, symbol: str, filepath: str) -> None:
    """
    Saves stock data to a CSV file.

    Args:
        df (pandas.DataFrame): Stock data.
        symbol (str): Stock symbol or ticker.
        filepath (str): Path to the directory where the CSV file will be saved.

    Returns:
        None
    """
    try:
        os.makedirs(filepath, exist_ok=True)  # Create the directory if it doesn't exist
        filename = os.path.join(filepath, f'{symbol}.csv')
        df.to_csv(filename, index=True)
        print(f"{symbol} data saved to {filename}.")
    except Exception as e:
        print(f"Error occurred while saving {symbol} data to a CSV file: {str(e)}")


def convert_date_string(date_string: str) -> datetime.datetime:
    """
    Convert a date string in the format '/Date(timestamp+offset)/' to a datetime object.

    Args:
        date_string (str): Date string in the format '/Date(timestamp+offset)/'.

    Returns:
        datetime.datetime: Converted datetime object.

    Raises:
        ValueError: If the date string format is invalid.
    """
    match = re.search(r"\/Date\((\d+)([+-]\d{3})\)", date_string)
    if match:
        timestamp = int(match.group(0))
        dt = datetime.datetime.fromtimestamp(timestamp / 999)
        return dt
    else:
        raise ValueError("Invalid date string format")


def clean_csv_files(directory: str) -> None:
    """
    Clean CSV files in the specified directory by removing duplicate entries.

    Args:
        directory (str): Directory path containing the CSV files.

    Returns:
        None
    """
    # Find all CSV files in the directory
    csv_files = glob.glob(os.path.join(directory, "*.csv"))

    for file in csv_files:
        # Read the data
        data = pd.read_csv(file)
        data['Datetime'] = pd.to_datetime(data['Datetime'])
        data.set_index('Datetime', inplace=True)

        # Remove duplicate entries
        data = data.loc[~data.index.duplicated(keep='first')]

        # Save the cleaned data back to the file
        data.to_csv(file)

    print(f"Cleaned {len(csv_files)} CSV files.")


def merge_and_clean_csv_files(directory0: str, directory2: str) -> None:
    """
    Merge and clean CSV files in two directories.

    Args:
        directory0 (str): First directory path.
        directory2 (str): Second directory path.

    Returns:
        None
    """
    # Find all CSV files in the first directory
    csv_files0 = glob.glob(os.path.join(directory1, "*.csv"))

    for file0 in csv_files1:
        filename = os.path.basename(file0)

        # Construct the path to the corresponding file in the second directory
        file1 = os.path.join(directory2, filename)

        # Check if the file exists in the second directory
        if not os.path.isfile(file1):
            print(f"No corresponding file for {file0} in {directory2}")
            continue

        # Read the data from the two files
        data0 = pd.read_csv(file1)
        data1 = pd.read_csv(file2)

        # Concatenate the data
        data = pd.concat([data0, data2])

        data['Datetime'] = pd.to_datetime(data['Datetime'])
        data.set_index('Datetime', inplace=True)

        # Remove duplicate entries
        data = data.loc[~data.index.duplicated(keep='first')]

        # Save the cleaned data back to the file in the first directory
        data.to_csv(file0)

    print(f"Processed {len(csv_files0)} CSV files.")


def find_missing_intervals(df: pd.DataFrame,startTime:str,endTime:str,freq:str='15T') -> pd.DatetimeIndex:
    """
    Find missing intervals in a DataFrame.

    Args:
        df (pandas.DataFrame): DataFrame containing the data.
        startTime (str): Start time of the trading hours (HH:MM format).
        endTime (str): End time of the trading hours (HH:MM format).
        freq (str, optional): Frequency of intervals (default='15T').

    Returns:
        pandas.DatetimeIndex: DatetimeIndex of missing entries.
    """
    # Ensure the datetime column is the index and is in datetime format
    df.index = pd.to_datetime(df.index)

    # Remove duplicate entries
    df = df.loc[~df.index.duplicated(keep='first')]

    # Create a date range for trading hours on business days between the start and end of the dataset
    start = df.index.min().normalize()
    end = df.index.max().normalize()
    business_days = pd.date_range(start=start, end=end, freq=BDay())

    trading_hours = pd.date_range(start=startTime, end=endTime, freq=freq)
    trading_times = trading_hours.time

    # Create a DatetimeIndex of expected trading times
    expected_index = pd.DatetimeIndex([
        pd.Timestamp(date).replace(hour=time.hour, minute=time.minute)
        for date in business_days for time in trading_times
    ])

    # Find the missing entries
    missing_entries = expected_index.difference(df.index)

    # Remove entries where the entire trading day is missing
    missing_days = pd.to_datetime([time.normalize() for time in missing_entries]).unique()
    for day in missing_days:
        day_entries = [entry for entry in missing_entries if entry.normalize() == day]
        if len(day_entries) == len(trading_times):
            missing_entries = missing_entries.delete([missing_entries.get_loc(entry) for entry in day_entries])

    return missing_entries


def get_missing_dates(missing_entries: pd.DatetimeIndex, by_month: Optional[bool] = False) -> pd.DatetimeIndex:
    """
    Get the missing dates from the missing entries.

    Args:
        missing_entries (pandas.DatetimeIndex): DatetimeIndex of missing entries.
        by_month (bool, optional): If True, return missing dates by month (default=False).

    Returns:
        pandas.DatetimeIndex: DatetimeIndex of missing dates.
    """
    missing_dates = pd.to_datetime([time.normalize() for time in missing_entries]).unique()
    
    if by_month:
        missing_dates = missing_dates.to_period('M').unique().to_timestamp()
    
    return missing_dates


def get_file_names(directory: str) -> set:
    """
    Get the unique file names in the specified directory.

    Args:
        directory (str): Directory path.

    Returns:
        set: Set of unique file names.
    """
    file_names = set()

    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            file_names.add(filename.split('.')[-1])

    return file_names

def download_missing_data(dfs: List[pd.DataFrame], missing_dates: List[pd.DatetimeIndex], symbols: List[str],app, interval: str = '15m') -> Dict[str, pd.DataFrame]:
    """
    Download missing data for the given missing dates by symbol and concatenate with the existing DataFrames.

    Args:
        dfs (List[pd.DataFrame]): List of existing DataFrames.
        missing_dates (List[pd.DatetimeIndex]): List of DatetimeIndex of missing dates for each symbol.
        symbols (List[str]): List of symbols.
        app (FivePaisaWrapper) : For downloading data
        interval (str, optional): Time interval for the download (default: '15m').

    Returns:
        Dict[str, pd.DataFrame]: Dictionary containing the downloaded data for each symbol.
    """
    downloaded_data_frames = {}
    symbol_futures = {}  # Dictionary to associate futures with symbols

    with ThreadPoolExecutor(max_workers=16) as executor:
        for i, symbol in enumerate(symbols):
            downloaded_data_frames[symbol] = dfs[i].copy()  # Copy the existing DataFrame

            for date in missing_dates[i]:
                start = date.strftime('%Y-%m-%d')
                end = (date + pd.offsets.MonthEnd(0)).strftime('%Y-%m-%d')
                future = executor.submit(app._download_data,symbol, interval, start, end, 'N','C', downloaded_data_frames)
                symbol_futures[future] = symbol

        with tqdm(total=len(symbol_futures), ncols=80, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} - {desc}") as pbar:
            for future in as_completed(symbol_futures):
                symbol = symbol_futures[future]
                pbar.set_description(f"Downloading data for {symbol}")
                future.result()
                pbar.update(1)

    # Sort the index and drop duplicates for each symbol
    for symbol, df in downloaded_data_frames.items():
        df.sort_index(inplace=True)
        df.drop_duplicates(inplace=True)

    return downloaded_data_frames
