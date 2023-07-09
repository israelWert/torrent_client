from dataclasses import dataclass
from typing import Final, Annotated, List, Any

from torrent_client.peer.message_id import MessageID


@dataclass
class Response:
    id: MessageID
    length: int
    message: Any


@dataclass
class PieceMessage:
    index: int
    begin: int
    block: bytes


@dataclass
class HandshakeMessage:
    START_INT: int = 19
    START_STR: bytes = b"BitTorrent protocol"
    EXTEND_STR: bytes = bytes(8)
    info_hash: Annotated[bytes, 20] = None
    peer_id: Annotated[bytes, 20] = None


@dataclass
class RequestMessage:
    piece_index: int
    block_offset: int
    size: int


@dataclass
class BitfieldMessage:
    bit_field: List[bool]


@dataclass
class HaveMessage:
    index: int


@dataclass
class ChokeMessage:
    pass


@dataclass
class UnchokeMessage:
    pass


@dataclass
class InterestedMessage:
    pass


@dataclass
class NotInterestedMessage:
    pass
