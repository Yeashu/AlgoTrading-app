from backtesting import Backtest,Strategy
from startegies import RTBollingerBands,Bhramastra
import pandas as pd
from A_utils import save_dict_to_csv,save_to_csv
from stocksList import nifty50_stocks
import os

def mBacktest(strategy:Strategy,stocks:list,dataDirectory,cash,intraday:bool,
              leverage:float,save:bool,commission:float ,
              saveDirectory:str = 'BacktestResult',verbose:bool = True ):
    '''
    This function runs backtest for all the stocks in the list
    Args:
        strategy: Strategy class
        stocks: list of stocks
        dataDirectory: directory where the data is stored
        cash: cash to start with
        intraday: bool, if True then index column is Datetime
        leverage: float, leverage to use
        commission: float, commission to use
        verbose: bool, if True then prints the results
        save: bool, if True then saves the results
        saveDirectory: directory to save the results
    Returns:
        btResults: dictionary of results
        btReturns: dictionary of returns
    TODO make it multithreaded
    '''
    indexCol = 'Date'
    btResults = {}
    btReturns = {}
    for symbol in stocks:
        if verbose : print(f'Backtest started for {symbol}')
        if intraday:
            indexCol = 'Datetime'
        
        data = pd.read_csv(dataDirectory+'/'+symbol+'.csv',index_col=indexCol)
        data.index = pd.DatetimeIndex(data.index)
        data = strategy.addSignals(data)
        bt = Backtest(data=data,strategy=strategy,cash=cash,margin=leverage,commission=commission)
        stat = bt.run()
        ret = stat['Return [%]']
        if verbose : print(f'Backtest completed for {strategy} for  {symbol}, \n Return {ret} ')
        btResults[symbol] = stat
        btReturns[symbol] = ret
    
    if save:
        #check if the directory exists in filesystem if not create one
        if not os.path.exists(saveDirectory):
            print('Directory does not exist')
            os.makedirs(saveDirectory)
            print(f'Directory {saveDirectory} created')
            
        print(f'Saving results of Backtest of {strategy} at {saveDirectory} ')
        Save(btResults=btResults,btReturns=btReturns,saveDirectory=saveDirectory)
        return
    
    return btResults,btReturns
    

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


#backtesting startegies
def main(startigies:list,stocks:list,dataDirectory:dict,saveDirectories:dict,
         cash,save:bool=False,leverage:float = 1,intraday:bool = False,
         CalcUnleveragedAlso:bool = False,commission:float=0,):
    '''
    This function runs backtest for all the startegies
    Args:
        startigies: list of startegies
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
    

    strat = {'Bhramastra':Bhramastra,'RTBollingerBands': RTBollingerBands}
    for st in startigies:
        strategy = strat[st]
        if intraday:
            saveDirectories[st] = saveDirectories[st] + '/intraday'
        else:
            saveDirectories[st] = saveDirectories[st] + '/daily'
        if CalcUnleveragedAlso:
            mBacktest(strategy,stocks,dataDirectory[st],cash,intraday=intraday,
                      leverage=1,save=save,saveDirectory=saveDirectories[st],
                      commission=commission)
        if leverage != 1:
            saveDirectories[st] = saveDirectories[st] + '/leveraged'
        else:
            return    
        mBacktest(strategy,stocks,dataDirectory[st],cash,intraday=intraday,
                  leverage=leverage,save=save,saveDirectory=saveDirectories[st]
                  ,commission=commission)
        
    


if __name__ == '__main__':
    main(startigies=['RTBollingerBands'],stocks=nifty50_stocks,
         dataDirectory={'RTBollingerBands':'/home/yeashu/project/AlgoTrading app/nifty data download/Data/Equities_csv/daily/nifty50'},
         saveDirectories={'RTBollingerBands':'/home/yeashu/project/AlgoTrading app/backtests/Results/RTBollingerBands'}
         ,cash=100000,leverage=1,intraday=False,CalcUnleveragedAlso=True,save=True)

    