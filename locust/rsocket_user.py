import asyncio
import time
import logging
from typing import Optional

from rsocket.helpers import single_transport_provider, utf8_decode
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP
from rsocket.rsocket_server import RSocketServer
from rsocket.frame_helpers import ensure_bytes

from locust import User

from chat_server import HandlerFactory, Handler

import random

class ConnectionServerWrapper:
    def __init__(self, server_id):
        self.server_id = server_id
    def return_session(self):
        server: Optional[RSocketServer] = None
        server_id: int = self.server_id
    
        def session(*connection):
            nonlocal server
            server = RSocketServer(TransportTCP(*connection),handler_factory=HandlerFactory(server_id, Handler).factory)
            return server
        return session

class RsocketUser(User):
    abstract = True

    def __init__(self, environment):
        super().__init__(environment)
        logging.basicConfig(level=logging.INFO)
    
    async def request_response(self, port):
        while True:
            try:
                connection = await asyncio.open_connection('lb', port)
                break
            except ConnectionError as e:
                reconnect_time = 1
                logging.info(f"Unable to connect to client, reconnection in {reconnect_time} second(s)")
                time.sleep(reconnect_time)
                continue
        start_time = time.monotonic()

        async with RSocketClient(single_transport_provider(TransportTCP(*connection))) as client:
            message = random.randint(1,10**8)
            logging.info(f"sending req_resp {message}")
            response = await client.request_response(Payload(ensure_bytes(f'req_resp {message}')))
            response_time = int((time.monotonic() - start_time) * 1000)
            logging.info(f"LB response: {utf8_decode(response.data)}")
            # logging.info(f"Response metadata: {utf8_decode(response.metadata)}")
            
            return response, response_time