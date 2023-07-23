import asyncio
from asyncio import InvalidStateError

import pytest

from torrent_client.download.file_loading.file_loader import FileLoader
from torrent_client.download.file_loading.load_request import LoadRequest
from torrent_client.download.test.fakes.fake_os_file import FakeOsFile
from torrent_client.download.test.fakes.fake_os_wrapper import FakeOsWrapper
from torrent_client.torrent_file.file_to_download import FileToDownload


class TestFileLoaderListenToRequests:
    @pytest.mark.asyncio
    async def test_still_running_if_file_doesnt_complete(self):
        file_length = 10
        os = FakeOsWrapper()
        f = FileLoader(FileToDownload(file_length, []), os)
        task = asyncio.create_task(f.listen_to_requests_and_download())
        os.os_files_to_return = [FakeOsFile()]
        await asyncio.sleep(0.1)
        with pytest.raises(InvalidStateError):
            task.exception()
        assert not task.done()
        task.cancel()

    @pytest.mark.asyncio
    async def test_sending_one_full_request(self):
        file_length = 10
        os = FakeOsWrapper()
        f = FileLoader(FileToDownload(file_length, []), os)
        file = FakeOsFile()
        os.os_files_to_return = [file]
        task = asyncio.create_task(f.listen_to_requests_and_download())
        await f.add_load_request(LoadRequest(0, b"test", 10))
        await asyncio.sleep(0.01)
        assert file.wrote_data[0] == b"test"
        assert task.done()
        assert task.exception() is None

    @pytest.mark.asyncio
    async def test_sending_two_requests_full_file(self):
        file_length = 10
        os = FakeOsWrapper()
        f = FileLoader(FileToDownload(file_length, []), os)
        file = FakeOsFile()
        os.os_files_to_return = [file]
        task = asyncio.create_task(f.listen_to_requests_and_download())
        await f.add_load_request(LoadRequest(0, b"test1", 5))
        await f.add_load_request(LoadRequest(0, b"test2", 5))
        await asyncio.sleep(0.01)
        assert file.wrote_data[0] == b"test1"
        assert file.wrote_data[1] == b"test2"
        assert task.done()
        assert task.exception() is None
