from dataclasses import dataclass
from typing import List, Union, Dict

from torrent_client.torrent_file.file_to_download import FileToDownload


@dataclass
class TorrentFile:
    announce_list: List[str]
    name: str
    piece_length: int
    pieces: List[bytes]
    is_single: bool
    files: List[FileToDownload]
    info_hash: bytes
    total_size: int

