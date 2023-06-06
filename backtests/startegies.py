from datetime import timedelta
from backtesting import Strategy
from backtesting.lib import crossover
import numpy as np
from pandas import DataFrame,Series
import pandas_ta as ta


#Implements the RaynerTeo BollingerBand Strategy
class RTBollingerBands(Strategy):
    '''make sl and tp work right'''
    slPercent:float = 0.00
    tpPercent:float = 1.00

    def B_SIGNAL(self):
        return self.data.ordersignal

    def addSignals(data, length=200, std=2.5, backcandles=6, percent=0.0):
        """
        Adds signals to the data using various technical indicators such as EMA, RSI, and Bollinger Bands.

        Parameters:
        - data:The DataFrame containing the necessary data columns (e.g., 'Close', 'High', 'Low').
        - length (optional): The length parameter for calculating the EMA and Bollinger Bands. Default is 200.
        - std (optional): The standard deviation parameter for calculating the Bollinger Bands. Default is 2.5.
        - backcandles (optional): The number of previous candles to consider for trend analysis. Default is 6.
        - percent (optional): The percentage parameter for adjusting the order signals. Default is 0.0.

        Returns: data
        -  Modifies the 'data' by adding the following columns:
            - 'EMA': Exponential Moving Average calculated using the 'Close' column.
            - 'RSI': Relative Strength Index calculated using the 'Close' column.
            - 'BBL_20_2.5': Lower Bollinger Band with length 20 and standard deviation 2.5.
            - 'BBU_20_2.5': Upper Bollinger Band with length 20 and standard deviation 2.5.
            - 'EMASignal': Signal indicating the trend based on EMA analysis (0, 1, 2, or 3).
            - 'ordersignal': Signal indicating the buy/sell order based on the specified conditions.

        Note: The function relies on the 'pandas_ta' module for calculating technical indicators.
        """

        # Calculate EMA, RSI, and Bollinger Bands
        data['EMA'] = ta.sma(data.Close, length=length)
        data['RSI'] = ta.rsi(data.Close, length=2)
        my_bbands = ta.bbands(data.Close, length=20, std=2.5)
        data = data.join(my_bbands)
        data.dropna(inplace=True)

        # Calculate EMA signal
        emasignal = [0] * len(data)
        for row in range(backcandles, len(data)):
            upt = 1
            dnt = 1
            for i in range(row - backcandles, row + 1):
                if data.High[i] >= data.EMA[i]:
                    dnt = 0
                if data.Low[i] <= data.EMA[i]:
                    upt = 0
            if upt == 1 and dnt == 1:
                emasignal[row] = 3
            elif upt == 1:
                emasignal[row] = 2
            elif dnt == 1:
                emasignal[row] = 1
        data['EMASignal'] = emasignal

        # Calculate order signal
        ordersignal = [0] * len(data)
        for i in range(1, len(data)):
            if data.EMASignal[i] == 2 and data.Close[i] <= data['BBL_20_2.5'][i]:
                ordersignal[i] = data.Close[i] - data.Close[i] * percent
            elif data.EMASignal[i] == 1 and data.Close[i] >= data['BBU_20_2.5'][i]:
                ordersignal[i] = data.Close[i] + data.Close[i] * percent
        data['ordersignal'] = ordersignal
        return data


    initsize = 0.99
    ordertime=[]
    def init(self):
        super().init()
        self.signal = self.I(self.B_SIGNAL)

    def next(self):
        super().next()
        
        for j in range(0, len(self.orders)):
            #print('!!!!!!!!!!!!!!!!!!!', self.data.index[-1])
            if self.data.index[-1]-self.ordertime[0]>timedelta(5):#days max to fulfill the order!!!
                #print('----------------------')
                #print(self.orders)
                #print(self.ordertime)
                self.orders[0].cancel()
                self.ordertime.pop(0)   
            
        if len(self.trades)>0:
            #print(self.data.index[-1], self.trades)
            if self.data.index[-1]-self.trades[-1].entry_time>=timedelta(10):
                self.trades[-1].close()
                #print(self.data.index[-1], self.trades[-1].entry_time)
            
            if self.trades[-1].is_long and self.data.RSI[-1]>=50:
                self.trades[-1].close()
            elif self.trades[-1].is_short and self.data.RSI[-1]<=50:
                self.trades[-1].close()
        
        if self.signal!=0 and len(self.trades)==0 and self.data.EMASignal==2:
            #Cancel previous orders
            for j in range(0, len(self.orders)):
                self.orders[0].cancel()
                self.ordertime.pop(0)
            #Add new replacement order
            self.buy(sl=self.signal*self.slPercent, limit=self.signal, size=self.initsize,tp=self.signal*self.tpPercent)
            self.ordertime.append(self.data.index[-1])
        
        elif self.signal!=0 and len(self.trades)==0 and self.data.EMASignal==1:
            #Cancel previous orders
            for j in range(0, len(self.orders)):
                self.orders[0].cancel()
                self.ordertime.pop(0)
            #Add new replacement order
            self.sell(sl=self.signal*self.tpPercent, limit=self.signal, size=self.initsize,tp=self.signal*self.slPercent)
            self.ordertime.append(self.data.index[-1])

