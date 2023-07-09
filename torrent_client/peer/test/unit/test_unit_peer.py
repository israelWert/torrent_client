import asyncio
from typing import Any, List, Optional

import pytest

from torrent_client.peer.exceptions import PeerUnexpectedBehaviorError, PeerReturnInvalidResponseError
from torrent_client.peer.message_id import MessageID
from torrent_client.peer.messages.messages_data import HandshakeMessage, InterestedMessage, BitfieldMessage, Response, \
    UnchokeMessage, RequestMessage, PieceMessage
from torrent_client.peer.peer import Peer
from torrent_client.peer.test.fakes.fake_peer_net import FakePeerNet
from torrent_client.peer.test.fakes.fake_piece_manager import FakePieceManager
from torrent_client.peer.test.fakes.fake_piece_request_state import FakePieceRequestState
from torrent_client import log_config
MessageAndResponse = tuple[Optional[Any], Optional[Response]]


def create_peer(info_hash: bytes, peer_id: str) -> tuple[Peer, FakePeerNet, FakePieceManager]:
    peer_net = FakePeerNet()
    piece_manager = FakePieceManager()
    peer = Peer(
        ip=None,
        port=None,
        bitfield_size=None,
        info_hash=info_hash,
        peer_id=peer_id,
        downloader=None,
        piece_manager=piece_manager,
        peer_net=peer_net
    )
    return peer, peer_net, piece_manager


async def check_conversion(peer_net: FakePeerNet, conversion_messages: List[MessageAndResponse]):
    for send, recv in conversion_messages:
        if send:
            await asyncio.sleep(0.1)
            assert peer_net.sent_message == send
        if recv:
            peer_net.next_response = recv
            await asyncio.sleep(0.1)


async def start_communication_test(peer_net: FakePeerNet,
                                   piece_manager: FakePieceManager,
                                   info_hash: bytes,
                                   peer_id: str,
                                   bit_filed: List
                                   ):
    await check_conversion(
        peer_net,
        [
            (
                HandshakeMessage(info_hash=info_hash, peer_id=peer_id.encode()),
                Response(MessageID.Handshake, 1, HandshakeMessage(info_hash=info_hash))
            ),
            (
                None,
                Response(MessageID.Bitfiled, 1, BitfieldMessage(bit_filed))
            ),
            (
                InterestedMessage(),
                None
            )
        ]
    )
    assert piece_manager.bit_field_response == bit_filed


async def get_piece_test(peer_net: FakePeerNet, piece_manager: FakePieceManager):
    piece_manager.request_state = FakePieceRequestState()
    num_of_blocks = 1
    piece_requests = [RequestMessage(0, i, 0) for i in range(num_of_blocks)]
    piece_manager.request_state.requests = piece_requests

    await check_conversion(
        peer_net,
        [(None, Response(MessageID.Unchoke, 1, UnchokeMessage()))]
    )
    await asyncio.sleep(2)
    await check_conversion(
        peer_net,
        [
            (request, Response(MessageID.Piece, 1, PieceMessage(0, 0, bytes()))) for request in piece_requests
        ]
    )


class TestUnitPeer:
    @pytest.mark.asyncio
    async def test_peer_wrong_info_hash(self):
        info_hash, peer_id = b"test info" + bytes(11), "test id"
        wrong_info_hash = bytes(20)
        peer, peer_net, piece_manager = create_peer(info_hash, peer_id)
        peer_task = asyncio.create_task(peer.download())
        await check_conversion(
            peer_net,
            [
                (None, Response(MessageID.Handshake, 1, HandshakeMessage(info_hash=wrong_info_hash)))
            ]
        )
        with pytest.raises(PeerReturnInvalidResponseError):
            raise peer_task.exception()

    @pytest.mark.asyncio
    async def test_peer_late_bitfiled(self):
        info_hash, peer_id = bytes(20), "test id"
        peer, peer_net, piece_manager = create_peer(info_hash, peer_id)
        peer_task = asyncio.create_task(peer.download())
        await check_conversion(
            peer_net,
            [
                (
                    None,
                    Response(MessageID.Handshake, 1, HandshakeMessage(info_hash=bytes(20)))
                ),
                (
                    None,
                    Response(MessageID.Unchoke, None, None)
                )
            ]
        )
        with pytest.raises(PeerUnexpectedBehaviorError):
            raise peer_task.exception()

    @pytest.mark.asyncio
    async def test_standard_conversion(self):
        info_hash, peer_id = b"test info" + bytes(11), "test id"
        bit_filed = [True, False, False]
        peer, peer_net, piece_manager = create_peer(info_hash, peer_id)
        peer_task = asyncio.create_task(peer.download())
        await start_communication_test(peer_net, piece_manager, info_hash, peer_id, bit_filed)
        await get_piece_test(peer_net, piece_manager)
        peer_task.cancel()
