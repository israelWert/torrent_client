from torrent_client.peer.downloading.piece_request import AbstractPieceDownloader


class FakePieceDownloader(AbstractPieceDownloader):
    def __init__(self):
        self.is_piece_complete_res = False
        self.requests = []
        self.blocks = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self):
        return self.requests.__iter__()

    def is_piece_complete(self) -> bool:
        return self.is_piece_complete_res

    def add_block(self, block: bytes, index: int):
        self.blocks.append(block)