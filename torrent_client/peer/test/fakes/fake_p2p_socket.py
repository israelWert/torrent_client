import asyncio
from typing import Any

from torrent_client.peer.p2p_messages_handling.message_id import MessageID
from torrent_client.peer.p2p_messages_handling.p2p_messages import Response
from torrent_client.peer.p2p_net.p2p_socket import AbstractP2PSocket


class FakeP2PSocket(AbstractP2PSocket):
    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __init__(self):
        self.sent_message = None
        self.next_response = None
        self._have_sent_new_message = False

    async def __anext__(self) -> Response:
        return await self.read()

    def is_read_response(self):
        return self.next_response is None

    async def read(self) -> Response:
        while True:
            if self.next_response:
                break
            await asyncio.sleep(0.01)
        next_message, self.next_response = self.next_response, None
        return next_message

    async def read_handshake(self) -> Response:
        return await self.read()

    def have_sent_new_message(self) -> bool:
        if self._have_sent_new_message:
            self._have_sent_new_message = False
            return True
        return False

    async def send(self, message: Any, message_id: MessageID) -> None:
        self._have_sent_new_message = True
        self.sent_message = message
