import ccxt
import ta
import pandas as pd
from trading_bot import TradingBot
# from optimisation_[STRATEGY NAME] import optimise_triggers

# Fetch historical data from Kraken exchange
# Returns OHLCV data as a list of lists
def fetch_data(timeframe):
    exchange = ccxt.kraken()
    ohlcv = exchange.fetch_ohlcv('BTC/AUD', timeframe=timeframe)
    return ohlcv

# Calculates indicators using historical data
# Returns results as a dataframe with the indicators
def calculate_indicators(data):
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['macd_diff'] = ta.trend.macd_diff(df['close'], window_slow=26, window_fast=12)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    return df

# Main function
def main():
    data = fetch_data('1m')
    df = calculate_indicators(data)
    expressions = [] # Will eventually be replaced by optimise_triggers(df)
    bot = TradingBot(df)
    bot.set_trigger_expressions(expressions)
    bot.run(True)

# Run main function
if __name__ == "__main__":
    main()

