from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable, Any

from torrent_client.constants import BLOCK_SIZE
from torrent_client.peer.clock import AbstractClock, Clock
from torrent_client.peer.message_id import MessageID
from torrent_client.peer.messages.messages_data import Response
from torrent_client.peer.peer_net.peer_protocol import AbstractPeerProtocol, PeerProtocol

from torrent_client.peer.peer_net.tcp_client import AbstractTcpClient, TcpClient

WAIT_SECONDS_UNTIL_TIMEOUT = 3
SLEEP_PERIOD = 0.01


class AbstractPeerNet(ABC):
    def __aiter__(self) -> "AbstractPeerNet":
        return self

    @abstractmethod
    def __anext__(self) -> Response:
        pass

    @abstractmethod
    async def read(self) -> Response:
        pass

    @abstractmethod
    async def read_handshake(self) -> Response:
        pass

    @abstractmethod
    async def send(self, message: Any, message_id: MessageID) -> None:
        pass


class PeerNet(AbstractPeerNet):
    def __init__(self,
                 ip: str,
                 port: int,
                 bitfiled_size: int,
                 client: AbstractTcpClient = None,
                 protocol: AbstractPeerProtocol = None,
                 clock: AbstractClock = None
                 ):
        self._client = client if client else TcpClient(ip, port)
        self._protocol = protocol if protocol else PeerProtocol(bitfiled_size)
        self._buff = b""
        self._clock = clock if clock else Clock()
        self._clock.set_timeout(WAIT_SECONDS_UNTIL_TIMEOUT)

    def _remove_from_buffer(self, size: int):
        self._buff = self._buff[size:]

    def _get_from_buffer(self, size: int):
        return self._buff[:size]

    def _is_hand_shake_full(self):
        return len(self._buff) >= self._protocol.handshake_size

    async def _wait_for_handshake(self):
        await self._recv_until_condition(self._is_hand_shake_full)

    async def _read_from_peer(self):
        data = await self._client.recv(BLOCK_SIZE)
        self._buff += data

    async def _recv_until_condition(self, condition: Callable[[], bool]):
        await self._read_from_peer()
        while not condition():
            await self._clock.sleep(SLEEP_PERIOD)
            await self._read_from_peer()

    def _is_response_containing_length(self) -> bool:
        return len(self._buff) >= self._protocol.length_byte_size

    async def _wait_until_recv_length(self) -> int:
        await self._recv_until_condition(
            self._is_response_containing_length
        )
        return self._protocol.decode_response_length(self._get_from_buffer(self._protocol.length_byte_size))

    async def _get_response_with_length_not_zero(self) -> int:
        while True:
            length = await self._wait_until_recv_length()
            if length != 0:
                return length
            self._remove_from_buffer(self._protocol.length_byte_size)

    def _is_response_size_length(self, length):
        return len(self._buff) >= (length + self._protocol.length_byte_size)

    async def _recv_buffer_size_length(self, length: int):
        await self._recv_until_condition(
            lambda: self._is_response_size_length(length)
        )

    async def _recv_valid_response(self) -> int:
        length = await self._get_response_with_length_not_zero()
        await self._recv_buffer_size_length(length)
        return length

    async def read_handshake(self) -> Response:
        self._clock.reset()
        await self._wait_for_handshake()
        hand_shake = self._get_from_buffer(self._protocol.handshake_size)
        self._remove_from_buffer(self._protocol.handshake_size)
        return self._protocol.decode_handshake(hand_shake)

    async def __anext__(self) -> Response:
        return await self.read()

    async def read(self) -> Response:
        self._clock.reset()
        response_length = await self._recv_valid_response()
        response_bytes = self._get_from_buffer(response_length+self._protocol.length_byte_size)
        response = self._protocol.decode_response_not_handshake(response_bytes)
        self._remove_from_buffer(response_length + self._protocol.length_byte_size)
        return response

    async def send(self, message: Any, message_id: MessageID) -> None:
        message_encoded = self._protocol.encode(message, message_id)
        await self._client.send(message_encoded)
