# AlgoTrading-app 

AlgoTrading-app is a Python-based application designed to streamline the entire trading process, from data collection for backtesting, strategy development, backtesting, strategy optimization to live execution.

## Key Features

- 🧠 **Intelligent Strategy Implementation**: Leverage the power of the `backtesting` library to effortlessly implement, test and optimize your trading strategies, ensuring optimal performance.

- 📈 **Advanced Technical Analysis**: Gain deeper insights into market trends with `pandas_ta`, a powerful library that calculates and analyzes a wide range of technical indicators.

- 🌐 **Seamless Data Integration**: Fetch historical stock data from renowned sources like Yahoo Finance using `yfinance` and 5paisa using our `FivePaisaWrapper`, ensuring you have access to reliable and up-to-date market data.
  
- ⚡ **Parallel Backtesting**: Accelerate your backtesting process with the power of multiprocessing, allowing you to test multiple strategies and stocks simultaneously.

- 🔍 **Parameter Optimization**: Identify the optimal strategy parameters by running comprehensive optimization routines, ensuring your strategies are finely tuned for maximum profitability.
  
- 🚀 **Concurrent Data Download**: Leverage multithreading capabilities to download historical and intraday stock data concurrently, streamlining your data acquisition process. This is done through our `FivePaisaWrapper` that uses multithreading to speed up the download by **20x** compared to using `py5paisa`.

- ⏱️ **Rate Limiting**: Respect API rate limits with rate-limiting mechanism, ensuring smooth and uninterrupted data retrieval.

# TO-DO
  
- 🔄 **Live Execution**: Seamlessly transition from backtesting to live trading, executing your proven strategies in real-time market conditions.
  
- 💻 **Live Trading Integration**: Execute trades directly through the 5paisa trading platform using `py5paisa`.

- 📆 **Robust Handling of Market Events**: Accurately account for stock splits, dividends, and holidays, ensuring your strategies adapt to real-world market dynamics.

## How It Works

### Backtesting with Multiprocessing

Our backtesting script utilizes the power of multiprocessing to run backtests for multiple stocks in parallel. This not only speeds up the backtesting process significantly but also allows for efficient utilization of system resources, making it ideal for testing multiple strategies across a wide range of stocks. We leverage the `backtesting.py` library by Kernc for conducting backtests and strategy optimization, ensuring robust and accurate results.

### Data Integration with FivePaisaWrapper

In addition to fetching historical stock data from Yahoo Finance using the `yfinance` library, AlgoTrading-app offers the option to use our custom `FivePaisaWrapper`. This wrapper utilizes multithreading to download historical and intraday stock data concurrently, making it faster than traditional methods. Compared to 5paisa's own API SDK `py5paisa`, our wrapper is up to **20** times faster during bulk download of stock data.

### Live Execution (Work in Progress)

While live execution of trading strategies is not currently implemented in AlgoTrading-app, it's on our to-do list.

## Setup

1. Clone the main repository (AlgoTrading-app) and initialize the submodules:

    ```sh
    git clone https://github.com/Yeashu/AlgoTrading-app.git
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



\* 5 paisa api key is required for `FivePaisaWrapper`

