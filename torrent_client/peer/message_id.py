from enum import Enum


class MessageID(Enum):
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    Bitfiled = 5
    Request = 6
    Piece = 7
    Handshake = 8
