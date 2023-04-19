import asyncio
import logging
from typing import Awaitable

from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import utf8_decode, create_response
from rsocket.payload import Payload
from rsocket.routing.request_router import RequestRouter
from rsocket.routing.routing_request_handler import RoutingRequestHandler
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP

import asyncio
import json
from dataclasses import dataclass
from datetime import timedelta
from math import ceil
from typing import Tuple, Any
from typing import Type, Callable
from rsocket.frame_helpers import str_to_bytes, ensure_bytes
from rsocket.helpers import create_future, noop
from rsocket.logger import logger
from rsocket.payload import Payload
from rsocket.request_handler import BaseRequestHandler, RequestHandler
from rsocket.rsocket_base import RSocketBase
from rsocket.rsocket_client import RSocketClient
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.transport import Transport
from typing import Awaitable

class IdentifiedHandler(BaseRequestHandler):
    def __init__(self, server_id: int, delay=timedelta(0)):
        self._delay = delay
        self._server_id = server_id

class Handler(IdentifiedHandler):
    async def request_response(self, payload: Payload) -> Awaitable[Payload]:
        username = utf8_decode(payload.data)
        return create_future(Payload(ensure_bytes(f'server {self._server_id} recevied {username}')))

class HandlerFactory:
    def __init__(self,
                 server_id: int,
                 handler_factory: Type[Handler],
                 delay=timedelta(0),
                 on_handler_create: Callable[[RequestHandler], None] = noop):
        self._on_handler_create = on_handler_create
        self._delay = delay
        self._server_id = server_id
        self._handler_factory = handler_factory

    def factory(self) -> BaseRequestHandler:
        handler = self._handler_factory(self._server_id, self._delay)
        self._on_handler_create(handler)
        return handler

async def run_server(server_id):
    def session(*connection):
        RSocketServer(TransportTCP(*connection), handler_factory=HandlerFactory(server_id, Handler).factory)

    async with await asyncio.start_server(session, 'localhost', 6565 + server_id) as server:
        logging.info(f"Server {server_id} started")
        await server.serve_forever()
        # return server


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server(1))
