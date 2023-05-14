from rsocket.request_handler import BaseRequestHandler
import logging
from rsocket.helpers import create_future, utf8_decode
from rsocket.local_typing import Awaitable
from rsocket.payload import Payload
from rsocket.frame_helpers import ensure_bytes
from datetime import timedelta

import asyncio
from contextlib import AsyncExitStack

from rsocket.rsocket_client import RSocketClient

from rsocket.helpers import single_transport_provider
from rsocket.load_balancer.round_robin import LoadBalancerRoundRobin
from rsocket.rsocket_server import RSocketServer
from rsocket.load_balancer.load_balancer_rsocket import LoadBalancerRSocket

from rsocket.transports.tcp import TransportTCP
from rsocket.helpers import create_future, noop
from typing import Type, Callable
import time 
from typing import Optional

from collections import deque

import os
import random

from strategies.weighted_round_robin import LoadBalancerWeightenedRoundRobin
from strategies.dynamic_weighted_round_robin import LoadBalancerDynamicWeightenedRoundRobin

load_balancing_strategy = LoadBalancerRoundRobin

class ChatClient:
    def __init__(self, rsocket: RSocketClient):
        self._rsocket = rsocket
        self._latancy_stack = deque(maxlen=3)
        self._connection_count = 0

    async def request_response(self, request_payload: Payload):
        self._connection_count += 1
        response = await self._rsocket.request_response(request_payload)
        request_time = utf8_decode(response.metadata)
        # logging.info(f"{request_time}")
        self._latancy_stack.append(int(request_time))
        self._connection_count -= 1
        return response

    def connection_count(self):
        return self._connection_count

    def avarage_server_latency(self):
        return sum(self._latancy_stack)/len(self._latancy_stack)


class LoadBalancerHandler(BaseRequestHandler):
    def __init__(self, server_count, stack, lb_strategy, delay=timedelta(0)):
        self._delay = delay
        self.stack = stack
        self.lb = None
        self.server_count = server_count
        self.lb_strategy = lb_strategy

    async def request_response(self, payload: Payload) -> Awaitable[Payload]:
        # logging.info("server recieved request")
        response = await LoadBalancerRSocket(self.lb_strategy).request_response(payload)
        logging.info(f"{utf8_decode(response.data)} in {utf8_decode(response.metadata)}ms")
        return create_future(Payload(ensure_bytes(f'{utf8_decode(response.data)}')))

async def create_lb_strategy(server_count, stack, host):
    clients = []
    for i in range(server_count):
        try:
            connection = await asyncio.open_connection(host, 6566 + i)
        except ConnectionError:
            reconnect_time = 1
            logging.info(f"Unable to connect to client, reconnection in {reconnect_time} second(s)")
            time.sleep(reconnect_time)
            continue
        cl = await stack.enter_async_context(RSocketClient(single_transport_provider(TransportTCP(*connection))))
        client = ChatClient(cl)
        clients.append(client)
    # lb_strategy = load_balancing_strategy(pool=clients,weights=[random.randint(2,3)for i in range(len(clients))])
    lb_strategy = load_balancing_strategy(pool=clients)
    return lb_strategy

class HandlerFactory:
    def __init__(self,
                 server_count: int,
                 lb_strategy:load_balancing_strategy,
                 stack:AsyncExitStack,
                 handler_factory: Type[LoadBalancerHandler],
                 delay=timedelta(0),
                 on_handler_create: Callable[[LoadBalancerHandler], None] = noop,
                 ):
        self._on_handler_create = on_handler_create
        self._delay = delay
        self._server_count = server_count
        self._handler_factory = handler_factory
        self.stack = stack
        self.lb_strategy = lb_strategy

    def factory(self) -> BaseRequestHandler:
        handler = self._handler_factory(self._server_count, self.lb_strategy,self.stack,self._delay)
        self._on_handler_create(handler)
        # logging.info(f"handler")
        return handler

async def run_lb(server_count, host,port):
    stack = AsyncExitStack()
    lb_strategy = await create_lb_strategy(server_count, stack, host)
    def session(*connection):
        RSocketServer(TransportTCP(*connection), handler_factory=HandlerFactory(server_count, stack,lb_strategy, LoadBalancerHandler).factory)

    async with await asyncio.start_server(session, host, port) as server:
        logging.info(f"Started load balancer on port {port}")
        await server.serve_forever()
    await stack.aclose()

if __name__ == "__main__":
    host = os.environ['HOST']
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_lb(5, host, 6565))

