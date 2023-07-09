from hashlib import sha1

from torrent_client.peer.piece.piece_download_info import PieceDownloadInfo
from torrent_client.peer.piece.piece_request_state import PieceRequestState
from torrent_client.peer.test.fakes.fake_peer_bridge import FakePeerBridge


class TestUnitPieceRequestState:
    def test_lock_unlock(self):
        bridge = FakePeerBridge()
        bridge.available_piece_to_download = [0]
        bridge.piece_info = PieceDownloadInfo(0, None, sha1(b"").digest())
        bitfield = [True]
        with PieceRequestState(bridge, bitfield) as prs:
            pass
        assert bridge.locked_index == 0
        assert bridge.unlocked_index == 0
