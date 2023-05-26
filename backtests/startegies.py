from datetime import timedelta
from backtesting import Strategy
import pandas_ta as ta


#Implements the RaynerTeo BollingerBand Strategy
class RTBollingerBands(Strategy):

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
            self.buy(sl=self.signal/2, limit=self.signal, size=self.initsize)
            self.ordertime.append(self.data.index[-1])
        
        elif self.signal!=0 and len(self.trades)==0 and self.data.EMASignal==1:
            #Cancel previous orders
            for j in range(0, len(self.orders)):
                self.orders[0].cancel()
                self.ordertime.pop(0)
            #Add new replacement order
            self.sell(sl=self.signal*2, limit=self.signal, size=self.initsize)
            self.ordertime.append(self.data.index[-1])

