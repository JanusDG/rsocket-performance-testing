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
from chat_client import ChatClient
from rsocket.helpers import create_future, noop
from typing import Type, Callable
import time 
class IdentifiedHandler(BaseRequestHandler):
    def __init__(self, server_count: int,stack,round_robin, delay=timedelta(0)):
        self._delay = delay
        self._server_count = server_count
        self.stack = stack
        self.round_robin = round_robin

class Handler(IdentifiedHandler):
    async def request_response(self, payload: Payload) -> Awaitable[Payload]:
        logging.info("server recieved request")
        username = utf8_decode(payload.data)
        return create_future(Payload(ensure_bytes(f'server {self._server_count} recevied {username}')))


class LoadBalancerHandler(IdentifiedHandler):
    def __init__(self, server_count, stack,round_robin, delay=timedelta(0)):
        self._delay = delay
        self.stack = stack
        self.lb = None
        self.server_count = server_count
        self.round_robin = round_robin
    

    async def request_response(self, payload: Payload) -> Awaitable[Payload]:
        logging.info("server recieved request")
        response = await LoadBalancerRSocket(self.round_robin).request_response(payload)
        logging.info(f"response: {utf8_decode(response.data)}")
        return create_future(Payload(ensure_bytes(f'{utf8_decode(response.data)}')))

async def create_round_robin(server_count, stack):
    
    clients = []
    for i in range(server_count):
        try:
            connection = await asyncio.open_connection("0.0.0.0", 6566 + i)
        except ConnectionError:
            reconnect_time = 1
            logging.info(f"Unable to connect to client, reconnection in {reconnect_time} second(s)")
            time.sleep(reconnect_time)
            continue
        client = await stack.enter_async_context(RSocketClient(single_transport_provider(TransportTCP(*connection))))
        client = ChatClient(client)
        clients.append(client)
    round_robin = LoadBalancerRoundRobin(clients)
    return round_robin

class HandlerFactory:
    def __init__(self,
                 server_count: int,
                 
                 round_robin:LoadBalancerRoundRobin,
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
        self.round_robin = round_robin

    def factory(self) -> BaseRequestHandler:
        handler = self._handler_factory(self._server_count, self.round_robin,self.stack,self._delay)
        self._on_handler_create(handler)
        logging.info(f"handler")
        return handler

async def run_server(server_count):
    stack = AsyncExitStack()
    round_robin = await create_round_robin(server_count, stack)
    def session(*connection):
        RSocketServer(TransportTCP(*connection), handler_factory=HandlerFactory(server_count, stack,round_robin, LoadBalancerHandler).factory)

    async with await asyncio.start_server(session, '0.0.0.0', 6565) as server:
        logging.info(f"Server started")
        await server.serve_forever()
    await stack.aclose()

if __name__ == "__main__":
    asyncio.run(run_server(5))

