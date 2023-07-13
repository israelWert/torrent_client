import logging
from abc import ABC, abstractmethod
from typing import Callable, Any

from torrent_client.constants import BLOCK_SIZE
from torrent_client.peer.p2p_net.clock import AbstractClock, Clock
from torrent_client.peer.p2p_messages_handling.message_id import MessageID
from torrent_client.peer.p2p_messages_handling.p2p_messages import Response
from torrent_client.peer.p2p_messages_handling.p2p_codec import AbstractP2PCodec, P2PCodec
from torrent_client.peer.p2p_net.tcp_client import TcpClient, AbstractTcpClient

logger = logging.getLogger(__name__)

WAIT_SECONDS_UNTIL_TIMEOUT = 3
SLEEP_PERIOD = 0.01


class AbstractP2PSocket(ABC):
    def __aiter__(self) -> "AbstractP2PSocket":
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

    @abstractmethod
    async def __aenter__(self) -> None:
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class P2PSocket(AbstractP2PSocket):

    def __init__(self,
                 ip: str,
                 port: int,
                 bitfiled_size: int,
                 client: AbstractTcpClient = None,
                 protocol: AbstractP2PCodec = None,
                 clock: AbstractClock = None
                 ):
        self._client = client if client else TcpClient(ip, port)
        self._protocol = protocol if protocol else P2PCodec(bitfiled_size)
        self._buff = b""
        self._clock = clock if clock else Clock()
        self._clock.set_timeout(WAIT_SECONDS_UNTIL_TIMEOUT)

    async def __aenter__(self) -> None:
        await self._client.init()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._client.close()

    def _remove_from_buffer(self, size: int) -> None:
        logger.debug(f"removing data from buffer size {size}")
        self._buff = self._buff[size:]

    def _get_from_buffer(self, size: int) -> bytes:
        logger.debug(f"getting from buffer data size: {size}")
        return self._buff[:size]

    def _is_hand_shake_full(self) -> bool:
        return len(self._buff) >= self._protocol.handshake_size

    async def _wait_for_handshake(self) -> None:
        await self._recv_until_condition(self._is_hand_shake_full)

    async def _read_from_peer(self) -> None:
        packet = await self._client.recv(BLOCK_SIZE)
        if len(packet) > 0:
            logger.debug(f"we got new data {packet}")
        self._buff += packet

    async def _recv_until_condition(self, condition: Callable[[], bool]) -> None:
        self._clock.reset()
        await self._read_from_peer()
        while not condition():
            await self._clock.sleep(SLEEP_PERIOD)
            await self._read_from_peer()

    def _is_response_containing_length(self) -> bool:
        return len(self._buff) >= self._protocol.length_datatype_size

    async def _wait_until_recv_length(self) -> int:
        await self._recv_until_condition(
            self._is_response_containing_length
        )
        return self._protocol.decode_response_length(self._get_from_buffer(self._protocol.length_datatype_size))

    async def _get_response_with_length_not_zero(self) -> int:
        while True:
            length = await self._wait_until_recv_length()
            if length != 0:
                return length
            self._remove_from_buffer(self._protocol.length_datatype_size)

    def _is_response_size_length(self, length):
        return len(self._buff) >= (length + self._protocol.length_datatype_size)

    async def _recv_buffer_size_length(self, length: int) -> None:
        await self._recv_until_condition(
            lambda: self._is_response_size_length(length)
        )

    async def _recv_response_return_size(self) -> int:
        length = await self._get_response_with_length_not_zero()
        await self._recv_buffer_size_length(length)
        return length

    async def read_handshake(self) -> Response:
        logger.debug("waiting for handshake response")
        await self._wait_for_handshake()
        logger.info("we got and shake response")
        hand_shake = self._get_from_buffer(self._protocol.handshake_size)
        self._remove_from_buffer(self._protocol.handshake_size)
        decoded_hand_shake = self._protocol.decode_handshake(hand_shake)
        logger.debug(f"hand shake data: [encoded: {hand_shake}, decoded: {decoded_hand_shake}]")
        return decoded_hand_shake

    async def __anext__(self) -> Response:
        return await self.read()

    async def read(self) -> Response:
        logger.info("waiting for readable response")
        response_length = await self._recv_response_return_size()
        full_response_length = response_length + self._protocol.length_datatype_size
        response_bytes = self._get_from_buffer(full_response_length)
        response = self._protocol.decode_response_not_handshake(response_bytes)
        self._remove_from_buffer(full_response_length)
        logger.debug(f"we got new response encoded: {response_bytes}, decoded: {response}")
        return response

    async def send(self, message: Any, message_id: MessageID) -> None:
        message_encoded = self._protocol.encode(message, message_id)
        logger.debug(f"we are sending message decoded{message}, encoded {message_encoded}")
        await self._client.send(message_encoded)
