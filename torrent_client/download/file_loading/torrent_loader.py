import asyncio
from abc import abstractmethod, ABC
from typing import List, Optional

from torrent_client.download.file_loading.file_loader import FileLoader, AbstractFileLoader
from torrent_client.download.file_loading.os_wrapper import OsWrapper, AbstractOsWrapper
from torrent_client.download.part import Part
from torrent_client.torrent_file.file_to_download import FileToDownload

PieceInPart = List[Part]


class AbstractTorrentLoader(ABC):
    @abstractmethod
    async def listen_to_requests_and_download(self) -> None:
        pass

    @abstractmethod
    def get_files_parts_in_pieces(self, piece_default_size: int) -> List[PieceInPart]:
        pass


class TorrentLoader(AbstractTorrentLoader):
    def __init__(self,
                 files_info: Optional[List[FileToDownload]] = None,
                 os: Optional[AbstractOsWrapper] = None,
                 files_loaders: Optional[List[AbstractFileLoader]] = None):
        self._os = os if os else OsWrapper()
        self._files = files_loaders if files_loaders else \
            [FileLoader(file_info, self._os) for file_info in files_info]

    async def listen_to_requests_and_download(self) -> None:
        await asyncio.gather(
            *[file.listen_to_requests_and_download() for file in self._files]
        )

    def get_files_parts_in_pieces(self, piece_default_size: int) -> List[PieceInPart]:
        pieces_as_parts = []
        for pieces in self._file_part_gen(piece_default_size):
            pieces_as_parts.extend(pieces)
        return pieces_as_parts

    def _file_part_gen(self, piece_default_size: int):
        left_parts = []
        for file in self._files:
            file_parts = self._get_file_parts(file, left_parts, piece_default_size)
            pieces, left_parts = self._group_parts_to_pieces(file_parts + left_parts, piece_default_size)
            yield pieces
        if left_parts:
            yield [left_parts]

    def _get_file_parts(self,
                        file: AbstractFileLoader,
                        left_parts: List[Part],
                        piece_default_size: int) -> List[Part]:
        file_first_block_size = piece_default_size - self._sum_parts_size(left_parts)
        file_parts = file.create_file_parts(file_first_block_size, piece_default_size)
        return file_parts

    @staticmethod
    def _group_parts_to_pieces(parts: List[Part], piece_default_size: int) -> tuple[List[List[Part]], List[Part]]:
        pieces_parts = []
        parts_groups = []
        for part in parts:
            pieces_parts.append(part)
            if TorrentLoader._sum_parts_size(pieces_parts) == piece_default_size:
                parts_groups.append(pieces_parts)
                pieces_parts = []
        return parts_groups, pieces_parts

    @staticmethod
    def _sum_parts_size(parts: List[Part]):
        return sum(part.size for part in parts)
