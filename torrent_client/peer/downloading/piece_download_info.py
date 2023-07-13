from dataclasses import dataclass


@dataclass
class PieceDownloadInfo:
    index: int
    piece_length: int
    piece_hash: bytes
