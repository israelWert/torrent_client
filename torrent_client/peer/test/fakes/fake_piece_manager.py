from typing import List

from torrent_client.peer.piece.piece_manager import AbstractPieceManager
from torrent_client.peer.piece.piece_request_state import AbstractPieceRequestState


class FakePieceManager(AbstractPieceManager):
    def __init__(self):
        self.notify_new_piece_data = []
        self.bit_field_response = None
        self.is_have_available_piece_res = True
        self.request_state = None

    def create_piece_request(self) -> AbstractPieceRequestState:
        return self.request_state

    def set_bitfiled(self, bitfiled: List[bool]):
        self.bit_field_response = bitfiled

    def notify_new_piece(self, index: int):
        self.notify_new_piece_data.append(index)

    def is_have_available_piece(self) -> bool:
        return self.is_have_available_piece_res

    def is_end_downloading(self) -> bool:
        return False
