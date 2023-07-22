from typing import List

from torrent_client.download.file_loading.torrent_loader import AbstractTorrentLoader, PieceInPart


class FakeTorrentLoader(AbstractTorrentLoader):
    async def listen_to_requests_and_download(self) -> None:
        pass

    def get_files_parts_in_pieces(self, piece_default_size: int) -> List[PieceInPart]:
        pass
