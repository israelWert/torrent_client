from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic


PeerMessage_ = TypeVar('PeerMessage_')


class MessageFactory(ABC, Generic[PeerMessage_]):
    @abstractmethod
    def decode(self, data: bytes) -> PeerMessage_:
        pass

    @abstractmethod
    def encode(self, obj: PeerMessage_) -> bytes:
        pass
