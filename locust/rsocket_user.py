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
import string
import os
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
        if os.environ['VARIATION']=="1":
            self.loads = [os.environ['LOAD_SIZE_SMALL'],
            os.environ['LOAD_SIZE_MID'],
            os.environ['LOAD_SIZE_BIG'],]
            self.packages = [
            os.environ['PACKAGE_SIZE_SMALL'],
            os.environ['PACKAGE_SIZE_MID'],
            os.environ['PACKAGE_SIZE_BIG'],
            ]
    
    async def request_response(self, lb_address, port):
        while True:
            try:
                logging.info(lb_address)
                connection = await asyncio.open_connection(lb_address, port)
                break
            except ConnectionError as e:
                reconnect_time = 1
                logging.info(f"Unable to connect to client, reconnection in {reconnect_time} second(s)")
                time.sleep(reconnect_time)
                continue
        start_time = time.monotonic()

        async with RSocketClient(single_transport_provider(TransportTCP(*connection))) as client:
            if os.environ['VARIATION']=="1":
                package_size = int(random.choice(self.packages))
                load_size = random.choice(self.loads)
            else:
                package_size = int(os.environ['PACKAGE_SIZE'])
                load_size = os.environ['LOAD_SIZE']
            message = load_size + ":" + ''.join(random.choices(string.ascii_letters + string.digits, k=package_size//4))
            
            logging.info(f"sending req_resp {message[:10]}")
            response = await client.request_response(Payload(ensure_bytes(f'{message}')))
            response_time = int((time.monotonic() - start_time) * 1000)
            logging.info(f"LB response: {utf8_decode(response.data)}")
            # logging.info(f"Response metadata: {utf8_decode(response.metadata)}")
            
            return response, response_time