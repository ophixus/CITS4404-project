import numpy as np
import pandas as pd
import operator
import random
from deap import gp, algorithms, base, creator, tools
from trading_bot import TradingBot

# Constants
POPULATION_SIZE = 500
GENERATIONS = 10
NODE_MUTATION_RATE = 0.9
SUBTREE_MUTATION_RATE = 0.5
CROSSOVER_RATE = 0.2
ELITISM_RATE = 0.01
HALL_OF_FAME_SIZE = 1
TOURNAMENT_SIZE = 2
PENALTY = -99999

# Protected division function
# Returns 1 if denominator is 0
def protected_div(left, right):
    if right == 0:
        return 1
    return left / right

# If-then-else functions for floats and bools
# Returns out1 if condition is true, otherwise returns out2
def if_then_else_float(condition, out1, out2):
    return out1 if condition else out2
def if_then_else_bool(condition, out1, out2):
    return out1 if condition else out2

# Mates two individuals using one-point crossover
# Returns the two new individuals
def mate(ind1, ind2):
    ind1[0], ind2[0] = gp.cxOnePoint(ind1[0], ind2[0])
    ind1[1], ind2[1] = gp.cxOnePoint(ind1[1], ind2[1])
    return ind1, ind2

# Mutates a node of an individual
# Returns the mutated individual
def mutate_node(individual, pset):
    individual[0], = gp.mutNodeReplacement(individual[0], pset=pset)
    individual[1], = gp.mutNodeReplacement(individual[1], pset=pset)
    return individual,

# Mutates a subtree of an individual
# Returns the mutated individual
def mutate_subtree(individual, pset):
    individual[0], = gp.mutUniform(individual[0], expr=toolbox.expr, pset=pset)
    individual[1], = gp.mutUniform(individual[1], expr=toolbox.expr, pset=pset)
    return individual,
    
# Evaluates fitness of an individual
# Returns the fitness value
def evaluate(individual, bot):
    # Compile individual
    buy_trigger = gp.compile(individual[0], pset=pset)
    sell_trigger = gp.compile(individual[1], pset=pset)
    # Check if function is valid, i.e. changes with input
    if buy_trigger(1, 0, 0) == buy_trigger(1, 1, 1) and sell_trigger(1, 0, 0) == sell_trigger(1, 1, 1):
        return PENALTY, PENALTY
    # Check if the expression is valid
    if not is_valid(individual):
        return PENALTY, PENALTY
    # Simulate trades
    bot.set_trigger_expressions([buy_trigger, sell_trigger])
    p = bot.run()
    # Penalise if one or less trades are made
    if p['total_trades'] <= 1:
        return PENALTY, PENALTY
    return p['net_profit'], p['average_profit']

# Checks if an individual is valid
# Returns True if valid, otherwise False
def is_valid(individual):
    for expr in individual:
        # Limit the height of the tree
        if expr.height > 5:
            return False
        # At least one indicator must be used
        if 'macd_diff' not in str(expr) and 'rsi' not in str(expr):
            return False
    return True

# Create primitive set
pset = gp.PrimitiveSetTyped('MAIN', [float, float, float], bool)
pset.renameArguments(ARG0='t')
pset.renameArguments(ARG1='macd_diff')
pset.renameArguments(ARG2='rsi')

# Logical operators
pset.addPrimitive(operator.and_, [bool, bool], bool)
pset.addPrimitive(operator.or_, [bool, bool], bool)
pset.addPrimitive(operator.not_, [bool], bool)
pset.addPrimitive(if_then_else_float, [bool, float, float], float)
pset.addPrimitive(if_then_else_bool, [bool, bool, bool], bool)

# Comparison operators
pset.addPrimitive(operator.lt, [float, float], bool)
pset.addPrimitive(operator.gt, [float, float], bool)
pset.addPrimitive(operator.eq, [float, float], bool)

# Arithmetic operators
pset.addPrimitive(operator.add, [float, float], float)
pset.addPrimitive(operator.sub, [float, float], float)
pset.addPrimitive(operator.mul, [float, float], float)
pset.addPrimitive(protected_div, [float, float], float)
pset.addEphemeralConstant('random_number', lambda: float(random.randint(-100, 100)), float)
pset.addEphemeralConstant('random_boolean', lambda: bool(random.randint(0, 1)), bool)

# Create fitness function and individual class
creator.create('FitnessMax', base.Fitness, weights=(1, 0.1))    # Change this line if you want to change the weights
creator.create('Individual', list, fitness=creator.FitnessMax)
creator.create('Gene', gp.PrimitiveTree, pset=pset)

# Create toolbox
toolbox = base.Toolbox()
toolbox.register('expr', gp.genHalfAndHalf, pset=pset, min_=1, max_=2)
toolbox.register('gene', tools.initIterate, creator.Gene, toolbox.expr)
toolbox.register('individual', tools.initRepeat, creator.Individual, toolbox.gene, n=2)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)
toolbox.register('compile', gp.compile, pset=pset)
toolbox.register('select', tools.selTournament, tournsize=TOURNAMENT_SIZE)
toolbox.register('mate', mate)
toolbox.register('mutate_node', mutate_node, pset=pset)
toolbox.register('mutate_subtree', mutate_subtree, pset=pset)

# Runs the genetic algorithm
def evolve(bot):
    # Register fitness function
    toolbox.register('evaluate', evaluate, bot=bot)

    # Create population and hall of fame
    pop = toolbox.population(n=POPULATION_SIZE)
    hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

    # Run genetic algorithm
    for gen in range(GENERATIONS):
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        # Apply crossover on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CROSSOVER_RATE:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        # Apply mutation on the offspring
        for mutant in offspring:
            if random.random() < NODE_MUTATION_RATE:
                toolbox.mutate_node(mutant)
                del mutant.fitness.values
            if random.random() < SUBTREE_MUTATION_RATE:
                toolbox.mutate_subtree(mutant)
                del mutant.fitness.values
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        # Apply elitism
        elitism = tools.selBest(pop, int(len(pop) * ELITISM_RATE))
        offspring.extend(elitism)
        # Replace population with offspring
        pop[:] = offspring
        # Update hall of fame
        hof.update(pop)
        # Print statistics
        print(f'Generation {gen + 1}:')
        print(f'Best individual buy trigger: {hof[0][0]}')
        print(f'Best individual sell trigger: {hof[0][1]}')
        print(f'Best individual fitness: {hof[0].fitness.values[0], hof[0].fitness.values[1]}')
    
    # Return best individual
    best_expr = toolbox.compile(hof[0][0]), toolbox.compile(hof[0][1])
    return best_expr

# Optimises the buy and sell triggers for the trading bot
# Returns the best buy and sell triggers
def optimise_triggers(df):
    bot = TradingBot(df)
    buy_trigger, sell_trigger = evolve(bot)
    return buy_trigger, sell_trigger