import gevent
from chat_server import run_server
from locust import events, task
from locust_user import RsocketUser

import logging

from rsocket.helpers import single_transport_provider, utf8_decode
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP
from locust import task, constant

import gevent.monkey
gevent.monkey.patch_all()
import asyncio
# asyncio.set_event_loop_policy(asyncio_gevent.EventLoopPolicy())
import gevent



@events.init.add_listener
def run_rsocket_server(environment, **_kwargs):
    def async_run_server():
        asyncio.run(run_server()) 
    gevent.spawn(async_run_server)
    logging.info(f"server started")


class ResponseRsocketUser(RsocketUser):
    wait_time = constant(5)

    @task
    def getResponse(self):
        logging.info("getResponse task started")
        async def request_response():
            connection = await asyncio.open_connection('localhost', 6565)

            async with RSocketClient(single_transport_provider(TransportTCP(*connection))) as client:
                response = await client.request_response(Payload(data=b'George'))

                logging.info(f"Server response: {utf8_decode(response.data)}")
        loop =  asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(request_response(), loop)
