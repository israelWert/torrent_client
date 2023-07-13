import asyncio
import logging
from abc import ABC, abstractmethod

from torrent_client.peer.exceptions import PeerReturnInvalidResponseError, NoPieceNeededError, ChokedWhileRequestingError
from torrent_client.peer.p2p_messages_handling.message_id import MessageID
from torrent_client.peer.p2p_messages_handling.p2p_messages import HandshakeMessage, Response, BitfieldMessage, InterestedMessage, \
    HaveMessage, PieceMessage, NotInterestedMessage
from torrent_client.peer.downloading.peer_bridge import PeerBridge
from torrent_client.peer.downloading.downloading_manager import AbstractDownloadingManager, DownloadingManager
from torrent_client.peer.downloading.piece_request import AbstractPieceDownloader
from torrent_client.peer.p2p_net.p2p_socket import AbstractP2PSocket, P2PSocket

logger = logging.getLogger(__name__)

SLEEP_TIME_SEC = 0.01


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
                 downloading_manager: AbstractDownloadingManager = None,
                 p2p_socket: AbstractP2PSocket = None
                 ):
        self._info_hash = info_hash
        self._peer_id = peer_id.encode()
        self._choked = True
        self._downloading_manager = downloading_manager if downloading_manager \
            else DownloadingManager(bitfield_size, downloader)
        self._p2p_socket = p2p_socket if p2p_socket else P2PSocket(ip, port, bitfield_size)
        self._interested = False

    async def download(self) -> None:
        logger.info("connecting to new peer")
        async with self._p2p_socket:
            logger.debug("connection was established")
            await self._send_and_recv_handshake()
            logger.info("peer handshake stage was completed")
            logger.info("start downloading session")
            await self._wait_and_save_pieces()

    async def _send_and_recv_handshake(self) -> None:
        message = HandshakeMessage(
            info_hash=self._info_hash,
            peer_id=self._peer_id,
        )
        await self._p2p_socket.send(message, MessageID.Handshake)
        response = await self._p2p_socket.read_handshake()
        self._check_handshake_info_hash(response)

    async def _wait_and_save_pieces(self) -> None:
        await self._listen_until_can_request_piece()
        while not self._downloading_manager.is_end_downloading():
            try:
                await self._get_and_save_piece()
            except (NoPieceNeededError, ChokedWhileRequestingError):
                await self._listen_until_can_request_piece()

    async def _listen_until_can_request_piece(self) -> None:
        async for response in self._p2p_socket:
            logger.debug("new response")
            self._check_and_use_regular_responses(response)
            await self._update_interested_state()
            if (not self._choked) and self._interested:
                logger.debug("peer can request pieces")
                return

    async def _get_and_save_piece(self) -> None:
        with self._downloading_manager.create_piece_downloader() as piece_downloader:
            logger.info("downloading was assigned to peer")
            await asyncio.gather(
                self._request_piece(piece_downloader), self._recv_piece_from_peer(piece_downloader)
            )
        logger.info("we downloaded the full downloading")

    async def _recv_piece_from_peer(self, piece_downloader: AbstractPieceDownloader) -> None:
        logger.info("start receiving blocks")
        async for response in self._p2p_socket:
            self._check_and_use_regular_responses(response)
            self._add_piece_if_needed(piece_downloader, response)
            if self._choked:
                raise ChokedWhileRequestingError()
            if piece_downloader.is_piece_complete():
                return

    async def _request_piece(self, piece_downloader: AbstractPieceDownloader) -> None:
        logger.info("start sending block requests")
        for message in piece_downloader:
            await self._p2p_socket.send(message, MessageID.Request)
            logger.debug(f"we sent block request to peer: {message}")
            await asyncio.sleep(SLEEP_TIME_SEC)
        logger.info("all block requests were send")

    def _check_handshake_info_hash(self, response: Response) -> None:
        message: HandshakeMessage = response.message
        if not message.info_hash == self._info_hash:
            raise PeerReturnInvalidResponseError("peer return hand shake with wrong info_hash")

    def _check_and_use_regular_responses(self, response: Response) -> None:
        logger.debug(f"we got new response {response}")
        if response.id == MessageID.Unchoke:
            self._choked = False
        elif response.id == MessageID.Choke:
            self._choked = True
        elif response.id == MessageID.Have:
            message: HaveMessage = response.message
            self._downloading_manager.notify_new_piece(message.index)
        elif response.id == MessageID.Bitfiled:
            message: BitfieldMessage = response.message
            self._downloading_manager.set_bitfiled(message.bit_field)
            logger.info("we got bitfield")

    @staticmethod
    def _add_piece_if_needed(piece_downloader: AbstractPieceDownloader, response: Response) -> None:
        if response.id == MessageID.Piece:
            logger.debug("new block was added")
            message: PieceMessage = response.message
            piece_downloader.add_block(message.block, message.index)

    async def _update_interested_state(self) -> None:
        logger.debug((not self._interested) and self._downloading_manager.has_available_piece())
        if (not self._interested) and self._downloading_manager.has_available_piece():
            logger.debug("sending interested")
            await self._make_interested()
        elif self._interested and (not self._downloading_manager.has_available_piece()):
            logger.debug("sending interested")
            await self._make_not_interested()

    async def _make_interested(self) -> None:
        await self._p2p_socket.send(InterestedMessage(), MessageID.Interested)
        self._interested = True

    async def _make_not_interested(self) -> None:
        await self._p2p_socket.send(NotInterestedMessage, MessageID.NotInterested)
        self._interested = False


