import asyncio
from typing import List

from rsocket.load_balancer.load_balancer_strategy import LoadBalancerStrategy
from rsocket.rsocket import RSocket

import copy
# Weighted
class LoadBalancerWeightenedRoundRobin(LoadBalancerStrategy):
    def __init__(self,
                 pool: List[RSocket], 
                 weights: List[int],
                 auto_connect=True,
                 auto_close=True):
        self._auto_close = auto_close
        self._auto_connect = auto_connect
        sorted_pairs = sorted(zip(weights,pool), reverse=True, key=lambda x: x[0])
        weights,pool = zip(*sorted_pairs)
        self._pool = list(pool)
        self._weights = list(weights)
        self._curweights = copy.deepcopy(self._weights)
        self._current_index = 1

    # def select(self) -> RSocket:
    #     if sum(self._curweights) == 0:
    #         self._curweights = copy.deepcopy(self._weights)
    #         self._current_index = 0
        
    #     while self._curweights[self._current_index] == 0:
    #         self._current_index = (self._current_index + 1) % len(self._pool)

    #     client = self._pool[self._current_index]
    #     self._curweights[self._current_index] -= 1
    #     self._current_index = (self._current_index + 1) % len(self._pool)
    #     return client

    def select(self):
        it = self._current_index
        for i in range(len(self._weights)):
            if self._weights[i]-it<0:
                it-=self._weights[i]
                continue
            else:
                self._current_index = (self._current_index % sum(self._weights)) + 1
                return self._pool[i]

    async def connect(self):
        if self._auto_connect:
            [await client.connect() for client in self._pool]

    async def close(self):
        if self._auto_close:
            await asyncio.gather(*[client.close() for client in self._pool],
                                 return_exceptions=True)
