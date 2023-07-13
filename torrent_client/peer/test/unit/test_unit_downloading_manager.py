import pytest

from torrent_client.peer.exceptions import NoPieceNeededError
from torrent_client.peer.downloading.downloading_manager import DownloadingManager
from torrent_client.peer.downloading.piece_request import PieceDownloader
from torrent_client.peer.test.fakes.fake_peer_bridge import FakePeerBridge


def create_text_objects(size: int, needed_pieces_indexes: [int], peer_bitfiled: [bool]) -> DownloadingManager:
    downloader = FakePeerBridge()
    downloader.available_piece_to_download = needed_pieces_indexes
    piece_manager = DownloadingManager(size, downloader)
    piece_manager.set_bitfiled(peer_bitfiled)
    return piece_manager


class TestUnitDownloadingManager:

    def test_available_piece_no_needed_pieces(self):
        piece_manager = create_text_objects(1, [], [True])
        assert not piece_manager.has_available_piece()

    def test_available_piece_empty_bitfiled(self):
        piece_manager = create_text_objects(1, [0], [False])
        assert not piece_manager.has_available_piece()

    def test_available_piece_with_needed_pieces_indexes_not_downloaded(self):
        piece_manager = create_text_objects(3, [0, 1], [False, False, True])
        assert not piece_manager.has_available_piece()

    def test_available_find_piece_to_download(self):
        piece_manager = create_text_objects(1, [0], [True])
        assert piece_manager.has_available_piece()
        assert isinstance(piece_manager.create_piece_downloader(), PieceDownloader)

        piece_manager = create_text_objects(3, [1], [False, True, False])
        assert piece_manager.has_available_piece()
        assert isinstance(piece_manager.create_piece_downloader(), PieceDownloader)