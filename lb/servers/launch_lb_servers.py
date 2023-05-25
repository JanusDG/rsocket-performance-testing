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

import time
import random

import os 

import argparse, sys
from worktypes import work_sleep, work_json, work_factorization


parser=argparse.ArgumentParser()
parser.add_argument("--server_count")
parser.add_argument("--port")
parser.add_argument("--work_type")
# parser.add_argument("--variation_scale")
parser.add_argument("--ip")
args=parser.parse_args()


worktypes = {
    "s":work_sleep,
    "j":work_json,
    "f":work_factorization,
}
worktype=worktypes[args.work_type]
# variation_scale=args.varisation_scale
ip=args.ip

class Handler(BaseRequestHandler):
    def __init__(self, server_id: int, delay=timedelta(0)):
        self._delay = delay
        self._server_id = server_id
    async def request_response(self, payload: Payload) -> Awaitable[Payload]:
        start_time = time.monotonic()
        message = utf8_decode(payload.data)
        logging.info(f"server {ip} (:{6566}) recieved request {message[:10]}")
        
        # simulate work
        m = int(message[:message.index(":")])
        worktype(m)
        # time.sleep(random.randint(1*1000,3*1000)/1000)


        response_time = int((time.monotonic() - start_time) * 1000)
        return create_future(Payload(data=ensure_bytes(f'server {ip} (:{6566}) processed {message[:10]}'),
                                     metadata=ensure_bytes(str(response_time))))


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
        return handler

async def run_server(host, port):
    def session(*connection):
        RSocketServer(TransportTCP(*connection),handler_factory=HandlerFactory(port-6566, Handler).factory) 

    async with await asyncio.start_server(session, host, port) as server:
        logging.info(f"started server on port {port}")
        await server.serve_forever()

async def run_all(host,server_count):
    tasks = []
    for i in range(server_count):
        tasks.append(run_server(host, 6566+i))
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    host = os.environ['HOST']
    
    if args.port is None:
        server_count = int(args.server_count)
        asyncio.run(run_all(host, server_count))
    else:
        asyncio.run(run_server(host, int(args.port)))
