import bencode

from torrent_client.test.data import torrents
from torrent_client.torrent_file.decoder import Decoder


class TestUnitDecoder:
    def test_decoder_single_file(self):
        data = bencode.decode(torrents.single_file)
        file = Decoder._encapsulate(data)
        assert len(file.pieces) == len(data["info"]["pieces"]) / 20
        assert file.name == data["info"]["name"]
        assert file.is_single
        assert ["length", "path"] == list(file.files[0].keys())
        assert bytes is type(file.pieces[0])

    def test_decoder_multi_file(self):
        data = bencode.decode(torrents.multi_file)
        file = Decoder._encapsulate(data)
        assert len(file.pieces) == len(data["info"]["pieces"]) / 20
        assert file.name == data["info"]["name"]
        assert not file.is_single
        assert["length", "path"] == list(file.files[0].keys())
        assert bytes is type(file.pieces[0])
