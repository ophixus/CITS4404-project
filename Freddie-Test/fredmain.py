import numpy as np
import random as rd
import ccxt
import ta
import pandas as pd
import heapq
import math


from GeneticAlg import individual, population

pop_size = 100
n_gens = 200
keep_best = 75
crossover = 25
external_mutation_probability = 0.2
internal_mutation_probability = 0.2

def fetch_data(timeframe):
    exchange = ccxt.kraken()
    ohlcv = exchange.fetch_ohlcv('BTC/AUD', timeframe=timeframe)
    return ohlcv



def main():

    data = fetch_data('1d')

    #runs algorithm
    test_gen = population(pop_size)
    test_gen.run_gen_al(keep_best,crossover,data,n_gens,external_mutation_probability,internal_mutation_probability)

    #stores fitness value of the final population in a pandas data frame
    check = test_gen.population
    df = pd.DataFrame(columns=['fitness_score'])
    for i in range(len(check)):
        fit = check[i].fitness(data)
        df.loc[i] = fit

    #prints how many of each fitness function is produced
    print(df.value_counts())

    #prints optimal solution (or one of the most optimal)
    index = df.values.argmax()
    print(check[index])
    print('The profit of the optimal solution is: ' + str(check[index].profit))




# Run main function
if __name__ == "__main__":
    main()





