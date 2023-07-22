import bencode

from torrent_client.test.data import torrents
from torrent_client.torrent_file.decoder import Decoder
from torrent_client.torrent_file.file_to_download import FileToDownload


class TestUnitDecoder:
    def test_decoder_single_file(self):
        data = bencode.decode(torrents.single_file)
        file = Decoder._encapsulate(data)
        assert len(file.pieces) == len(data["info"]["pieces"]) / 20
        assert file.name == data["info"]["name"]
        assert file.is_single
        assert isinstance(file.files[0], FileToDownload)
        assert isinstance(file.pieces[0], bytes)
        assert isinstance(file.info_hash, bytes)
        assert 1 == len(file.files)

    def test_decoder_multi_file(self):
        data = bencode.decode(torrents.multi_file)
        file = Decoder._encapsulate(data)
        assert len(file.pieces) == len(data["info"]["pieces"]) / 20
        assert file.name == data["info"]["name"]
        assert not file.is_single
        assert isinstance(file.files[0], FileToDownload)
        assert isinstance(file.pieces[0], bytes)
        assert isinstance(file.info_hash, bytes)
        assert 1 < len(file.files)
