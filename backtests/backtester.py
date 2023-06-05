from backtesting import Backtest,Strategy
from A_utils import save_dict_to_csv, save_to_csv
from stocksList import nifty50_stocks
from startegies import RTBollingerBands,Bhramastra,BhramastraRS
import pandas as pd
import os
from multiprocessing import Process, Manager
import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")

#filter and ignore specific warning categories
#warnings.filterwarnings("ignore", category=DeprecationWarning)
#warnings.filterwarnings("ignore", category=RuntimeWarning)


#global 
strat = {'Bhramastra':Bhramastra,'RTBollingerBands': RTBollingerBands,
         'BhramastraRS':BhramastraRS}

def mBacktest(strategy: Strategy, stocks: list, dataDirectory, cash, intraday: bool,
              leverage: float, save: bool, commission: float, savePlots:bool,
              openPlots:bool,oldStyle:bool,saveDirectory: str = 'BacktestResult',
              verbose: bool = True,):
    """
    Run backtests for multiple stocks using multiprocessing.
    
    Args:
        strategy (Strategy): The trading strategy to be used for backtesting.
        stocks (list): List of stock symbols to perform backtests on.
        dataDirectory (str): Directory path where the stock data files are located.
        cash (float): Initial cash amount for backtesting.
        intraday (bool): Flag indicating whether the data is intraday or daily.
        leverage (float): Leverage amount for margin trading.
        save (bool): Flag indicating whether to save the backtest results.
        commission (float): Commission rate for trading.
        saveDirectory (str, optional): Directory path to save the backtest results. Defaults to 'BacktestResult'.
        verbose (bool, optional): Flag indicating whether to print progress and results. Defaults to True.
        
    Returns:
        tuple: A tuple containing the backtest results and returns.
    """
    if save:
        createDirIfNotExists(saveDirectory)
    if savePlots:
        createDirIfNotExists(f'{saveDirectory}/Plots/')
    btResults = {}
    btReturns = {}
    indexCol = 'Datetime' if intraday else 'Date'

    def run_backtest(strategy: Strategy, cash, leverage, commission: float,
                    symbol: str, indexCol: str, resultDict, savePlots:bool,
                    openPlots:bool,verbose: bool = True,saveDirectory:str = ''):
        """
        Run backtest for a single stock.
        
        Args:
            strategy (Strategy): The trading strategy to be used for backtesting.
            cash (float): Initial cash amount for backtesting.
            leverage (float): Leverage amount for margin trading.
            commission (float): Commission rate for trading.
            symbol (str): The stock symbol.
            indexCol (str): The column to be used as the index in the stock data.
            resultDict (Manager.dict): Shared dictionary to store the backtest results.
            verbose (bool, optional): Flag indicating whether to print progress and results. Defaults to True.
        """
        if verbose:
            print(f'Backtest started for {symbol}')

        data = pd.read_csv(dataDirectory + '/' + symbol + '.csv', index_col=indexCol)
        data.index = pd.DatetimeIndex(data.index)
        if oldStyle:
            data = strategy.addSignals(data)
        bt = Backtest(data=data, strategy=strategy, cash=cash, margin=leverage, commission=commission)
        stat = bt.run()
        ret = stat['Return [%]']
        resultDict[symbol] = (stat, ret)

        if verbose:
            print(f'Backtest completed for {strategy} for {symbol}, \n Return {ret}')
        if savePlots:
            print(f'Saving plots for {symbol}')
            bt.plot(filename=f'{saveDirectory}/Plots/{symbol}.html',plot_drawdown=True,plot_return=True,plot_pl=True,open_browser=openPlots)

    if verbose:
        print(f'Running backtests for {len(stocks)} stocks')

    with Manager() as manager:
        resultDict = manager.dict()

        processes = []
        for symbol in stocks:
            process = Process(target=run_backtest, args=(strategy, cash, leverage, commission, symbol, indexCol,
                                                        resultDict,savePlots,openPlots,verbose,saveDirectory))
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
        
        for symbol, (sbtResults, sbtReturns) in resultDict.items():
            btResults[symbol] = sbtResults
            btReturns[symbol] = sbtReturns


    if save:
        print(f'Saving results of Backtest of {strategy} at {saveDirectory}')
        Save(btResults=btResults, btReturns=btReturns, saveDirectory=saveDirectory)
        return

    return btResults, btReturns

