from typing import Any

from torrent_client.peer.message_id import MessageID
from torrent_client.peer.messages.messages_data import Response
from torrent_client.peer.peer_net.peer_protocol import AbstractPeerProtocol


class FakePeerProtocol(AbstractPeerProtocol):
    def __init__(self):
        self.decode_received = None
        self.decode_response = None
        self.length_response = 10
        self._length_bit_size = 4
        self.length_received = None

    def decode_response_not_handshake(self, payload: bytes) -> Response:
        self.decode_received = payload
        return self.decode_response

    def decode_handshake(self, payload: bytes) -> Response:
        self.decode_received = payload
        return self.decode_response

    def encode(self, message: Any, message_id: MessageID) -> bytes:
        pass

    def decode_response_length(self, payload: bytes) -> int:
        self.length_received = payload
        return self.length_response

    @property
    def handshake_size(self) -> int:
        return self.length_response

    @property
    def length_byte_size(self) -> int:
        return self._length_bit_size
