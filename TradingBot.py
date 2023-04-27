import ccxt
import pandas as pd
import ta
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
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
    # combine the short and long SMA with the RSI to determine the buy and sell conditions
    def buy_condition(self, t):
        short_sma = self.data['short_sma'].iloc[t]
        long_sma = self.data['long_sma'].iloc[t]
        rsi = self.data['rsi'].iloc[t]
        return short_sma > long_sma and rsi < 30
    def sell_condition(self, t):
        short_sma = self.data['short_sma'].iloc[t]
        long_sma = self.data['long_sma'].iloc[t]
        rsi = self.data['rsi'].iloc[t]
        return short_sma < long_sma and rsi > 70
    # Define buy and sell triggers for the bot according to the task requirements
    def buy_trigger(self, t):
        buy_t = self.buy_condition(t)
        buy_t_1 = self.buy_condition(t - 1)
        sell_t = self.sell_condition(t)
        sell_t_1 = self.sell_condition(t - 1)
        return buy_t and not buy_t_1 and not (sell_t and not sell_t_1)
    def sell_trigger(self, t):
        sell_t = self.sell_condition(t)
        sell_t_1 = self.sell_condition(t - 1)
        buy_t = self.buy_condition(t)
        buy_t_1 = self.buy_condition(t - 1)
        return sell_t and not sell_t_1 and not (buy_t and not buy_t_1)
    # executes the trades based on the buy and sell triggers
    def execute_trades(self):
        buy_signals = []
        sell_signals = []

        for t in range(1, len(self.data)):
            if self.buy_trigger(t):
                buy_signals.append(t)
            elif self.sell_trigger(t) and buy_signals:
                sell_signals.append(t)

        return buy_signals, sell_signals

def main():
    bot = TradingBot('BTC/AUD')
    buy_signals, sell_signals = bot.execute_trades()
    print("Buy signals:", buy_signals)
    print("Sell signals:", sell_signals)

if __name__ == '__main__':
    main()
