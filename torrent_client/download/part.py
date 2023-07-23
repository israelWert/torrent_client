from dataclasses import dataclass
from torrent_client.download.file_loading.load_listener import LoadListener


@dataclass
class Part:
    file: LoadListener
    size: int
    beginning: int
