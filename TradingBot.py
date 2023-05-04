import ccxt
import pandas as pd
import ta
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from sklearn.model_selection import ParameterGrid
import numpy as np
class TradingBot:
    # initializes the bot with given parameters
    # define short_window and long_window as 9 and 21 respectively to calculate the SMA
    # define rsi_window as 14 to calculate the RSI (RSI widwows are usually 14 was recommended by J. Welles Wilder, the creator of the RSI)
    # The maximum value for this parameter is determined by the exchange API limits
    def __init__(self, symbol, short_window=9, long_window=21,  rsi_window=14,timeframe='1d', limit=720):
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_window = rsi_window
        self.timeframe = timeframe
        self.limit = limit
        self.data = self.fetch_data()
        self.data = self.prepare_dataframe()
    #fetches historical data for the specified symbol, timeframe and limit from the Kraken exchange
    def fetch_data(self):
        exchange = ccxt.kraken()
        data = exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=self.limit)
        return data
    #prepares the historical OHLCV data into a pandas dataframe 
    def prepare_dataframe(self):
        df = pd.DataFrame(self.data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        # convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%d/%m/%Y')
        df.set_index('timestamp', inplace=True)
        print(df)
        return df
    # calculates the short and long simple moving averages (SMA) for the given data
    # calculates the relative strength index (RSI) for the given data
    
    def buy_condition(self, t,p,short_window,long_window):
        short_sma = SMAIndicator(close=self.data["close"], window=short_window, fillna=True).sma_indicator().iloc[t]
        long_sma = SMAIndicator(close=self.data["close"], window=long_window, fillna=True).sma_indicator().iloc[t]
        return short_sma > (long_sma*p)
    def sell_condition(self, t, p,short_window,long_window):
        short_sma = SMAIndicator(close=self.data["close"], window=short_window, fillna=True).sma_indicator().iloc[t]
        long_sma = SMAIndicator(close=self.data["close"], window=long_window, fillna=True).sma_indicator().iloc[t]
        return short_sma < (long_sma * p)
    # Define buy and sell triggers for the bot according to the task requirements
    def buy_trigger(self, t, p,short_window,long_window):
        buy_t = self.buy_condition(t, p,short_window,long_window)
        buy_t_1 = self.buy_condition(t - 1, p,short_window,long_window)
        sell_t = self.sell_condition(t, p,short_window,long_window)
        sell_t_1 = self.sell_condition(t - 1, p,short_window,long_window)
        return buy_t and not buy_t_1 and not (sell_t and not sell_t_1)
    def sell_trigger(self, t, p,short_window,long_window):
        sell_t = self.sell_condition(t, p,short_window,long_window)
        sell_t_1 = self.sell_condition(t - 1, p,short_window,long_window)
        buy_t = self.buy_condition(t, p,short_window,long_window)
        buy_t_1 = self.buy_condition(t - 1, p,short_window,long_window)
        return sell_t and not sell_t_1 and not (buy_t and not buy_t_1)
    # executes the trades based on the buy and sell triggers
    def execute_trades(self, p,short_window,long_window):
        # Start with 100 AUD
        p = float(p)
        short_window = int(round(short_window))
        long_window = int(round(long_window))
        cash = 100.0
        btc = 0.0
        # Assume that the trading fees are 2% per transaction
        trading_fee = 0.02

        # Loop over the time series data
        for t in range(len(self.data)):
            # If we have cash and a buy trigger occurs
            if cash > 0 and self.buy_trigger(t, p,short_window,long_window):
                # Buy BTC with all available cash (minus the trading fee)
                btc = (cash * (1 - trading_fee)) / self.data['close'].iloc[t]
                cash = 0
            # If we have BTC and a sell trigger occurs
            elif btc > 0 and self.sell_trigger(t, p,short_window,long_window):
                # Sell all BTC for cash (minus the trading fee)
                cash = btc * self.data['close'].iloc[t] * (1 - trading_fee)
                btc = 0

        # If we have BTC at the end of the time period, sell it for cash
        if btc > 0:
            cash = btc * self.data['close'].iloc[-1] * (1 - trading_fee)

        # Return the final amount of cash
        return cash
    
    
    def ADE(self):
        # Initialize parameters
        n = 100    # population size
        D = 3     # number of dimensions
        F = 0.5    # scale factor for mutation
        CR = 0.8   # crossover rate
        MaxFEs = 50 # Maximum number of function evaluations
        P_range = (0.6, 1.5)
        short_window_range = (5, 30)
        long_window_range = (10, 60)
        # Initialize population with random values within P_range
        population = np.empty((n, D))
        population[:, 0] = np.random.uniform(P_range[0], P_range[1], n)
        population[:, 1] = np.random.randint(short_window_range[0], short_window_range[1], n)
        population[:, 2] = np.random.randint(long_window_range[0], long_window_range[1], n)

        for gen in range(MaxFEs // n):
            # DE/rand/1 mutation and crossover
            mutated_population = np.empty_like(population)
            for i in range(n):
                r1, r2, r3 = population[np.random.choice(n, 3, replace=False)]
                vi = r1 + F * (r2 - r3)  # DE/rand/1 mutation
                # Crossover
                ui = np.where(np.random.rand(D) < CR, vi, population[i])
                mutated_population[i] = ui
            # TLLS-based local search
            offspring_population = np.empty_like(population)
            for i in range(n):
                sigma = 10**(-1 - (10 / (D + 3)) * (gen * n + i) / MaxFEs)
                v1, v2 = np.random.normal(mutated_population[i], sigma, (2, D))
                offspring_population[i] = max([v1, v2, mutated_population[i]], key=lambda x: self.execute_trades(*x))
            # Crowding-based selection
            next_population = np.empty_like(population)
            for i in range(n):
                uti = offspring_population[i]
                xtnn = min(population, key=lambda x: np.linalg.norm(x-uti))
                if self.execute_trades(*uti) >= self.execute_trades(*xtnn):
                    next_population[i] = uti
                else:
                    next_population[i] = xtnn
            population = next_population
        print(self.execute_trades(*max(population, key=lambda x: self.execute_trades(*x))), max(population, key=lambda x: self.execute_trades(*x)))
        return(self.execute_trades(*max(population, key=lambda x: self.execute_trades(*x))), max(population, key=lambda x: self.execute_trades(*x)))
        

def main():
    bot = TradingBot('BTC/AUD')
    bot.ADE()
    

if __name__ == '__main__':
    main()
