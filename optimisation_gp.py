import numpy as np
import pandas as pd
import operator
import random
from deap import gp, algorithms, base, creator, tools
from trading_bot import TradingBot

# Constants
POPULATION_SIZE = 200
GENERATIONS = 10
MUTATION_RATE = 0.5
CROSSOVER_RATE = 0.9
HALL_OF_FAME_SIZE = 1
TOURNAMENT_SIZE = 3
PENALTY = -99999

default_buy_expr = lambda t, macd_diff, rsi, *args: rsi < 30
default_sell_expr = lambda t, macd_diff, rsi, *args: rsi > 70

# Checks if a trigger expression is valid
# Returns true if valid, false otherwise
def is_valid_trigger(trigger):
    if trigger(100,0,0) == trigger(100,1,1):
        return False
    return True
    
# Protected division function
# Returns 1 if denominator is 0
def protected_div(left, right):
    if right == 0:
        return 1
    return left / right

# If-then-else function
# Returns out1 if condition is true, otherwise returns out2
def if_then_else(condition, out1, out2):
    if condition:
        return out1
    else:
        return out2

# Create primitive set
pset = gp.PrimitiveSetTyped('MAIN', [float for n in range(3)], bool)
pset.renameArguments(ARG0='t')
pset.renameArguments(ARG1='macd_diff')
pset.renameArguments(ARG2='rsi')

# Logical operators
pset.addPrimitive(operator.and_, [bool, bool], bool)
pset.addPrimitive(operator.or_, [bool, bool], bool)
pset.addPrimitive(operator.not_, [bool], bool)
pset.addPrimitive(if_then_else, [bool, float, float], float)

# Comparison operators
pset.addPrimitive(operator.lt, [float, float], bool)
pset.addPrimitive(operator.gt, [float, float], bool)
pset.addPrimitive(operator.eq, [float, float], bool)

# Arithmetic operators
pset.addPrimitive(operator.add, [float, float], float)
pset.addPrimitive(operator.sub, [float, float], float)
pset.addPrimitive(operator.mul, [float, float], float)
pset.addPrimitive(protected_div, [float, float], float)
pset.addPrimitive(operator.neg, [float], float)
pset.addEphemeralConstant('random_number', lambda: float(random.randint(-100, 100)), float)

# Terminal set
pset.addTerminal(True, bool)
pset.addTerminal(False, bool)

# Create fitness function and individual class
creator.create('FitnessMax', base.Fitness, weights=(1.0,))
creator.create('Individual', gp.PrimitiveTree, fitness=creator.FitnessMax)

# Create fitness function
def fitness_function(individual, bot, isBuyTrigger):
    func = gp.compile(individual, pset)
    # Check if expression is valid
    if not is_valid_trigger(func):
        return PENALTY,
    # Simulate triggers
    if isBuyTrigger:
        default = default_buy_expr
        bot.set_trigger_expressions([func, default])
    else:
        default = default_sell_expr
        bot.set_trigger_expressions([default, func])
    p = bot.run()
    # Penalise if no trades are made
    if p['total_trades'] <= 1:
        return PENALTY,
    return p['net_profit'],
        
# Optimises the buy and sell triggers for the trading bot
# Returns the best buy and sell triggers
def optimise_triggers(df):
    bot = TradingBot(df)
    buy_trigger = evolve(bot, True)
    sell_trigger = evolve(bot, False)
    return buy_trigger, sell_trigger

def evolve(bot, isBuyTrigger):
    if isBuyTrigger:
        print('Evolving buy trigger...')
    else:
        print('Evolving sell trigger...')
    # Create toolbox
    toolbox = base.Toolbox()
    toolbox.register('expr', gp.genHalfAndHalf, pset=pset, min_=1, max_=2)
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)
    toolbox.register('compile', gp.compile, pset=pset)
    toolbox.register('evaluate', fitness_function, bot=bot, isBuyTrigger=isBuyTrigger)
    toolbox.register('select', tools.selTournament, tournsize=TOURNAMENT_SIZE)
    toolbox.register('mate', gp.cxOnePoint)
    toolbox.register('expr_mut', gp.genFull, min_=0, max_=2)
    toolbox.register('mutate', gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

    # Create statistics
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register('max', np.max)
    stats.register('min', np.max)
    stats.register('avg', np.mean)

    # Create population and hall of fame
    pop = toolbox.population(n=POPULATION_SIZE)
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    # Run genetic algorithm
    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=CROSSOVER_RATE, mutpb=MUTATION_RATE, ngen=GENERATIONS, stats=stats, halloffame=hof, verbose=True)
    best_expr = toolbox.compile(hof[0])
    print('Best expression: ')
    print(hof[0])
    return best_expr