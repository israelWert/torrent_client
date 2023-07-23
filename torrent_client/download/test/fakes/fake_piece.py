from torrent_client.download.piece import AbstractPiece
from torrent_client.peer.downloading.piece_bitfield_info import PieceBitfieldInfo


class FakePiece(AbstractPiece):
    def is_available_to_download(self) -> bool:
        pass

    def occupy(self) -> PieceBitfieldInfo:
        pass

    def release(self) -> None:
        pass

    async def download(self, data: bytes) -> None:
        pass

    def get_size(self) -> int:
        pass

    def is_downloaded(self) -> bool:
        pass
