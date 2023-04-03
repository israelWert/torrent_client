from torrent_client.test.data import torrent_file_1
from torrent_client.torrent_file.decoder import Decoder


class TestUnitDecoder:
    def test_decoder_encapsulate(self):
        file = Decoder._encapsulate(torrent_file_1.data)

        assert len(file.pieces) == len(torrent_file_1.data["info"]["pieces"])/20
        assert file.name == torrent_file_1.data["info"]["name"]
        assert file.is_single
