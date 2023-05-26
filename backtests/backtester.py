from backtesting import Backtest
from startegies import RTBollingerBands
import pandas as pd

#backtesting startegies
def main():
    # Read data from a CSV file into a DataFrame
    df = pd.read_csv('/home/yeashu/project/AlgoTrading app/nifty data download/Data/Equities_csv/intraday/BHARTIARTL.csv', index_col='Datetime')
    df.index = pd.to_datetime(df.index)
    
    # Add signals to the DataFrame and create an instance of the strategy
    data_with_signals = RTBollingerBands.addSignals(df)
    bt = Backtest(data_with_signals, RTBollingerBands, cash=10000, margin=1/5, commission=.00)
    
    # Run the backtest and print the statistics
    stat = bt.run()
    print(stat)


if __name__ == '__main__':
    main()

    