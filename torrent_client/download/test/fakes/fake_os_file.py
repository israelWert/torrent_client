from torrent_client.download.file_loading.os_file import AbstractOsFile


class FakeOsFile(AbstractOsFile):
    def __init__(self):
        self.wrote_data = []

    async def __aenter__(self) -> "AbstractOsFile":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def write(self, data: bytes) -> None:
        self.wrote_data.append(data)

    async def read(self, size) -> bytes:
        pass

    async def seek(self, pos: int) -> None:
        pass
