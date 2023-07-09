import asyncio
from typing import Any, AsyncIterator

from torrent_client.peer.message_id import MessageID
from torrent_client.peer.messages.messages_data import Response
from torrent_client.peer.peer_net.peer_net import AbstractPeerNet


class FakePeerNet(AbstractPeerNet):
    def __init__(self):
        self.sent_message = None
        self.next_response = None

    async def __anext__(self) -> Response:
        return await self.read()

    async def read(self) -> Response:
        while True:
            if self.next_response:
                break
            await asyncio.sleep(0.01)
        next_message, self.next_response = self.next_response, None
        return next_message

    async def read_handshake(self) -> Response:
        return await self.read()

    async def send(self, message: Any, message_id: MessageID) -> None:
        self.sent_message = message
