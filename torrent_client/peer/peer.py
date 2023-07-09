import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

from torrent_client.peer.exceptions import PeerReturnInvalidResponseError, PeerUnexpectedBehaviorError, \
    NoPieceNeededError, ChokedWhileRequestingError
from torrent_client.peer.message_id import MessageID
from torrent_client.peer.messages.messages_data import HandshakeMessage, Response, BitfieldMessage, InterestedMessage, \
    HaveMessage, PieceMessage
from torrent_client.peer.piece.peer_bridge import PeerBridge
from torrent_client.peer.piece.piece_manager import AbstractPieceManager, PieceManager
from torrent_client.peer.piece.piece_request_state import AbstractPieceRequestState
from torrent_client.peer.peer_net.peer_net import PeerNet, AbstractPeerNet

logger = logging.getLogger(__name__)

SLEEP_TIME_SEC = 0.01
TIMEOUT_SEC = 7


class AbstractPeer(ABC):

    @abstractmethod
    async def download(self) -> None:
        pass


class Peer(AbstractPeer):
    def __init__(self,
                 ip: str,
                 port: int,
                 info_hash: bytes,
                 bitfield_size: int,
                 peer_id: str,
                 downloader: PeerBridge,
                 piece_manager: AbstractPieceManager,
                 peer_net: AbstractPeerNet = None
                 ):
        self._info_hash = info_hash
        self._peer_id = peer_id.encode()
        self._choked = True
        self._main_task: Optional[asyncio.Task] = None
        self._piece_manager = piece_manager if piece_manager else PieceManager(bitfield_size, downloader)
        self._peer_net = peer_net if peer_net else PeerNet(ip, port, bitfield_size)

    async def download(self) -> None:
        await self._start_conversation()
        logger.info("we have started conversation")
        await self._handle_conversation()

    async def _handle_conversation(self):
        await self._listen_until_can_request_piece()
        logger.info(self._piece_manager.is_end_downloading())
        while not self._piece_manager.is_end_downloading():
            try:
                await self._request_and_recv_piece()
            except (NoPieceNeededError, ChokedWhileRequestingError):
                await self._listen_until_can_request_piece()

    async def _start_conversation(self) -> None:
        await self._send_and_recv_handshake()
        logger.info("we got hand shake")
        await self._wait_for_bit_filed()
        logger.info("we got bitfield")
        await self._peer_net.send(InterestedMessage(), MessageID.Interested)

    def _check_handshake_info_hash(self, response: Response):
        message: HandshakeMessage = response.message
        if not message.info_hash == self._info_hash:
            raise PeerReturnInvalidResponseError("peer return hand shake with wrong info_hash")

    async def _send_and_recv_handshake(self) -> None:
        message = HandshakeMessage(
            info_hash=self._info_hash,
            peer_id=self._peer_id,
        )
        await self._peer_net.send(message, MessageID.Handshake)
        response = await self._peer_net.read_handshake()
        self._check_handshake_info_hash(response)

    async def _wait_for_bit_filed(self) -> None:
        response = await self._peer_net.read()
        if response.id == MessageID.Bitfiled:
            message: BitfieldMessage = response.message
            self._piece_manager.set_bitfiled(message.bit_field)
        else:
            logger.error(f"peer didn't send bitfiled after handshake he send {response.id}")
            raise PeerUnexpectedBehaviorError(f"peer didn't send bitfiled after handshake he send {response.id}")

    def _update_peer_by_response(self, response):
        if response.id == MessageID.Unchoke:
            self._choked = False
        elif response.id == MessageID.Choke:
            self._choked = True
        elif response.id == MessageID.Have:
            message: HaveMessage = response.message
            self._piece_manager.notify_new_piece(message.index)
        elif response.id == MessageID.Bitfiled:
            raise PeerUnexpectedBehaviorError("peer send bitField after more then 3 seconds")

    @staticmethod
    def _add_piece_if_needed(request_state: AbstractPieceRequestState, response: Response):
        if response.id == MessageID.Piece:
            logger.debug(f"we got piece black from peer {response}")
            message: PieceMessage = response.message
            request_state.add_block(message.block, message.index)

    async def _listen_until_can_request_piece(self):
        logger.info(self._peer_net)
        async for response in self._peer_net:
            self._update_peer_by_response(response)
            if (not self._choked) and self._piece_manager.is_have_available_piece():
                logger.info("peer can request pieces")
                return

    async def _recv_piece_from_peer(self, request_state: AbstractPieceRequestState):
        async for response in self._peer_net:
            self._update_peer_by_response(response)
            if self._choked:
                raise ChokedWhileRequestingError()
            self._add_piece_if_needed(request_state, response)
            if request_state.is_piece_complete():
                return

    async def _request_piece(self, request_state: AbstractPieceRequestState):
        logger.debug("start sending requests")
        logger.info(request_state)
        logger.info(f"the requests :{request_state.__iter__()}")
        for message in request_state:
            await self._peer_net.send(message, MessageID.Request)
            logger.debug(f"we sent piece block to peer: {message}")
            await asyncio.sleep(SLEEP_TIME_SEC)

    async def _request_and_recv_piece(self):
        with self._piece_manager.create_piece_request() as request_state:
            logger.info("start downloading from piece")
            await asyncio.gather(
                self._request_piece(request_state), self._recv_piece_from_peer(request_state)
            )
