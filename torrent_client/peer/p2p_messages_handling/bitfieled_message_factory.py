import struct
from typing import List

from torrent_client.peer.p2p_messages_handling.message_factory import MessageFactory, PeerMessage_
from torrent_client.peer.p2p_messages_handling.p2p_messages import BitfieldMessage


class BitfieldMessageFactory(MessageFactory):
    def __init__(self, bitfield_size):
        self._bitfield_size = bitfield_size

    @staticmethod
    def _byte_to_bit_list(byte: int) -> List[bool]:
        return [bool((byte >> bit_index) & 1) for bit_index in range(8)]

    def decode(self, data: bytes) -> BitfieldMessage:
        bitfield = []
        for byte in data:
            bitfield.extend(self._byte_to_bit_list(byte))
        return BitfieldMessage(bitfield[:self._bitfield_size])

    @staticmethod
    def complete_to_8_bit(bits: List[bool]):
        bits.extend([False] * (8 - len(bits)))

    @staticmethod
    def bits_to_byte(bits: List[bool]):
        bits_int = 0
        for idx, setting in enumerate(bits):
            bits_int += setting * 2 ** idx
        return struct.pack("B", bits_int)

    def encode(self, obj: BitfieldMessage) -> bytes:
        bit_list = obj.bit_field
        bytes_bitfiled = b""
        for byte_start in range(0, len(bit_list), 8):
            bits = bit_list[byte_start:byte_start+8]
            self.complete_to_8_bit(bits)
            bytes_bitfiled += self.bits_to_byte(bits)
        return bytes_bitfiled
