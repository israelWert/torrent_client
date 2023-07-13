from typing import Any

from torrent_client.peer.p2p_messages_handling.message_id import MessageID
from torrent_client.peer.p2p_messages_handling.p2p_messages import Response
from torrent_client.peer.p2p_messages_handling.p2p_codec import AbstractP2PCodec


class FakeP2PCodec(AbstractP2PCodec):
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
    def length_datatype_size(self) -> int:
        return self._length_bit_size
