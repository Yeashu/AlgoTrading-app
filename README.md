# AlgoTrading-app 

AlgoTrading-app is a Python-based application designed to streamline the entire trading process, from stock market data collection, strategy development, backtesting, strategy optimization to live execution.

## Key Features

- 🧠 **Intelligent Strategy Implementation**: Leverage the power of the `backtesting` library to effortlessly implement, test and optimize your trading strategies, ensuring optimal performance.

- 📈 **Advanced Technical Analysis**: Gain deeper insights into market trends with `pandas_ta`, a powerful library that calculates and analyzes a wide range of technical indicators.

- 🌐 **Seamless Data Integration**: Fetch historical stock data from renowned sources like Yahoo Finance using `yfinance` and 5paisa using our `FivePaisaWrapper`, ensuring you have access to reliable and up-to-date market data.
  
- ⚡ **Parallel Backtesting**: Accelerate your backtesting process with the power of multiprocessing, allowing you to test multiple strategies and stocks simultaneously.

- 🔍 **Parameter Optimization**: Identify the optimal strategy parameters by running comprehensive optimization routines, ensuring your strategies are finely tuned for maximum profitability.
  
- 🚀 **Concurrent Data Download**: Leverage multithreading capabilities to download historical and intraday stock data concurrently, streamlining your data acquisition process. This is done through our `FivePaisaWrapper` that uses multithreading to speed up the download by **20x** compared to using `py5paisa`.

# TO-DO
  
- 🔄 **Live Execution**: Seamlessly transition from backtesting to live trading, executing your proven strategies in real-time market conditions.
  
- 💻 **Live Trading Integration**: Execute trades directly through the 5paisa trading platform using `py5paisa`.

- 📆 **Robust Handling of Market Events**: Accurately account for stock splits, dividends, and holidays, ensuring your strategies adapt to real-world market dynamics.

## How It Works

- ### Backtesting with Multiprocessing

   Our backtesting script utilizes the power of multiprocessing to run backtests for multiple stocks in parallel. This not only speeds up the backtesting process significantly but also allows for efficient utilization of system resources, making it ideal for testing multiple strategies across a wide range of stocks. We leverage the `backtesting.py` library by Kernc for conducting backtests and strategy optimization, ensuring robust and accurate results.

- ### Data Integration with FivePaisaWrapper

  In addition to fetching historical stock data from Yahoo Finance using the `yfinance` library, AlgoTrading-app offers the option to use our custom `FivePaisaWrapper`. This wrapper utilizes multithreading to download historical and intraday stock data concurrently, making it faster than traditional methods. Compared to 5paisa's own API SDK `py5paisa`, our wrapper is up to **20** times faster during bulk download of stock data.

- ### Live Execution (Work in Progress)

  While live execution of trading strategies is not currently implemented in AlgoTrading-app, it's on my to-do list.


# Usage Instructions

## Setup

1. Clone the main repository (AlgoTrading-app) and initialize the submodules:

    ```sh
    git clone --recurse-submodules https://github.com/Yeashu/AlgoTrading-app.git
    cd AlgoTrading-app
    ```

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```
    or
   Intial the virtual environment using conda:
   ```sh
   conda env create -f environment.yml
   conda activate AlgoTrading
   ```

## Running a Backtest

To run a backtest using the `AlgoTrading-app`, follow these steps:

1. **Configure Your Strategy**:
   Open the `backtests/strategies.py` file and define your trading strategy. For example, you might set up a simple moving average crossover strategy.

   ```python
   from backtesting import Strategy
   from backtesting.lib import crossover
   from backtesting.test import SMA

   class SmaCross(Strategy):
       def init(self):
           self.sma1 = self.I(SMA, self.data.Close, 10)
           self.sma2 = self.I(SMA, self.data.Close, 20)

       def next(self):
           if crossover(self.sma1, self.sma2):
               self.buy()
           elif crossover(self.sma2, self.sma1):
               self.sell()
   ```
2. **Prepare Your Data**:
   Use the `yfinance` library to fetch historical stock data. You can also use `FivePaisaWrapper` for data.

   ```python
    import yfinance as yf
 
    # Define the list of stocks to backtest
    stocks = ['AAPL', 'MSFT', 'GOOGL']

    # Fetch data for each stock
    data_directory = '/path/to/data'
    for stock in stocks:
        data = yf.download(stock, start='2020-01-01', end='2021-01-01')
        data.to_csv(f'{data_directory}/{stock}.csv')
   ```
   Replace /path/to/data with the directory path where you want to save your stock data files.

3. **Run the Backtest:**
   Use the `backtests/backtester.py` script to execute your backtest for the fetched data. The script is designed to run backtests for multiple stocks using multiprocessing.

   ```python
   from backtests.strategies import SmaCross
   from backtests.backtester import mBacktest

   mBacktest(
       strategy=SmaCross,
       stocks=stocks,
       dataDirectory=data_directory,
       cash=10000,
       intraday=False,
       leverage=1,
       save=True,
       commission=0.002,
       savePlots=True,
       openPlots=False,
       oldStyle=False,
       saveDirectory='BacktestResult',
       verbose=True
   )
   ```
   The results of backtests will be stored in the directory specified by the saveDirectory parameter in the mBacktest function.
   Feel free to read the function (mBacktest) documentation for more info (It is well written ;) .
   

\* 5 paisa api key is required for `FivePaisaWrapper`

# Acknowledgments and Credits
## Libraries and APIs Used

  - **backtesting.py**: A Python library by Kernc for backtesting trading strategies. https://github.com/kernc/backtesting.py

  - **pandas_ta**: A powerful Python library for technical analysis in pandas. https://github.com/twopirllc/pandas-ta
    
  - **py5paisa**: Python SDK for 5paisa APIs. https://github.com/OpenApi-5p/py5paisa. 

  - **yfinance**: Python library to fetch historical market data from Yahoo Finance. https://github.com/ranaroussi/yfinance

## Contributors

  **Yeashu**: developer and maintainer of AlgoTrading-app.

## Special Thanks

  **Open-source Community**: Gratitude to all developers and contributors who create and maintain open-source projects, providing valuable resources and tools for the developer community worldwide.

# License

This project is licensed under the MIT License.

