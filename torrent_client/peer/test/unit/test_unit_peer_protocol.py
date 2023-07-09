from typing import Any

from torrent_client.peer.message_id import MessageID
from torrent_client.peer.messages.messages_data import HandshakeMessage, ChokeMessage, UnchokeMessage, InterestedMessage, \
    NotInterestedMessage, PieceMessage, BitfieldMessage, HaveMessage
from torrent_client.peer.peer_net.peer_protocol import PeerProtocol


def check_message(message: Any, id_: MessageID, peer_protocol: PeerProtocol):
    encode_message = peer_protocol.encode(message, id_)
    assert type(encode_message) == bytes
    decode_response = peer_protocol.decode_response_not_handshake(encode_message)
    assert decode_response.id == id_
    assert decode_response.message == message


class TestUnitPeerProtocol:
    def test_handshake(self):
        peer_protocol = PeerProtocol(0)
        message = HandshakeMessage(info_hash=bytes(20), peer_id=bytes(20))
        encoded_message = peer_protocol.encode(message, MessageID.Handshake)
        assert type(encoded_message) == bytes
        assert len(encoded_message) == peer_protocol.handshake_size
        response_message = peer_protocol.decode_handshake(encoded_message)
        decode_message: HandshakeMessage = response_message.message
        assert decode_message == message

    def test_empty_messages(self):
        peer_protocol = PeerProtocol(0)
        empty_messages = [ChokeMessage, UnchokeMessage, InterestedMessage, NotInterestedMessage]
        empty_messages_ids = [MessageID.Choke, MessageID.Unchoke, MessageID.Interested, MessageID.NotInterested]
        for message_type, id_ in zip(empty_messages, empty_messages_ids):
            message = message_type()
            check_message(message, id_, peer_protocol)

    def test_piece_messages(self):
        peer_protocol = PeerProtocol(0)
        message = PieceMessage(1, 2, b"asd")
        check_message(message, MessageID.Piece, peer_protocol)

    def test_bitfiled(self):
        peer_protocol = PeerProtocol(10)
        message = BitfieldMessage([True, False]*5)
        check_message(message, MessageID.Bitfiled, peer_protocol)

    def test_have(self):
        peer_protocol = PeerProtocol(0)
        message = HaveMessage(5)
        check_message(message, MessageID.Have, peer_protocol)
