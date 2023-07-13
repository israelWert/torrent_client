import struct
from abc import ABC, abstractmethod
from typing import Any

from torrent_client.peer.p2p_messages_handling.message_id import MessageID
from torrent_client.peer.p2p_messages_handling.bitfieled_message_factory import BitfieldMessageFactory
from torrent_client.peer.p2p_messages_handling.fixed_message_factory import FixedMessageFactory
from torrent_client.peer.p2p_messages_handling.piece_message_factory import PieceMessageFactory
from torrent_client.peer.p2p_messages_handling.message_factory import MessageFactory
from torrent_client.peer.p2p_messages_handling.p2p_messages import HandshakeMessage, ChokeMessage, UnchokeMessage, \
    HaveMessage, RequestMessage, InterestedMessage, NotInterestedMessage, Response


class AbstractP2PCodec(ABC):
    @abstractmethod
    def encode(self, message: Any, message_id: MessageID) -> bytes:
        pass

    @abstractmethod
    def decode_response_not_handshake(self, payload: bytes) -> Response:
        pass

    @abstractmethod
    def decode_handshake(self, payload: bytes) -> Response:
        pass

    @abstractmethod
    def decode_response_length(self, payload: bytes) -> int:
        pass

    @property
    @abstractmethod
    def handshake_size(self) -> int:
        pass

    @property
    @abstractmethod
    def length_datatype_size(self) -> int:
        pass


class P2PCodec(AbstractP2PCodec):
    _HEADER_STRUCT = struct.Struct("!IB")
    _LENGTH_STRUCT = struct.Struct("!I")

    _CONSTANT_MESSAGES_FACTORIES = {
        MessageID.Choke: FixedMessageFactory(ChokeMessage, struct.Struct("")),
        MessageID.Unchoke: FixedMessageFactory(UnchokeMessage, struct.Struct("")),
        MessageID.Interested: FixedMessageFactory(InterestedMessage, struct.Struct("")),
        MessageID.NotInterested: FixedMessageFactory(NotInterestedMessage, struct.Struct("")),
        MessageID.Piece: PieceMessageFactory(),
        MessageID.Have: FixedMessageFactory(HaveMessage, struct.Struct("!I")),
        MessageID.Request: FixedMessageFactory(RequestMessage, struct.Struct("!III")),
        MessageID.Handshake: FixedMessageFactory(HandshakeMessage, struct.Struct("!B19s8s20s20s"))
    }

    def __init__(self, bitfield_size: int):
        self._messages_factories: dict[MessageID, MessageFactory] = self._CONSTANT_MESSAGES_FACTORIES
        self._messages_factories[MessageID.Bitfiled] = BitfieldMessageFactory(bitfield_size)

    def encode(self, message: Any, message_id: MessageID) -> bytes:
        encoded_message = self._messages_factories[message_id].encode(message)
        header = b""
        if message_id != MessageID.Handshake:
            length = len(encoded_message) + 1
            header = self._HEADER_STRUCT.pack(length, message_id.value)
        return header + encoded_message

    def decode_response_length(self, payload: bytes) -> int:
        return self._LENGTH_STRUCT.unpack(payload)[0]

    def _decode_header(self, payload: bytes) -> tuple[int, MessageID, bytes]:
        header_size = self._HEADER_STRUCT.size
        header, rest = payload[:header_size], payload[header_size:]
        length, _id = self._HEADER_STRUCT.unpack(header)
        _id = MessageID(_id)
        return length, _id, rest

    def decode_response_not_handshake(self, payload: bytes) -> Response:
        length, message_id, rest = self._decode_header(payload)
        message_data = self._messages_factories[message_id].decode(rest)
        return Response(message_id, length, message_data
                        )

    def decode_handshake(self, payload: bytes) -> Response:
        message_data = self._messages_factories[MessageID.Handshake].decode(payload)
        return Response(
            MessageID.Handshake,
            self.handshake_size,
            message_data
        )

    @property
    def handshake_size(self):
        return self._CONSTANT_MESSAGES_FACTORIES[MessageID.Handshake].size

    @property
    def length_datatype_size(self):
        return self._LENGTH_STRUCT.size
