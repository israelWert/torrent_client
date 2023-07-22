from abc import ABC, abstractmethod
from typing import List

from torrent_client.download.exceptions import PieceAllReadyOccupiedError, UnoccupiedPieceError
from torrent_client.download.file_loading.load_request import LoadRequest
from torrent_client.download.part import Part
from torrent_client.peer.downloading.piece_bitfield_info import PieceBitfieldInfo


class AbstractPiece(ABC):
    @abstractmethod
    def is_available_to_download(self) -> bool:
        pass

    @abstractmethod
    def occupy(self) -> PieceBitfieldInfo:
        pass

    @abstractmethod
    def release(self) -> None:
        pass

    @abstractmethod
    async def download(self, data: bytes) -> None:
        pass

    @abstractmethod
    def get_size(self) -> int:
        pass

    @abstractmethod
    def is_downloaded(self) -> bool:
        pass


class Piece(AbstractPiece):
    def __init__(self, parts: List[Part], index: int, hash_: bytes):
        self._index = index
        self._hash = hash_
        self._size = sum(part.size for part in parts)
        self._occupied = False
        self._downloaded = False
        self._parts = parts

    def release(self) -> None:
        if not self._occupied:
            raise UnoccupiedPieceError()
        self._occupied = False


    async def _download(self, data: bytes) -> None:
        data_all_ready_requested = 0
        for part in self._parts:
            part_start_in_data, part_end_in_data = data_all_ready_requested,  part.size+data_all_ready_requested
            request_to_load = LoadRequest(part.beginning, data[part_start_in_data: part_end_in_data], part.size)
            await part.file.add_load_request(request_to_load)
            data_all_ready_requested += part.size

    async def download(self, data: bytes):
        self._downloaded = True
        await self._download(data)


    def is_available_to_download(self) -> bool:
        return (not self._occupied) and (not self._downloaded)

    def occupy(self) -> PieceBitfieldInfo:
        if self._occupied:
            raise PieceAllReadyOccupiedError()
        self._occupied = True
        return PieceBitfieldInfo(self._index, self._size, self._hash)


    def get_size(self) -> int:
        return self._size

    def is_downloaded(self) -> bool:
        return self._downloaded
