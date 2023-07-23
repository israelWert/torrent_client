import pytest

from torrent_client.download.file_loading.torrent_loader import TorrentLoader
from torrent_client.download.test.fakes.fake_file_loader import FakeFileLoader


class TestUnitTorrentLoaderLoad:
    @pytest.mark.asyncio
    async def test_run_loaders(self):
        files = [FakeFileLoader([]) for _ in range(5)]
        t_loader = TorrentLoader(files_loaders=files)
        await t_loader.listen_to_requests_and_download()
        for file in files:
            assert file.run_load
