from dataclasses import dataclass
from typing import List


@dataclass
class FileToDownload:
    length: int
    path: List[str]
