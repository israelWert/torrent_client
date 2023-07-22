from dataclasses import dataclass


@dataclass
class PieceBitfieldInfo:
    index: int
    piece_length: int
    piece_hash: bytes
