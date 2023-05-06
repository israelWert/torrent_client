from dataclasses import dataclass
from typing import List, Union, Dict


@dataclass
class File:
    announce_list: List[str]
    name: str
    piece_length: int
    pieces: List[bytes]
    is_single: bool
    files: List[Dict[str, Union[int, List[str]]]]
    info_hash: bytes
    total_size: int