#implements Bhramastra startedgy by Pushkar Raj Thakur
class Bhramastra(Strategy):

    initsize = 0.99

    #def B_SIGNAL(self):
        #return self.data.ordersignal

    def addSignals(data: DataFrame,Version1:bool = False) -> DataFrame:
        """
        Adds additional technical analysis signals to the given DataFrame.

        Args:
            data (DataFrame): The input DataFrame containing OHLCV (Open, High, Low, Close, Volume) data.

        Returns:
            DataFrame: The modified DataFrame with added technical analysis signals.

        This function calculates and adds the following signals to the input DataFrame:
        1. Supertrend: Calculates the Supertrend indicator using the high, low, and close prices with a length of 20
           and a multiplier of 2. Adds the 'Trend' column representing the Supertrend trend direction
           and the 'STValue' column representing the Supertrend value.
        2. VWAP (Volume Weighted Average Price): Calculates the VWAP using the high, low, close prices, and volume.
           Adds the 'VWAP' column representing the VWAP values.
        3. MACD (Moving Average Convergence Divergence): Calculates the MACD indicator using the closing prices
           with a fast length of 12, slow length of 26, and signal length of 9.
           Adds the 'MACDF' column representing the MACD line value,
           the 'MACDh' column representing the MACD histogram,
           and the 'MACDS' column representing the MACD signal line.

        Note:
        - This function modifies the input DataFrame in-place by adding the calculated signals.
        - Rows with missing values (NaN) are dropped from the DataFrame before returning the result.

        Example usage:
        >>> df = addSignals(df)
        """

        # Calculate Supertrend
        supertrend = ta.supertrend(data.High, data.Low, data.Close, length=20, multiplier=2)
        data['Trend'] = supertrend['SUPERTd_20_2.0']
        data['STValue'] = supertrend['SUPERT_20_2.0']

        # Calculate VWAP
        vwap = ta.vwap(data['High'], data['Low'], data.Close, data.Volume)
        data['VWAP'] = vwap

        # Calculate MACD
        macd = ta.macd(data.Close, 12, 26, 9)
        data['MACDF'] = macd['MACD_12_26_9']
        #data['MACDh'] = macd['MACDh_12_26_9'] dont need histogram
        data['MACDS'] = macd['MACDs_12_26_9']

        # Drop rows with missing values
        data.dropna(inplace=True)

        # Calculate order signal
        data['ordersignal'] = 0
        sIndex = data.columns.get_loc('ordersignal') 
        if Version1:
            for i in range(len(data)):
            #conditions of stratedgy
                if crossover(data['MACDF'][:i],data['MACDS'][:i]) and data['Close'][i]<data['VWAP'][i] and data['Trend'][i] == 1:
                    data.iloc[i,sIndex] = 1
                elif crossover(data['MACDS'][:i],data['MACDF'][:i]) and data['Close'][i]>data['VWAP'][i] and data['Trend'][i] == -1:
                    data.iloc[i,sIndex] = 2
        else:
            for i in range(1, len(data)):
                if data['Trend'].iloc[i] == 1:
                    if data['MACDF'].iloc[i] > data['MACDS'].iloc[i] and data['Close'].iloc[i] > data['VWAP'].iloc[i]:
                        data.iloc[i,sIndex] = 1  # Buy signal
                elif data['Trend'].iloc[i] == -1:
                    if data['MACDF'].iloc[i] < data['MACDS'].iloc[i] and data['Close'].iloc[i] < data['VWAP'].iloc[i]:
                        data.iloc[i,sIndex] = 2

        return data


    def init(self):
        super().init()
        #self.signal = self.I(self.B_SIGNAL)

    def next(self):
        super().next()

        # Check if there are no open trades
        if len(self.trades) == 0:
            # Buy if a buy (1) signal is generated
            if self.data.ordersignal[-1] == 1:
                self.buy(size=self.initsize)
            # Sell if a sell (2) signal is generated
            elif self.data.ordersignal[-1] == 2:
                self.sell(size=self.initsize)

        # Check if there is an open position
        elif self.position:
            # Check if the current position is long
            if self.position.is_long:
                # Close the position if the trend changes to down
                if self.data.Trend[-1] == -1:
                    self.position.close()
                # Close the position if MACDS crosses below MACDF
                elif crossover(self.data.MACDS, self.data.MACDF):
                    self.position.close(0.50)

            # Check if the current position is short
            else:
                # Close the position if the trend changes to up
                if self.data.Trend[-1] == 1:
                    self.position.close()
                # Close the position if MACDF crosses above MACDS
                elif crossover(self.data.MACDF, self.data.MACDS):
                    self.position.close(0.50)


