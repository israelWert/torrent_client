import asyncio
from typing import Any

import pytest

from torrent_client.constants import BLOCK_SIZE
from torrent_client.peer.exceptions import PeerTimeOutError
from torrent_client.peer.peer_net.peer_net import PeerNet
from torrent_client.peer.test.fakes.fake_clock import FakeClock
from torrent_client.peer.test.fakes.fake_peer_protocol import FakePeerProtocol
from torrent_client.peer.test.fakes.fake_tcp_client import FakeTcpClient
from torrent_client.torrent_file.file import File

SOME_STRING = "data"


def insert_message(client: FakeTcpClient,
                   protocol: FakePeerProtocol,
                   length: int,
                   length_bit_size: int = 0):
    protocol.length_response = length
    protocol._length_bit_size = length_bit_size
    data = bytes(length + length_bit_size)
    client.data = data
    protocol.decode_response = SOME_STRING
    return data


class TestUnitPeerNet:
    @pytest.fixture
    def generator_init(self):
        client, protocol, clock = FakeTcpClient(), FakePeerProtocol(), FakeClock()
        return PeerNet(None, None, None, client, protocol, clock), client, protocol, clock

    @pytest.mark.asyncio
    async def test_read_handshake(self, generator_init):
        generator, client, protocol, clock = generator_init
        length = 5
        full_message = insert_message(client, protocol, length)
        response = await generator.read_handshake()
        assert SOME_STRING == response
        assert len(protocol.decode_received) == length
        assert protocol.decode_received == full_message

    @pytest.mark.asyncio
    async def test_read_one_block(self, generator_init):
        generator, client, protocol, clock = generator_init
        full_pack = insert_message(client, protocol, 5, 4)
        response = await generator.read()
        assert SOME_STRING == response
        assert full_pack == protocol.decode_received
        assert protocol.length_received == full_pack[:protocol.length_byte_size]

    @pytest.mark.asyncio
    async def test_read_multi_blocks_at_once(self, generator_init):
        generator, client, protocol, clock = generator_init
        full_pack = insert_message(client, protocol, BLOCK_SIZE*3, 4)
        response = await generator.read()
        assert SOME_STRING == response
        assert full_pack == protocol.decode_received
        assert protocol.length_received == full_pack[:protocol.length_byte_size]

    @pytest.mark.asyncio
    async def test_read_multi_messages(self, generator_init):
        generator, client, protocol, clock = generator_init
        pack_1 = insert_message(client, protocol, 1, 4)
        client.data += pack_1
        for i in range(2):
            response = await generator.read()
            assert SOME_STRING == response
            assert pack_1 == protocol.decode_received
            assert protocol.length_received == pack_1[:protocol.length_byte_size]

    @pytest.mark.asyncio
    async def test_no_response_raise(self, generator_init):
        generator, client, protocol, clock = generator_init
        clock.timeout = 3
        with pytest.raises(PeerTimeOutError):
            await generator.read()
