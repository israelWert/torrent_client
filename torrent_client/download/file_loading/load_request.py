from dataclasses import dataclass


@dataclass
class LoadRequest:
    beginning_in_file: int
    data: bytes
    size: int
