import csv

def save_dict_to_csv(data_dict, save_directory, filename):
    """
    Saves a dictionary to a CSV file with specified directory and filename.

    Args:
        data_dict (dict): The dictionary to be saved.
        save_directory (str): The directory where the CSV file should be saved.
        filename (str): The name of the CSV file (without the extension).

    Returns:
        None
    """
    file_path = f"{save_directory}/{filename}.csv"

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Symbol', 'Return'])  # Write header row

        for symbol, return_value in data_dict.items():
            writer.writerow([symbol, return_value])
    
    print(f"Dictionary saved to {file_path}")



def save_to_csv(df, symbol, filepath):
    """
    Saves stock data to a CSV file.

    Args:
        df (pandas.DataFrame): Stock data.
        symbol (str): Stock symbol or ticker.
        filepath (str): Path to the directory where the CSV file will be saved.

    """
    try:
        filename = f'{filepath}/{symbol}.csv'
        df.to_csv(filename, index=True)
        print(f"{symbol} data saved to {filename}.")
    except Exception as e:
        print(f"Error occurred while saving {symbol} data to a CSV file: {str(e)}")

        