import struct

from torrent_client.peer.p2p_messages_handling.message_factory import MessageFactory
from torrent_client.peer.p2p_messages_handling.p2p_messages import PieceMessage


class PieceMessageFactory(MessageFactory[PieceMessage]):
    def decode(self, data: bytes):
        length = len(data)
        data_in_tuple = struct.unpack(f"II{length - 8}s", data)
        return PieceMessage(*data_in_tuple)

    def encode(self, obj: PieceMessage) -> bytes:
        return struct.pack(f"II{len(obj.block)}s", obj.index, obj.begin, obj.block)
