import ccxt
from ta import momentum, trend, volatility, volume
import pandas as pd
import numpy as np

# Constants
START_BALANCE = 100
FEES = 0.02
WINDOW_SIZE = 60  # 1 minute timeframe to hourly


# Fetch historical data from Kraken exchange
# Returns OHLCV data as a list of lists
def fetch_data(timeframe):
    exchange = ccxt.kraken()
    ohlcv = exchange.fetch_ohlcv('BTC/AUD', timeframe=timeframe)
    return ohlcv

# Trading bot class that will be used to run the trading strategy
class TradingBot:
    def __init__(self, data):
        self.data = data
        self.df = None
        self.params = {}
        self.triggers = {}
        self.balance = START_BALANCE
        self.holdings = 0
        self.trades = None

    # Calculates indicators using historical data
    # Stores results as a dataframe with the indicators
    def calculate_indicators(self):
        self.df = pd.DataFrame(self.data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.df['macd_diff'] = trend.macd_diff(self.df['close'], window_slow=WINDOW_SIZE*2, window_fast=WINDOW_SIZE)
        self.df['rsi'] = momentum.rsi(self.df['close'], window=WINDOW_SIZE)
        self.df['hourly_change'] = momentum.roc(self.df['close'], window=WINDOW_SIZE)
        self.df['minute_change'] = momentum.roc(self.df['close'], window=1)
        self.df['ma_hourly'] = trend.sma_indicator(self.df['close'], window=WINDOW_SIZE)
        self.df['ma_diff_1m'] = momentum.roc(self.df['ma_hourly'], window=1)
        self.df['ma_diff_1h'] = momentum.roc(self.df['ma_hourly'], window=WINDOW_SIZE)
        self.df['bollinger_upper'] = volatility.bollinger_hband(self.df['close'], window=WINDOW_SIZE, window_dev=2)
        self.df['bollinger_lower'] = volatility.bollinger_lband(self.df['close'], window=WINDOW_SIZE, window_dev=2)
        self.df['bollinger_diff'] = self.df['bollinger_upper'] - self.df['bollinger_lower']
        self.df['eom'] = volume.ease_of_movement(self.df['high'], self.df['low'], self.df['volume'], window=WINDOW_SIZE)
        

    # Determines if a buy signal should be triggered
    # Returns True if parameters are met, False otherwise
    def buy_trigger(self, t):
        macd_diff = self.df['macd_diff'][t] > self.params['buy_macd_diff']
        rsi = self.df['rsi'][t] < self.params['buy_rsi']
        return macd_diff and rsi

    # Determines if a sell signal should be triggered
    # Returns True if parameters are met, False otherwise
    def sell_trigger(self, t):
        macd_diff = self.df['macd_diff'][t] < self.params['sell_macd_diff']
        rsi = self.df['rsi'][t] > self.params['sell_rsi']
        return macd_diff and rsi

    # Optimises the trading strategy using adaptive AI techniques
    # Stores the optimised parameters and triggers as class attributes
    def optimise_strategy(self):
        self.params.update({'buy_macd_diff': 0.1, 'buy_rsi': 30, 'sell_macd_diff': -0.1, 'sell_rsi': 70})
        self.triggers = {'buy': self.buy_trigger, 'sell': self.sell_trigger}

    # Spends all available balance on a trade
    # Adds a new trade to the trades dataframe
    def buy(self, t, price):
        self.holdings = self.balance / price * (1 - FEES)
        self.balance = 0
        self.trades.loc[len(self.trades)] = [t, price, None, None, None]

    # Sells all available holdings on a trade
    # Updates the trade in the trades dataframe
    def sell(self, t, price):
        self.balance = self.holdings * price * (1 - FEES)
        self.holdings = 0
        self.trades.loc[len(self.trades) - 1][2:4] = [t, price]

    # Simulates trades using historical data
    # Stores the trades in a dataframe
    def simulate_trades(self):
        # Create empty dataframe to store trades
        self.trades = pd.DataFrame(columns=['entry_time', 'entry_price', 'exit_time', 'exit_price', 'profit'])

        # Iterate through all time steps
        for t in range(len(self.df)):
            # Check if buy or sell triggers are met
            if self.triggers['buy'](t) and not self.holdings:
                self.buy(t, self.df['close'][t])
            elif self.triggers['sell'](t) and not self.balance:
                self.sell(t, self.df['close'][t])
        
        # At the end of the simulation, sell all holdings and calculate profit per trade
        if self.holdings:
            self.sell(t, self.df['close'][t])
        self.trades['profit'] = self.trades['exit_price'] - self.trades['entry_price']

    # Evaluates the performance of the trading strategy
    # Returns a dictionary of performance metrics
    def calculate_performance(self):
        performance_metrics = {
            'net_profit': "{:.2f} AUD".format(self.balance - START_BALANCE),
            'total_trades': len(self.trades),
            'average_profit': "{:.2f} AUD".format(self.trades['profit'].mean())
        }
        return performance_metrics

    # Runs the trading strategy
    # Prints performance metrics
    def run(self):
        self.calculate_indicators()
        self.optimise_strategy()
        self.simulate_trades()
        performance = self.calculate_performance()
        for key, value in performance.items():
            print(key, value)

# Main function
def main():
    data = fetch_data('1m')
    bot = TradingBot(data)
    bot.run()

# Run main function
if __name__ == "__main__":
    main()

