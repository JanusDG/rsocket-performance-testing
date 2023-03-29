import asyncio
import time
import logging

from rsocket.helpers import single_transport_provider, utf8_decode
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP

from locust import User


class RsocketUser(User):
    abstract = True

    def __init__(self, environment):
        super().__init__(environment)
    
    async def request_response(self):
            connection = await asyncio.open_connection('localhost', 6565)
            start_time = time.monotonic()

            async with RSocketClient(single_transport_provider(TransportTCP(*connection))) as client:
                response = await client.request_response(Payload(data=b'George'))
                response_time = int((time.monotonic() - start_time) * 1000)
                logging.info(f"Server response: {utf8_decode(response.data)}")
                logging.info(f"Response metadata: {utf8_decode(response.metadata)}")
                
                return response, response_time