class BrahmastraR(Strategy):
    initsize = 0.99

    def init(self):
        super().init()
        High = Series(self.data.High,index=self.data.index)
        Low = Series(self.data.Low,index=self.data.index)
        Close = Series(self.data.Close,index=self.data.index)
        Volume = Series(self.data.Volume,index=self.data.index)
        supertrend = ta.supertrend(High, Low, Close, length=20, multiplier=2)
        self.Trend = self.I(lambda :supertrend['SUPERTd_20_2.0'].values,name='Trend')
        self.STLValue = self.I(lambda :supertrend['SUPERT_20_2.0'].values,name='SuperTrendValue')
        self.vwap = self.I(ta.vwap,High, Low, Close, Volume)
        macd = ta.macd(self.data.Close, 12, 26, 9)
        self.macdF = self.I(lambda :macd['MACD_12_26_9'].values,name='macdF')
        #macd['MACDh_12_26_9'] dont need histogram
        self.macdS = self.I(lambda :macd['MACDs_12_26_9'].values,name='macdS')

    def next(self):
        super().next()

                # Check if there are no open trades
        if len(self.trades) == 0:
            # Buy if ...
            if self.Trend[-1] == 1:
                if crossover(self.macdF,self.macdS):
                    self.buy(size=self.initsize)
            #Sell if ..
            else :
                if crossover(self.macdS,self.macdF):
                    self.sell(size=self.initsize)

        # Check if there is an open position
        elif self.position:
            # Check if the current position is long
            if self.position.is_long:
                # Close the position if the trend changes to down
                if self.data.Trend[-1] == -1:
                    self.position.close()
                # Close the position if MACDS crosses below MACDF
                elif crossover(self.macdS,self.macdF):
                    self.position.close(0.50)

            # Check if the current position is short
            else:
                # Close the position if the trend changes to up
                if self.data.Trend == 1:
                    self.position.close()
                # Close the position if MACDF crosses above MACDS
                elif crossover(self.macdF,self.macdS):
                    self.position.close(0.50)

