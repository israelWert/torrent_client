import pytest

from torrent_client.peer.exceptions import NoPieceNeededError
from torrent_client.peer.piece.piece_manager import PieceManager
from torrent_client.peer.piece.piece_request_state import PieceRequestState
from torrent_client.peer.test.fakes.fake_peer_bridge import FakePeerBridge


def create_text_objects(size: int, needed_pieces_indexes: [int], peer_bitfiled: [bool]) -> PieceManager:
    downloader = FakePeerBridge()
    downloader.available_piece_to_download = needed_pieces_indexes
    piece_manager = PieceManager(size, downloader)
    piece_manager.set_bitfiled(peer_bitfiled)
    return piece_manager


class TestUnitPieceManager:

    def test_available_piece_no_needed_pieces(self):
        piece_manager = create_text_objects(1, [], [True])
        assert not piece_manager.is_have_available_piece()

    def test_available_piece_empty_bitfiled(self):
        piece_manager = create_text_objects(1, [0], [False])
        assert not piece_manager.is_have_available_piece()

    def test_available_piece_with_needed_pieces_indexes_not_downloaded(self):
        piece_manager = create_text_objects(3, [0, 1], [False, False, True])
        assert not piece_manager.is_have_available_piece()

    def test_available_find_piece_to_download(self):
        piece_manager = create_text_objects(1, [0], [True])
        assert piece_manager.is_have_available_piece()
        assert isinstance(piece_manager.create_piece_request(), PieceRequestState)

        piece_manager = create_text_objects(3, [1], [False, True, False])
        assert piece_manager.is_have_available_piece()
        assert isinstance(piece_manager.create_piece_request(), PieceRequestState)