def mOptimize(bt:Backtest,maximize='SQN', method='grid', max_tries=None, constraint=None, return_heatmap=False, return_optimization=False, random_state=None, **kwargs):
    '''write function that optmizes the strategy on a parameter using backtesting.py
        TODO make it work as intended'''
    bt.optimize(maximize=maximize,method=method,max_tries=max_tries,
                constraint=constraint,return_heatmap=return_heatmap,
                return_optimization=return_optimization,random_state=random_state)
    pass


def Save(btResults:dict,btReturns:dict,saveDirectory):
    '''
    Saves the results of backtest
    Args:
        btResults: dictionary of results
        btReturns: dictionary of returns
        saveDirectory: directory to save the results
    Returns:
        None
    '''
    save_dict_to_csv(btReturns,saveDirectory,'AA_Returns')
    for symbol,stat in btResults.items():
        save_to_csv(stat,symbol,saveDirectory)

def createDirIfNotExists(directory):
    # Check if the directory exists in the file system, if not create one
    if not os.path.exists(directory):
        print('Directory does not exist')
        os.makedirs(directory)
        print(f'Directory {directory} created')


#backtesting startegies
def main(stratagies:list,stocks:list,dataDirectory:dict,saveDirectories:dict,
         cash,save:bool=False,leverage:float = 1,intraday:bool = False,
         CalcUnleveragedAlso:bool = False,commission:float=0,
         savePlots:bool = False,openPlots:bool = False, oldStyle:bool = True):
    '''
    This function runs backtest for all the startegies
    Args:
        stratagies: list of startegies
        stocks: list of stocks
        dataDirectory: dictionary of data directory
        saveDirectories: dictionary of save directory
        cash: cash to start with
        leverage: float, leverage to use
        intraday: bool, if True then index column is Datetime
        CalcUnleveragedAlso: bool, if True then calculates the unleveraged backtest also
    Returns:
        None
    '''

    for st in stratagies:
        saveDirectories[st] = saveDirectories[st] + '/' + st
        strategy = strat[st]
        if intraday:
            saveDirectories[st] = saveDirectories[st] + '/intraday'
        else:
            saveDirectories[st] = saveDirectories[st] + '/daily'
        if CalcUnleveragedAlso:
            mBacktest(strategy,stocks,dataDirectory[st],cash,intraday=intraday,
                      leverage=1,save=save,saveDirectory=saveDirectories[st],
                      commission=commission,savePlots=savePlots,openPlots=openPlots
                      ,oldStyle=oldStyle)
        if leverage != 1:
            saveDirectories[st] = saveDirectories[st] + '/leveraged'
            mBacktest(strategy,stocks,dataDirectory[st],cash,intraday=intraday,
                  leverage=leverage,save=save,saveDirectory=saveDirectories[st]
                  ,commission=commission,savePlots=savePlots,openPlots=openPlots
                  ,oldStyle=oldStyle)
        
    


if __name__ == '__main__':
    Strategies=['BhramastraRS']
    oldStyle = False
    dataDirectories=['/home/yeashu/project/AlgoTrading app/nifty_data_download/Data/Equities_csv/daily/nifty50']
    ResultDirectories=['/home/yeashu/project/AlgoTrading app/backtests/Results']
    stocks=nifty50_stocks
    leverage=1
    intraday=False
    CalcUnleveragedAlso=True
    save=True
    savePlots=True
    openPlots=False
    cash=100000
    commission=0
    main(stratagies=Strategies,stocks=stocks,dataDirectory={i:j for i,j in zip(Strategies,dataDirectories)},
         saveDirectories={i:ResultDirectories[0] for i in Strategies},#modify it to save to diff directories
         cash=cash,save=save,leverage=leverage,intraday=intraday,
         CalcUnleveragedAlso=CalcUnleveragedAlso,commission=commission,
         savePlots=savePlots,openPlots=openPlots,oldStyle=oldStyle)
