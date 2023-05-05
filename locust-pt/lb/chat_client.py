import asyncio
import logging
from typing import Optional

from rsocket.extensions.helpers import composite, route
from rsocket.extensions.mimetypes import WellKnownMimeTypes
from rsocket.frame_helpers import ensure_bytes
from rsocket.helpers import single_transport_provider, utf8_decode
from rsocket.payload import Payload
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP


class ChatClient:
    def __init__(self, rsocket: RSocketClient):
        self._rsocket = rsocket

    async def request_response(self, request_payload):
        response = await self._rsocket.request_response(request_payload)
        print(f'Server response: {utf8_decode(response.data)}')
        return response

async def main():
    connection = await asyncio.open_connection('localhost', 6565)

    async with RSocketClient(single_transport_provider(TransportTCP(*connection)),
                             metadata_encoding=WellKnownMimeTypes.MESSAGE_RSOCKET_COMPOSITE_METADATA) as client1:
        user = ChatClient(client1)

        payload = Payload(data=ensure_bytes('user1'))
        await user.request_response(payload)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
