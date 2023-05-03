
import numpy as np
import random as rd
import ccxt
import ta
import pandas as pd
import heapq
import math

from trading_bot import TradingBot




class individual:
    
    def __init__(self, inputs = [[0,0],0,0,[0,0]]):
                 
                #  macd_range = [0,0],rsi_int=0,crit_macd=0,rsi_bs_range = [0,0]):
        self.macd_lower = inputs[0][0]
        self.macd_higher = inputs[0][1]
        self.rsi_int = inputs[1]
        self.crit_macd = inputs[2]
        self.rsi_buy = inputs[3][0]
        self.rsi_sell = inputs[3][1]

        # if auto_create:
        #     self.create_individual()

    def __str__(self):
        out = ''
        out += f'MACD lower bound is: {self.macd_lower} \n'
        out += f'MACD higher bound is: {self.macd_higher}\n'
        out += f'RSI is: {self.rsi_int}\n'
        out += f'MACD critical value is: {self.crit_macd}\n'
        out += f'RSI buy value is: {self.rsi_buy}\n'
        out += f'RSI sell value is: {self.rsi_sell}\n'
        return out

    def macd_window(self):
        self.macd_lower = rd.randint(3,80)
        self.macd_higher = rd.randint(self.macd_lower,100)

    def rsi_window(self):
        self.rsi_int = rd.randint(5,70)

    def buy_sell_macd(self):
        random_int = rd.randint(-10,10)
        random_float = rd.random()
        self.crit_macd = random_int*random_float

    def buy_sell_rsi(self):
        self.rsi_sell = rd.randint(60,90)
        self.rsi_buy = rd.randint(10,40)

    def create_individual(self):
        self.macd_window()
        self.rsi_window()
        self.buy_sell_macd()
        self.buy_sell_rsi()

    def create_crossover_list(self):
        self.crossover_list = [ [self.macd_lower, self.macd_higher], self.rsi_int, self.crit_macd, [self.rsi_buy, self.rsi_sell] ]


    def mating(self,mate):
        crossover_point = rd.randint(1,4)
        self.create_crossover_list()
        mate.create_crossover_list()
        big_list = self.crossover_list[:crossover_point] + mate.crossover_list[crossover_point:]

        offspring = individual(big_list) 
        return offspring
    

    def mutate(self,mutation_probability):

        for i in range(4):
            if rd.random() < mutation_probability:

                if i == 0:
                    self.macd_window()
                elif i == 1:
                    self.rsi_window()
                elif i == 2:
                    self.buy_sell_macd()
                elif i == 3: 
                    self.buy_sell_rsi   

    def fitness(self,data):
        data_frame = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data_frame['macd_diff'] = ta.trend.macd_diff(data_frame['close'], window_slow=self.macd_higher, window_fast=self.macd_lower)
        data_frame['rsi'] = ta.momentum.rsi(data_frame['close'], window=self.rsi_int)
        PARAMETERS = {'buy_macd_diff': self.buy_sell_macd, 'buy_rsi': self.rsi_buy, 'sell_macd_diff': self.buy_sell_macd, 'sell_rsi': self.rsi_sell}
        expressions = []
        bot = TradingBot(data_frame)
        bot.set_trigger_expressions(expressions)
        fitness_stats = bot.run()
        self.profit = fitness_stats['net_profit']
        
        self.fitness_score = (1+self.profit/100)        +    3    *(fitness_stats['total_trades']) * math.copysign(1,self.profit)
        
        if fitness_stats['total_trades'] == 0:
            self.fitnes_score = -100000

        # if self.fitness_score == 0:
        #     self.fitnes_score = -1000000000



        return self.fitness_score
    

class population:
    def __init__(self,pop_size):
        self.pop_size = pop_size


    def create_population(self):
        population = []
        for i in range(self.pop_size):
            person = individual()
            person.create_individual()
            population.append(person)
        self.population = population
        return self.population
    
    def mate_parents(self,parents,n_children):  
        "Perhaps n_children is == pop_size"
        n_parents = len(parents)
        offspring = []

        for i in range(n_children):

            rand_list = rd.sample(range(n_parents),2)
            p1 = self.population[rand_list[0]]
            p2 = self.population[rand_list[1]]
            child = p1.mating(p2)
            offspring.append(child)
        
        return offspring
    
    def mutate_population(self,external_mutation_probability, internal_mutation_probability):
            for i in range(len(self.population)):
                 if rd.random()<external_mutation_probability:
                      self.population[i].mutate(internal_mutation_probability)

    def population_fitness(self,testing_data):
        fitness_list = []
        for i in range(len(self.population)):

            
            fitness_score = self.population[i].fitness(testing_data)
            
            fitness_list.append(fitness_score)
        self.pop_fitness = fitness_list
            
        return self.pop_fitness
    
    def select_best(self,n_best,testing_data,print_stats = False):
        fitness_list = self.population_fitness(testing_data)
        largest_nums = heapq.nlargest(n_best,fitness_list)
        largest_indexes = []
        for num in largest_nums:
            for i, x in enumerate(fitness_list):
                if x == num:
                    largest_indexes.append(i)
        best_list = []
        for i in range(n_best):
            best_list.append(self.population[largest_indexes[i]])
        self.best_list = best_list

        if print_stats:

            print('Best performance is {}, mean is {}, worst is {}'.format(
                max(fitness_list),
                np.mean(fitness_list),
                min(fitness_list)))

        return best_list
            
    def next_generation(self,keep_best,crossover,testing_data):
        current_population = self.population
        survival = self.select_best(keep_best,testing_data)
        mating = self.mate_parents(current_population,crossover)
        self.population = survival+mating
        # print(self.population)


    def run_gen_al(self,keep_best,crossover,testing_data,n_gens,external_mutation_probability,internal_mutation_probability):
        self.create_population()
        for i in range(n_gens):
            self.next_generation(keep_best,crossover,testing_data)
            if i == n_gens-1:
                self.select_best(keep_best,testing_data,True)
            else:
                self.mutate_population(external_mutation_probability,internal_mutation_probability)




        
                





        



