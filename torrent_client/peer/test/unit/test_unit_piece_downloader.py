from hashlib import sha1

from torrent_client.peer.downloading.piece_bitfield_info import PieceBitfieldInfo
from torrent_client.peer.downloading.piece_request import PieceDownloader
from torrent_client.peer.test.fakes.fake_peer_bridge import FakePeerBridge


class TestUnitPieceDownloader:
    def test_lock_unlock(self):
        bridge = FakePeerBridge()
        bridge.available_piece_to_download = [0]
        bridge.piece_info = PieceBitfieldInfo(0, None, sha1(b"").digest())
        bitfield = [True]
        with PieceDownloader(bridge, bitfield) as prs:
            pass
        assert bridge.locked_index == 0
        assert bridge.unlocked_index == 0