class BhramastraRS(Strategy):

    plotIndicators:bool = None
    V1:bool = None
    initsize = 0.99

    #def B_SIGNAL(self):
        #return self.data.ordersignal

    def addSignals(self,data: DataFrame,plotIndicators:bool,Version1:bool = False):
        """
        Adds additional technical analysis signals to the given DataFrame.

        Args:
            data (DataFrame): The input DataFrame containing OHLCV (Open, High, Low, Close, Volume) data.

        Returns:
            DataFrame: The modified DataFrame with added technical analysis signals.

        This function calculates and adds the following signals to the input DataFrame:
        1. Supertrend: Calculates the Supertrend indicator using the high, low, and close prices with a length of 20
           and a multiplier of 2. Adds the 'Trend' column representing the Supertrend trend direction
           and the 'STValue' column representing the Supertrend value.
        2. VWAP (Volume Weighted Average Price): Calculates the VWAP using the high, low, close prices, and volume.
           Adds the 'VWAP' column representing the VWAP values.
        3. MACD (Moving Average Convergence Divergence): Calculates the MACD indicator using the closing prices
           with a fast length of 12, slow length of 26, and signal length of 9.
           Adds the 'MACDF' column representing the MACD line value,
           the 'MACDh' column representing the MACD histogram,
           and the 'MACDS' column representing the MACD signal line.

        Note:
        - This function modifies the input DataFrame in-place by adding the calculated signals.
        - Rows with missing values (NaN) are dropped from the DataFrame before returning the result.

        Example usage:
        >>> df = addSignals(df)
        """

        # Calculate Supertrend
        supertrend = ta.supertrend(data.High, data.Low, data.Close, length=20, multiplier=2)
        self.Trend = self.I(lambda :supertrend['SUPERTd_20_2.0'].values,name='Trend',plot=plotIndicators)
        self.STValue = self.I(lambda :supertrend['SUPERT_20_2.0'].values,name='STValue',plot=plotIndicators)

        # Calculate VWAP
        vwap = ta.vwap(data['High'], data['Low'], data.Close, data.Volume).values
        self.vwap = self.I(lambda :vwap, name='VWAP',plot=plotIndicators)

        # Calculate MACD
        macd = ta.macd(data.Close, 12, 26, 9)
        self.MACDF = self.I(lambda :macd['MACD_12_26_9'].values,name='MACDF',plot=plotIndicators)
        #data['MACDh'] = macd['MACDh_12_26_9'] dont need histogram
        self.MACDS = self.I(lambda :macd['MACDs_12_26_9'].values,name='MACDS',plot=plotIndicators)

        #self.adx = self.I(lambda :ta.adx(data['High'],data['Low'],data['Close'],length=14)['ADX_14'], name='adx',plot=plotIndicators)

        # Calculate order signal
        ordersignal = np.zeros(len(data))
        if Version1:
            for i in range(len(data)):
            #conditions of stratedgy
                if crossover(self.MACDF[:i],self.MACDS[:i]) and data['Close'][i]<self.vwap[i] and self.Trend[i] == 1:
                    ordersignal[i] = 1
                elif crossover(self.MACDS[:i],self.MACDF[:i]) and data['Close'][i]>self.vwap[i] and self.Trend[i] == -1:
                    ordersignal[i] = 2
        else:
            for i in range(1, len(data)):
                if self.Trend[i] == 1:
                    if self.MACDF[i] > self.MACDS[i] and data['Close'].iloc[i] > self.vwap[i]:
                        ordersignal[i] = 1  # Buy signal
                elif self.Trend[i] == -1:
                    if self.MACDF[i] < self.MACDS[i] and data['Close'].iloc[i] < self.vwap[i]:
                        ordersignal[i] = 2

        self.ordersignal= self.I(lambda :ordersignal,name='ordersignal')


    def init(self):
        super().init()
        data_dict = {
            'High': self.data.High,
            'Low': self.data.Low,
            'Close': self.data.Close,
            'Volume': self.data.Volume
        }
        df = DataFrame(data=data_dict,index=self.data.index)
        self.addSignals(df,plotIndicators=self.plotIndicators,Version1=self.V1)
        #self.signal = self.I(self.B_SIGNAL)

    def next(self):
        super().next()

        # Check if there are no open trades
        if len(self.trades) == 0:
           # if self.adx[-1]>25:
            # Buy if a buy (1) signal is generated
            if self.ordersignal[-1] == 1:
                self.buy(size=self.initsize)
            # Sell if a sell (2) signal is generated
            elif self.ordersignal[-1] == 2:
                self.sell(size=self.initsize)

        # Check if there is an open position
        elif self.position:
            # Check if the current position is long
            if self.position.is_long:
                # Close the position if the trend changes to down
                if self.Trend[-1] == -1:
                    self.position.close()
                # Close the position if MACDS crosses below MACDF
                elif crossover(self.MACDS, self.MACDF):
                    self.position.close(0.50)

            # Check if the current position is short
            else:
                # Close the position if the trend changes to up
                if self.Trend[-1] == 1:
                    self.position.close()
                # Close the position if MACDF crosses above MACDS
                elif crossover(self.MACDF, self.MACDS):
                    self.position.close(0.50)