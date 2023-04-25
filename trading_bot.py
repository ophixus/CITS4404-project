import pandas as pd

# Constants
START_BALANCE = 100
FEES = 0.02

# Trading bot class that will be used to run the trading strategy
class TradingBot:
    def __init__(self, df):
        self.df = df
        self.triggers = {}
        self.balance = START_BALANCE
        self.holdings = 0
        self.trades = None

    # Takes a list of expressions for the buy and sell trigger respectively
    # Generates a function for each trigger expression
    def set_trigger_expressions(self, expressions):
        buy_trigger, sell_trigger = [self.generate_trigger(e) for e in expressions]
        self.triggers = {'buy': buy_trigger, 'sell': sell_trigger}

    # Creates a buy or sell trigger function from an expression
    # Returns a function that takes a timeframe and returns True or False if the trigger is met
    def generate_trigger(self, expression):
        def trigger(self, t):
            return eval(expression, {}, {'t': t})
        return trigger

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
        # Reset balance and holdings
        self.balance = START_BALANCE
        self.holdings = 0

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
            'average_profit': "{:.2f} AUD".format(self.trades['profit'].mean()),
            'win_rate': "{:.2f}%".format(len(self.trades[self.trades['profit'] > 0]) / len(self.trades) * 100 if len(self.trades) else 0),
        }
        return performance_metrics

    # Runs the trading strategy
    # Prints performance metrics
    def run(self):
        self.simulate_trades()
        performance = self.calculate_performance()
        for key, value in performance.items():
            print(key, value)