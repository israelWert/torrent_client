from torrent_client.peer.piece.piece_request_state import AbstractPieceRequestState


class FakePieceRequestState(AbstractPieceRequestState):
    def __init__(self):
        self.is_piece_complete_res = False
        self.requests = []
        self.blocks = []

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self):
        return self.requests

    def is_piece_complete(self) -> bool:
        return self.is_piece_complete_res

    def add_block(self, block: bytes, index: int):
        self.blocks.append(block)