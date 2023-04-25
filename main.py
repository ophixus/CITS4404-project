import ccxt
import ta
import pandas as pd
from trading_bot import TradingBot
from ta import momentum, volatility, volume, trend
# from optimisation_[STRATEGY NAME] import optimise_triggers

PARAMETERS = {'buy_macd_diff': 0.1, 'buy_rsi': 30, 'sell_macd_diff': -0.1, 'sell_rsi': 70}
WINDOW_SIZE = 60

# Fetch historical data from Kraken exchange
# Returns OHLCV data as a list of lists
def fetch_data(timeframe):
    exchange = ccxt.kraken()
    ohlcv = exchange.fetch_ohlcv('BTC/AUD', timeframe=timeframe)
    return ohlcv

# Calculates indicators using historical data
# Returns results as a dataframe with the indicators
def calculate_indicators(self, data):
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['macd_diff'] = trend.macd_diff(self.df['close'], window_slow=WINDOW_SIZE*2, window_fast=WINDOW_SIZE)
    df['rsi'] = momentum.rsi(self.df['close'], window=WINDOW_SIZE)
    df['hourly_change'] = momentum.roc(self.df['close'], window=WINDOW_SIZE)
    df['minute_change'] = momentum.roc(self.df['close'], window=1)
    df['ma_hourly'] = trend.sma_indicator(self.df['close'], window=WINDOW_SIZE)
    df['ma_diff_1m'] = momentum.roc(self.df['ma_hourly'], window=1)
    df['ma_diff_1h'] = momentum.roc(self.df['ma_hourly'], window=WINDOW_SIZE)
    df['bollinger_upper'] = volatility.bollinger_hband(self.df['close'], window=WINDOW_SIZE, window_dev=2)
    df['bollinger_lower'] = volatility.bollinger_lband(self.df['close'], window=WINDOW_SIZE, window_dev=2)
    df['bollinger_diff'] = self.df['bollinger_upper'] - self.df['bollinger_lower']
    df['eom'] = volume.ease_of_movement(self.df['high'], self.df['low'], self.df['volume'], window=WINDOW_SIZE)
    return df

# Main function
def main():
    data = fetch_data('1m')
    df = calculate_indicators(data)
    # expressions = optimise_triggers(df, PARAMETERS)
    bot = TradingBot(df)
    # bot.set_trigger_expressions(expressions)
    bot.run()

# Run main function
if __name__ == "__main__":
    main()

