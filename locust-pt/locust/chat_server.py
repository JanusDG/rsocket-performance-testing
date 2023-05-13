import asyncio
import logging

from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import create_future, utf8_decode
from rsocket.local_typing import Awaitable
from rsocket.payload import Payload
from rsocket.request_handler import BaseRequestHandler
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP
from datetime import timedelta
from rsocket.helpers import create_future, noop

from typing import Tuple, Any
from typing import Type, Callable

class IdentifiedHandler(BaseRequestHandler):
    def __init__(self, server_id: int, delay=timedelta(0)):
        self._delay = delay
        self._server_id = server_id

class Handler(IdentifiedHandler):
    async def request_response(self, payload: Payload) -> Awaitable[Payload]:
        logging.info("server recieved request")
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

async def start_server(port):
    def session(*connection):
        RSocketServer(TransportTCP(*connection), handler_factory=Handler)
    
    def session_handler(*connection):
        # nonlocal server
        server = RSocketServer(TransportTCP(*connection),handler_factory=HandlerFactory(0, Handler).factory)    
    
    async def server_serve_forever(port):
        async with await asyncio.start_server(session_handler, 'localhost', port) as server:
            await server.serve_forever()
    
    async def server_start_serving(port):
        server = await asyncio.start_server(session_handler, 'localhost', port)
        await server.start_serving()
        return server
        
    await server_serve_forever(port)
    



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_server())
