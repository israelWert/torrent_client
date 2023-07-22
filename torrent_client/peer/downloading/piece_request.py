from abc import abstractmethod, ABC
from typing import List, Iterable
from hashlib import sha1

from torrent_client.constants import BLOCK_SIZE
from torrent_client.peer.exceptions import CorruptedPieceError, NoPieceNeededError
from torrent_client.peer.p2p_messages_handling.p2p_messages import RequestMessage
from torrent_client.peer.downloading.peer_bridge import PeerBridge


class AbstractPieceDownloader(ABC):
    @abstractmethod
    def __enter__(self) -> "AbstractPieceDownloader":
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def __iter__(self) -> Iterable[RequestMessage]:
        pass

    @abstractmethod
    def is_piece_complete(self) -> bool:
        pass

    @abstractmethod
    def add_block(self, block: bytes, index: int):
        pass


class PieceDownloader(AbstractPieceDownloader):
    def __init__(self,
                 downloader: PeerBridge,
                 bit_filed: List[bool],
                 ):
        self._downloader = downloader
        self._bit_filed = bit_filed
        self._buffer = b""

    def __enter__(self):
        for piece_index in self._downloader.get_needed_pieces_indexes():
            if not self._bit_filed[piece_index]:
                continue
            self._piece_info = self._downloader.occupy_piece(piece_index)
            break
        else:
            raise NoPieceNeededError()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, Exception):
            self._downloader.unlock_piece(self._piece_info.index)
        else:
            self._check_piece_hash()
            self._downloader.store_piece(self._buffer, self._piece_info.index)
            self._downloader.unlock_piece(self._piece_info.index)

    def _is_hash_valid(self):
        buffer_hash = sha1(self._buffer).digest()
        return buffer_hash == self._piece_info.piece_hash

    def _check_piece_hash(self):
        if not self._is_hash_valid():
            self._downloader.unlock_piece(self._piece_info.index)
            raise CorruptedPieceError()

    def is_piece_complete(self):
        return self._buffer == self._piece_info.piece_length

    def add_block(self, block: bytes, index: int):
        if self._piece_info.index != index:
            raise
        self._buffer += block

    def _iter(self) -> Iterable[RequestMessage]:
        for offset in range(0, self._piece_info.piece_length, BLOCK_SIZE):
            yield RequestMessage(
                self._piece_info.index,
                offset,
                BLOCK_SIZE
            )

    def __iter__(self) -> Iterable[RequestMessage]:
        return self._iter()
