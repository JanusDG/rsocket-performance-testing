import asyncio
import logging

from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import create_future, utf8_decode
from rsocket.local_typing import Awaitable
from rsocket.payload import Payload
from rsocket.request_handler import BaseRequestHandler
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP
from rsocket.helpers import create_future, noop
from typing import Type, Callable
from datetime import timedelta

class IdentifiedHandler(BaseRequestHandler):
    def __init__(self, server_id: int, delay=timedelta(0)):
        self._delay = delay
        self._server_id = server_id

class Handler(IdentifiedHandler):
    async def request_response(self, payload: Payload) -> Awaitable[Payload]:
        logging.info(f"server {self._server_id} (:{self._server_id+6566}) recieved request")
        username = utf8_decode(payload.data)
        return create_future(Payload(ensure_bytes(f'server {self._server_id} recevied {username}')))


class HandlerFactory:
    def __init__(self,
                 server_id: int,
                 handler_factory: Type[Handler],
                 delay=timedelta(0),
                 on_handler_create: Callable[[Handler], None] = noop):
        self._on_handler_create = on_handler_create
        self._delay = delay
        self._server_id = server_id
        self._handler_factory = handler_factory

    def factory(self) -> BaseRequestHandler:
        handler = self._handler_factory(self._server_id, self._delay)
        self._on_handler_create(handler)
        logging.info(f"handler")
        return handler

async def run_server(port):
    def session(*connection):
        RSocketServer(TransportTCP(*connection),handler_factory=HandlerFactory(port-6566, Handler).factory) 

    async with await asyncio.start_server(session, '0.0.0.0', port) as server:
        logging.info(port)
        await server.serve_forever()

async def run_all(server_count):
    tasks = []
    for i in range(server_count):
        tasks.append(run_server(6566+i))
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_all(5))
