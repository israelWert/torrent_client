import asyncio
from typing import Any, List, Optional, Tuple

import pytest

from torrent_client.peer.exceptions import PeerReturnInvalidResponseError
from torrent_client.peer.p2p_messages_handling.message_id import MessageID
from torrent_client.peer.p2p_messages_handling.p2p_messages import (
    HandshakeMessage, InterestedMessage, BitfieldMessage, Response,
    UnchokeMessage, RequestMessage, PieceMessage, HaveMessage
)
from torrent_client.peer.peer import Peer
from torrent_client.peer.test.fakes.fake_p2p_socket import FakeP2PSocket
from torrent_client.peer.test.fakes.fake_downloading_manager import FakeDownloadingManager
from torrent_client.peer.test.fakes.fake_piece_downloader import FakePieceDownloader

MessageAndResponse = Tuple[Optional[Any], Optional[Response]]


def create_peer(info_hash: bytes, peer_id: str) -> Tuple[Peer, FakeP2PSocket, FakeDownloadingManager]:
    p2p_socket = FakeP2PSocket()
    downloading_manager = FakeDownloadingManager()
    peer = Peer(
        ip=None,
        port=None,
        bitfield_size=None,
        info_hash=info_hash,
        peer_id=peer_id,
        downloader=None,
        downloading_manager=downloading_manager,
        p2p_socket=p2p_socket
    )
    return peer, p2p_socket, downloading_manager


async def wait_until_send_message(p2p_socket: FakeP2PSocket, task: asyncio.Task) -> None:
    while not p2p_socket.have_sent_new_message():
        await asyncio.sleep(0.01)
        if task.done():
            raise task.exception()


async def wait_until_read_response(p2p_socket: FakeP2PSocket, task: asyncio.Task) -> None:
    while not p2p_socket.is_read_response():
        await asyncio.sleep(0.01)
        if task.done():
            raise task.exception()


async def check_conversion(p2p_socket: FakeP2PSocket, task: asyncio.Task,
                           conversion_messages: List[MessageAndResponse]) -> None:
    for send, recv in conversion_messages:
        if send:
            await wait_until_send_message(p2p_socket, task)
            assert p2p_socket.sent_message == send
        if recv:
            p2p_socket.next_response = recv
            await wait_until_read_response(p2p_socket, task)


async def start_communication_with_bitfiled_test(
        p2p_socket: FakeP2PSocket,
        downloading_manager: FakeDownloadingManager,
        task: asyncio.Task,
        info_hash: bytes,
        peer_id: str,
        bit_field: List[bool]
) -> None:
    await check_conversion(
        p2p_socket,
        task,
        [
            (
                HandshakeMessage(info_hash=info_hash, peer_id=peer_id.encode()),
                Response(MessageID.Handshake, 1, HandshakeMessage(info_hash=info_hash))
            ),
            (
                None,
                Response(MessageID.Bitfiled, 1, BitfieldMessage(bit_field))
            ),
            (
                InterestedMessage(),
                None
            )
        ]
    )
    assert downloading_manager.bit_field_response == bit_field


async def get_piece_test(p2p_socket: FakeP2PSocket, downloading_manager: FakeDownloadingManager, task: asyncio.Task) -> None:
    downloading_manager.piece_downloader = FakePieceDownloader()
    num_of_blocks = 3
    piece_requests = [RequestMessage(0, i, 0) for i in range(num_of_blocks)]
    downloading_manager.piece_downloader.requests = piece_requests

    await check_conversion(
        p2p_socket,
        task,
        [(None, Response(MessageID.Unchoke, 1, UnchokeMessage()))]
    )
    await check_conversion(
        p2p_socket,
        task,
        [
            (request, Response(MessageID.Piece, 0, PieceMessage(0, 0, b""))) for request in piece_requests
        ]
    )


class TestUnitPeer:
    @pytest.mark.asyncio
    async def test_peer_wrong_info_hash(self) -> None:
        info_hash, peer_id = b"test info" + bytes(11), "test id"
        wrong_info_hash = bytes(20)
        peer, p2p_socket, downloading_manager = create_peer(info_hash, peer_id)
        peer_task = asyncio.create_task(peer.download())
        with pytest.raises(PeerReturnInvalidResponseError):
            await check_conversion(
                p2p_socket,
                peer_task,
                [
                    (None, Response(MessageID.Handshake, 1, HandshakeMessage(info_hash=wrong_info_hash)))
                ]
            )

    @pytest.mark.asyncio
    async def test_no_bitfield(self) -> None:
        info_hash, peer_id = bytes(20), "test id"
        peer, p2p_socket, downloading_manager = create_peer(info_hash, peer_id)
        peer_task = asyncio.create_task(peer.download())
        downloading_manager.is_have_available_piece_res = False
        await check_conversion(
            p2p_socket,
            peer_task,
            [
                (
                    None,
                    Response(MessageID.Handshake, 1, HandshakeMessage(info_hash=bytes(20)))
                ),
                (
                    None,
                    Response(MessageID.Unchoke, 1, UnchokeMessage())
                )
            ]
        )
        peer_task.cancel()
        await asyncio.sleep(0.01)

    @pytest.mark.asyncio
    async def test_no_piece_needed(self):
        info_hash, peer_id = bytes(20), "test id"
        peer, p2p_socket, downloading_manager = create_peer(info_hash, peer_id)
        peer_task = asyncio.create_task(peer.download())
        downloading_manager.is_have_available_piece_res = False
        await check_conversion(
            p2p_socket,
            peer_task,
            [
                (
                    HandshakeMessage(info_hash=info_hash, peer_id=peer_id.encode()),
                    Response(MessageID.Handshake, 1, HandshakeMessage(info_hash=bytes(20)))
                )
            ]
        )
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(wait_until_send_message(p2p_socket, peer_task), timeout=0.2)
        downloading_manager.is_have_available_piece_res = True
        await check_conversion(
            p2p_socket,
            peer_task,
            [
                (
                    None,
                    Response(MessageID.Have, 1, HaveMessage(2))
                ),
                (
                    InterestedMessage(),
                    None
                )
            ]
        )
        peer_task.cancel()
        await asyncio.sleep(0.01)

    @pytest.mark.asyncio
    async def test_download_with_bitfiled(self) -> None:
        info_hash, peer_id = b"test info" + bytes(11), "test id"
        bit_field = [True, False, False]
        peer, p2p_socket, downloading_manager = create_peer(info_hash, peer_id)
        peer_task = asyncio.create_task(peer.download())
        await start_communication_with_bitfiled_test(p2p_socket, downloading_manager, peer_task, info_hash, peer_id, bit_field)
        await get_piece_test(p2p_socket, downloading_manager, peer_task)
        peer_task.cancel()
        await asyncio.sleep(0.01)
