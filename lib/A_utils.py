import csv
import datetime
import re
import os

import pandas as pd

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

    """
    try:
        os.makedirs(filepath, exist_ok=True)  # Create the directory if it doesn't exist
        filename = os.path.join(filepath, f'{symbol}.csv')
        df.to_csv(filename, index=True)
        print(f"{symbol} data saved to {filename}.")
    except Exception as e:
        print(f"Error occurred while saving {symbol} data to a CSV file: {str(e)}")


def convert_date_string(date_string):
    match = re.search(r"\/Date\((\d+)([+-]\d{4})\)", date_string)
    if match:
        timestamp = int(match.group(1))
        dt = datetime.datetime.fromtimestamp(timestamp / 1000)
        return dt
    else:
        raise ValueError("Invalid date string format") 