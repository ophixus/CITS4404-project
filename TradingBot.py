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
        self.data = self.calculate_indicators()
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
    def calculate_indicators(self):
        short_sma = SMAIndicator(close=self.data["close"], window=self.short_window, fillna=True)
        long_sma = SMAIndicator(close=self.data["close"], window=self.long_window, fillna=True)
        rsi = RSIIndicator(close=self.data["close"], window=self.rsi_window, fillna=True)
        self.data["short_sma"] = short_sma.sma_indicator()
        self.data["long_sma"] = long_sma.sma_indicator()
        self.data["rsi"] = rsi.rsi()
        return self.data
    
    def buy_condition(self, t,p):
        short_sma = self.data['short_sma'].iloc[t]
        long_sma = self.data['long_sma'].iloc[t] 
        return short_sma > (long_sma*p )
    def sell_condition(self, t, p):
        short_sma = self.data['short_sma'].iloc[t]
        long_sma = self.data['long_sma'].iloc[t]
        return short_sma < (long_sma * p)
    # Define buy and sell triggers for the bot according to the task requirements
    def buy_trigger(self, t, p):
        buy_t = self.buy_condition(t, p)
        buy_t_1 = self.buy_condition(t - 1, p)
        sell_t = self.sell_condition(t, p)
        sell_t_1 = self.sell_condition(t - 1, p)
        return buy_t and not buy_t_1 and not (sell_t and not sell_t_1)
    def sell_trigger(self, t, p):
        sell_t = self.sell_condition(t, p)
        sell_t_1 = self.sell_condition(t - 1, p)
        buy_t = self.buy_condition(t, p)
        buy_t_1 = self.buy_condition(t - 1, p)
        return sell_t and not sell_t_1 and not (buy_t and not buy_t_1)
    # executes the trades based on the buy and sell triggers
    def execute_trades(self, p):
        # Start with 100 AUD
        cash = 100.0
        btc = 0.0
        # Assume that the trading fees are 2% per transaction
        trading_fee = 0.02

        # Loop over the time series data
        for t in range(len(self.data)):
            # If we have cash and a buy trigger occurs
            if cash > 0 and self.buy_trigger(t, p):
                # Buy BTC with all available cash (minus the trading fee)
                btc = (cash * (1 - trading_fee)) / self.data['close'].iloc[t]
                cash = 0
            # If we have BTC and a sell trigger occurs
            elif btc > 0 and self.sell_trigger(t, p):
                # Sell all BTC for cash (minus the trading fee)
                cash = btc * self.data['close'].iloc[t] * (1 - trading_fee)
                btc = 0

        # If we have BTC at the end of the time period, sell it for cash
        if btc > 0:
            cash = btc * self.data['close'].iloc[-1] * (1 - trading_fee)

        # Return the final amount of cash
        return cash
    def optimize_p(self):
        # Define a grid of possible P values
        p_values = np.linspace(0.8, 1.2, 50)  # Change this range based on your expectations
        grid = ParameterGrid({'P': p_values})

        best_score = float('-inf')  # Initialize the best score as negative infinity
        best_p = None  # Initialize the best P value

        # Iterate over all possible P values in the grid
        for params in grid:
            P = params['P']
            score = self.execute_trades(P)  # You need to define this method to evaluate your strategy
            if score > best_score:
                best_score = score
                best_p = P
        return best_score

def main():
    
    bot = TradingBot('BTC/AUD')
    final_cash = bot.optimize_p()
    print('Final amount of cash:', final_cash)

if __name__ == '__main__':
    main()
