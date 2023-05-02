import socket
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, ClassVar

from torrent_client.tracker.event import Event
from torrent_client.tracker.exceptions import TrackerCommotionError
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse
from torrent_client.tracker.udp_net.udp_action import UDPAction

Response = Any

PROTOCOL_ID: int = 0x41727101980


@dataclass
class UdpTrackerResponse:
    action: UDPAction
    transaction_id: int
    payload: bytes


def decode_ip_port(data) -> list[dict[str, str]]:
    peers = []
    offset = 20
    while offset+6 < len(data):
        ip_int, port = struct.unpack("!IH", data[offset:offset + 6])
        ip_address = socket.inet_ntoa(struct.pack("!I", ip_int))
        peers.append({'ip': ip_address, 'port': port})
        offset += 6
    return peers


class AbstractUDPMessageManager(ABC):
    @abstractmethod
    def encode_response_header(self, data) -> UdpTrackerResponse:
        pass

    @abstractmethod
    def encode_connect(self, response: UdpTrackerResponse) -> int:
        return struct.unpack("!I", response)[0]

    @abstractmethod
    def decode_connect(self, transaction_id: int) -> bytes:
        pass

    @abstractmethod
    def decode_announce(self, connection_id: int, transaction_id: int, req: TrackerRequest) -> bytes:
        pass

    @abstractmethod
    def encode_announce(self, response: UdpTrackerResponse) -> TrackerResponse:
        pass

    @abstractmethod
    def check_and_raise_error(self, response: UdpTrackerResponse) -> None:
        pass


class UDPMessageManager(AbstractUDPMessageManager):
    RESPONSE_HEADER_ENCODER = struct.Struct("!II")
    CONNECT_DECODER = struct.Struct("!QII")
    CONNECT_ENCODER = struct.Struct("!Q")
    ANNOUNCE_ENCODE = struct.Struct("!QLL20s20sQQQLLLlI")
    ANNOUNCE_WITHOUT_PEERS_DECODER = struct.Struct("!III")

    def encode_response_header(self, data: bytes) -> UdpTrackerResponse:
        header_size = self.RESPONSE_HEADER_ENCODER.size
        if len(data) < header_size:
            raise ValueError("data was to shore for response")
        action, transaction_id = self.RESPONSE_HEADER_ENCODER.unpack(data[:header_size])
        return UdpTrackerResponse(UDPAction(action), transaction_id, data[header_size:])

    def encode_connect(self, response: UdpTrackerResponse) -> int:
        return self.CONNECT_ENCODER.unpack(response.payload)[0]

    def decode_connect(self, transaction_id: int):
        return self.CONNECT_DECODER.pack(PROTOCOL_ID, UDPAction.CONNECT_ACTION.value, transaction_id)

    def decode_announce(self, connection_id: int, transaction_id: int, req: TrackerRequest):
        return self.ANNOUNCE_ENCODE.pack(
            connection_id,
            UDPAction.ANNOUNCE_ACTION.value,
            transaction_id,
            req.info_hash,
            req.peer_id,
            req.downloaded,
            req.left,
            req.uploaded,
            Event.to_udp(req.event),
            0,
            0,
            -1,
            9999)

    def encode_announce(self, response: UdpTrackerResponse) -> TrackerResponse:
        payload = response.payload
        encode_size = self.ANNOUNCE_WITHOUT_PEERS_DECODER.size
        interval, _, _ = self.ANNOUNCE_WITHOUT_PEERS_DECODER.unpack(payload[:encode_size])
        return TrackerResponse(interval, decode_ip_port(payload[encode_size:]))

    def check_and_raise_error(self, response: UdpTrackerResponse):
        payload = response.payload
        if response.action == UDPAction.ERROR_ACTION.value:
            message = struct.unpack(f'!4{len(payload)}', response.payload)
            raise TrackerCommotionError(f"got error message {message}")
