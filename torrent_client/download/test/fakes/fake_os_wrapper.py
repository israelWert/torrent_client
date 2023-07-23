from torrent_client.download.file_loading.os_file import AbstractOsFile
from torrent_client.download.file_loading.os_wrapper import AbstractOsWrapper


class FakeOsWrapper(AbstractOsWrapper):
    def __init__(self):
        self.is_dir_exist_return = False
        self.created_dirs = []
        self.os_files_to_return = []

    async def makedir(self, path: str) -> None:
        self.created_dirs.append(path)

    def make_file(self, path: str) -> AbstractOsFile:
        return self.os_files_to_return.pop()

    def is_dir_exist(self, path: str) -> bool:
        return self.is_dir_exist_return
