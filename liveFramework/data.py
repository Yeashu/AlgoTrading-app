import pandas as pd
import numpy as np
class Data:
    def __init__(self,data:pd.DataFrame, stockName:str):
        # Set up any necessary configurations or parameters for data processing
        self.stockName = stockName
        #Add all the columns as numpy array
        for column in data.columns:
            setattr(self, column, data[column].values)
    
    def fetch_live_data(self):
        # Fetch live market data from the paper trading broker API
        # Implement the necessary code to retrieve live data
        pass
    
    def preprocess_data(self, raw_data):
        # Preprocess the raw data obtained from the API
        # Implement any required data cleaning or transformations
        pass
    
    def convert_to_numpy(self, processed_data):
        # Convert preprocessed data to NumPy arrays for faster performance
        # Implement the necessary code for conversion
        pass
    
    def calculate_metrics(self, data):
        # Calculate any required metrics or indicators from the live data
        # Implement the necessary code for metric calculations
        pass
