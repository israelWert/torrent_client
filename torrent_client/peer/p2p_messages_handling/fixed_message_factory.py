from dataclasses import astuple
from struct import Struct
from typing import Type, Any

from torrent_client.peer.p2p_messages_handling.message_factory import MessageFactory, PeerMessage_


class FixedMessageFactory(MessageFactory):
    def __init__(self, message_type: Type[PeerMessage_], struct: Struct):
        self._class = message_type
        self._struct = struct

    def decode(self, data: bytes) -> PeerMessage_:
        return self._class(*self._struct.unpack(data))

    def encode(self, obj: Any) -> bytes:
        return self._struct.pack(*astuple(obj))

    @property
    def size(self):
        return self._struct.size
