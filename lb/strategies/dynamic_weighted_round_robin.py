import asyncio
from typing import List

from rsocket.load_balancer.load_balancer_strategy import LoadBalancerStrategy
from rsocket.rsocket import RSocket

import copy
from collections import Counter
import math
# def get_lcm(nums):
#     def get_prime_factors(num):
#         factors = Counter()
#         div = 2
#         while num > 1:
#             while num % div == 0:
#                 factors[div] += 1
#                 num //= div
#             div += 1
#             if div * div > num and num > 1:
#                 factors[num] += 1
#                 break
#         return factors
#     factors = Counter()
#     for num in nums:
#         num_factors = get_prime_factors(num)
#         for factor, count in num_factors.items():
#             factors[factor] = max(factors[factor], count)
#     lcm = 1
#     for factor, count in factors.items():
#         lcm *= factor ** count
#     return lcm

class LoadBalancerDynamicWeightenedRoundRobin(LoadBalancerStrategy):
    def __init__(self,
                 pool: List[RSocket], 
                 auto_connect=True,
                 auto_close=True):
        self._auto_close = auto_close
        self._auto_connect = auto_connect
        self._pool = pool
        self._weights = [1 for i in range(len(self._pool))]
        self._current_index = 1

    # def select(self) -> RSocket:
    #     if sum(self._weights) == 0:
    #         latencies = [round(client.avarage_server_latency()/100)*100 for client in self._pool]
    #         inverted_weights = [int(math.ceil(lat / min(latencies))) for lat in latencies]
    #         lcm = get_lcm(inverted_weights)
    #         pool = self._pool
    #         weights = [int(lcm/iw) for iw in inverted_weights]
    #         sorted_pairs = sorted(zip(weights,pool), reverse=True, key=lambda x: x[0])
    #         weights, pool = zip(*sorted_pairs)
    #         self._pool = list(pool)
    #         self._weights = list(weights)      
    #         self._current_index = 0
        
    #     while self._weights[self._current_index] == 0:
    #         self._current_index = (self._current_index + 1) % len(self._pool)

    #     client = self._pool[self._current_index]
    #     self._weights[self._current_index] -= 1
    #     self._current_index = (self._current_index + 1) % len(self._pool)
    #     return client
    def select(self):
        it = self._current_index
        for i in range(len(self._weights)):
            if self._weights[i]-it<0:
                it-=self._weights[i]
                continue
            else:
                client = self._pool[i]
                if (self._current_index) == sum(self._weights):
                    lat = [client.avarage_server_latency() for client in self._pool]
                    inverted = [math.ceil(l/max(1,min(lat))) for l in lat]
                    self._weights = [max(inverted)//max(1,ll) for ll in inverted]
                    self._current_index = 1
                else:
                    self._current_index += 1
                return client

    async def connect(self):
        if self._auto_connect:
            [await client.connect() for client in self._pool]

    async def close(self):
        if self._auto_close:
            await asyncio.gather(*[client.close() for client in self._pool],
                                 return_exceptions=True)
