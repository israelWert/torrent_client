from typing import Any

from torrent_client.peer.p2p_messages_handling.message_id import MessageID
from torrent_client.peer.p2p_messages_handling.p2p_messages import HandshakeMessage, ChokeMessage, UnchokeMessage, InterestedMessage, \
    NotInterestedMessage, PieceMessage, BitfieldMessage, HaveMessage
from torrent_client.peer.p2p_messages_handling.p2p_codec import P2PCodec


def check_message(message: Any, id_: MessageID, p2p_codec: P2PCodec):
    encode_message = p2p_codec.encode(message, id_)
    assert type(encode_message) == bytes
    decode_response = p2p_codec.decode_response_not_handshake(encode_message)
    assert decode_response.id == id_
    assert decode_response.message == message


class TestUnitP2PCodec:
    def test_handshake(self):
        peer_protocol = P2PCodec(0)
        message = HandshakeMessage(info_hash=bytes(20), peer_id=bytes(20))
        encoded_message = peer_protocol.encode(message, MessageID.Handshake)
        assert type(encoded_message) == bytes
        assert len(encoded_message) == peer_protocol.handshake_size
        response_message = peer_protocol.decode_handshake(encoded_message)
        decode_message: HandshakeMessage = response_message.message
        assert decode_message == message

    def test_empty_messages(self):
        peer_protocol = P2PCodec(0)
        empty_messages = [ChokeMessage, UnchokeMessage, InterestedMessage, NotInterestedMessage]
        empty_messages_ids = [MessageID.Choke, MessageID.Unchoke, MessageID.Interested, MessageID.NotInterested]
        for message_type, id_ in zip(empty_messages, empty_messages_ids):
            message = message_type()
            check_message(message, id_, peer_protocol)

    def test_piece_messages(self):
        peer_protocol = P2PCodec(0)
        message = PieceMessage(1, 2, b"asd")
        check_message(message, MessageID.Piece, peer_protocol)

    def test_bitfiled(self):
        peer_protocol = P2PCodec(10)
        message = BitfieldMessage([True, False]*5)
        check_message(message, MessageID.Bitfiled, peer_protocol)

    def test_have(self):
        peer_protocol = P2PCodec(0)
        message = HaveMessage(5)
        check_message(message, MessageID.Have, peer_protocol)
