import asyncio
from typing import Any

import pytest

from torrent_client.constants import BLOCK_SIZE
from torrent_client.peer.exceptions import PeerTimeOutError
from torrent_client.peer.p2p_net.p2p_socket import P2PSocket
from torrent_client.peer.test.fakes.fake_clock import FakeClock
from torrent_client.peer.test.fakes.fake_p2p_codec import FakeP2PCodec
from torrent_client.peer.test.fakes.fake_tcp_client import FakeTcpClient
from torrent_client.torrent_file.file import File

SOME_STRING = "data"


def insert_message(client: FakeTcpClient,
                   p2p_codec: FakeP2PCodec,
                   length: int,
                   length_bit_size: int = 0):
    p2p_codec.length_response = length
    p2p_codec._length_bit_size = length_bit_size
    data = bytes(length + length_bit_size)
    client.data = data
    p2p_codec.decode_response = SOME_STRING
    return data


class TestUnitP2PSocket:
    @pytest.fixture
    def socket_init(self):
        client, p2p_codec, clock = FakeTcpClient(), FakeP2PCodec(), FakeClock()
        return P2PSocket(None, None, None, client, p2p_codec, clock), client, p2p_codec, clock

    @pytest.mark.asyncio
    async def test_read_in_one_response(self, socket_init):
        generator, client, p2p_codec, clock = socket_init
        length = 5
        client.response_size = 5
        full_message = insert_message(client, p2p_codec, length)
        response = await generator.read_handshake()
        assert SOME_STRING == response
        assert len(p2p_codec.decode_received) == length
        assert p2p_codec.decode_received == full_message

    @pytest.mark.asyncio
    async def test_read_in_multi_response(self, socket_init):
        generator, client, p2p_codec, clock = socket_init
        length = 5
        client.response_size = 1
        full_message = insert_message(client, p2p_codec, length)
        response = await generator.read_handshake()
        assert SOME_STRING == response
        assert len(p2p_codec.decode_received) == length
        assert p2p_codec.decode_received == full_message

    @pytest.mark.asyncio
    async def test_read_one_block(self, socket_init):
        generator, client, p2p_codec, clock = socket_init
        full_pack = insert_message(client, p2p_codec, 5, 4)
        response = await generator.read()
        assert SOME_STRING == response
        assert full_pack == p2p_codec.decode_received
        assert p2p_codec.length_received == full_pack[:p2p_codec.length_datatype_size]

    @pytest.mark.asyncio
    async def test_read_multi_blocks_at_once(self, socket_init):
        generator, client, p2p_codec, clock = socket_init
        full_pack = insert_message(client, p2p_codec, BLOCK_SIZE*3, 4)
        response = await generator.read()
        assert SOME_STRING == response
        assert full_pack == p2p_codec.decode_received
        assert p2p_codec.length_received == full_pack[:p2p_codec.length_datatype_size]

    @pytest.mark.asyncio
    async def test_read_multi_messages(self, socket_init):
        generator, client, p2p_codec, clock = socket_init
        pack_1 = insert_message(client, p2p_codec, 1, 4)
        client.data += pack_1
        for i in range(2):
            response = await generator.read()
            assert SOME_STRING == response
            assert pack_1 == p2p_codec.decode_received
            assert p2p_codec.length_received == pack_1[:p2p_codec.length_datatype_size]

    @pytest.mark.asyncio
    async def test_no_response_raise(self, socket_init):
        generator, client, p2p_codec, clock = socket_init
        clock.timeout = 3
        with pytest.raises(PeerTimeOutError):
            await generator.read()
