import asyncio
import logging

from rsocket.helpers import utf8_decode
from rsocket.payload import Payload
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP
from rsocket.load_balancer.load_balancer_rsocket import LoadBalancerRSocket
from rsocket.load_balancer.round_robin import LoadBalancerRoundRobin
from typing import Optional
from rsocket.helpers import single_transport_provider, utf8_decode
from rsocket.payload import Payload
from rsocket.transports.tcp import TransportTCP
from rsocket.payload import Payload
from rsocket.rsocket_server import RSocketServer
from asyncio import Event
from asyncio.base_events import Server
from typing import Optional
from rsocket.helpers import single_transport_provider
from rsocket.rsocket_client import RSocketClient
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP
from contextlib import AsyncExitStack

from chat_server import *
from chat_client import ChatClient

class ConnectionServerWrapper:
    def __init__(self, server_id):
        self.server_id = server_id
    def return_session(self):
        server: Optional[RSocketServer] = None
        server_id: int = self.server_id
    
        def session(*connection):
            nonlocal server
            server = RSocketServer(TransportTCP(*connection),handler_factory=HandlerFactory(server_id, Handler).factory)
        return session

async def launch_server(host, server_id, server):
    await server.start_serving()
    logging.info(f"Server {6565+ server_id} started")

async def launch_lb_servers(server_count, host):
    for i in range(server_count):
        wrapper = ConnectionServerWrapper(i)
        server = await asyncio.start_server(wrapper.return_session(), host, 6565 + i)
        print(server.is_serving())
        await launch_server(host, i, server)

async def launch_lb(host, server_count, request_count):

    await launch_lb_servers(server_count, host)
            
    async with AsyncExitStack() as stack:
        clients = []
        for i in range(server_count):
            connection = await asyncio.open_connection(host, 6565 + i)

            client = await stack.enter_async_context(RSocketClient(single_transport_provider(TransportTCP(*connection))))
            client = ChatClient(client)
            clients.append(client)
        
        round_robin = LoadBalancerRoundRobin(clients)
        for j in range(request_count):
            response = await LoadBalancerRSocket(round_robin).request_response(Payload(('request %d' % j).encode()))
            logging.info(f"response: {utf8_decode(response.data)}")
        
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    future = asyncio.run(launch_lb('localhost',3,10))