import asyncio
import logging
import random
import socket
from typing import Optional

from torrent_client.tracker.exceptions import TrackerCommotionError, TrackerNotSportedError, \
    TrackerNotRespondingError
from torrent_client.tracker.net.tracker_protocol import TrackerProtocol
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse
from torrent_client.tracker.net.udp_net.async_udp_client import AbstractAsyncUdpClient
from enum import Enum

from torrent_client.tracker.net.udp_net.udp_tracker_messages import UDPMessageManager, AbstractUDPMessageManager

logger = logging.getLogger(__name__)
MAX_TRANSACTION_ID = 2 ** 32 - 1
MAX_ATTEMPTS_TO_CONNECT = 12
RETRANSMISSION_MAX = 4


class Action(Enum):
    CONNECT_ACTION = 0
    ANNOUNCE_ACTION = 1
    ERROR_ACTION = 3


class UDPTracker(TrackerProtocol):
    def __init__(self, tracker_url: str,
                 udp_client: AbstractAsyncUdpClient,
                 message_manager: AbstractUDPMessageManager = None):
        self._message_manager = message_manager if message_manager else UDPMessageManager()
        self.ip, str_port = UDPTracker.get_ip_and_port(tracker_url)
        self.port = int(str_port)
        self._tracker_url = tracker_url
        self.client = udp_client
        self._connection_id = None
        self._attempts_to_connect = 0
        logger.info("udp tracker was created")

    async def __aenter__(self):
        try:
            addrinfo = socket.getaddrinfo(self.ip, self.port, socket.AF_INET, socket.SOCK_DGRAM)
            self.ip = addrinfo[0][4][0]
            if self.ip.count(":") > 0:
                raise TrackerNotSportedError()
        except socket.gaierror:
            raise TrackerNotRespondingError()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def is_connected(self):
        return self._attempts_to_connect < MAX_ATTEMPTS_TO_CONNECT

    async def send_message(self, req: TrackerRequest, with_response: bool = True) -> Optional[TrackerResponse]:
        logger.info("send new request")
        logger.debug(req)
        if not self._connection_id and not with_response:
            return
        if not self._connection_id:
            self._attempts_to_connect += 1
            await self._connect()
            logger.info("connection was established")
        response = await self._announce(req, with_response)
        logger.info("response was received successfully")
        return response

    async def _connect(self):
        transaction_id = self.generate_transaction_id()
        message = self._message_manager.decode_connect(transaction_id)
        response = await self._send_recv_reliable(message, transaction_id)
        self._connection_id = self._message_manager.encode_connect(response)

    async def _announce(self, req: TrackerRequest, with_response: bool) -> Optional[TrackerResponse]:
        transaction_id = self.generate_transaction_id()
        message = self._message_manager.decode_announce(
            self._connection_id,
            transaction_id,
            req)
        if not with_response:
            self._send(message)
            return
        response = await self._send_recv_reliable(message, transaction_id)
        return self._message_manager.encode_announce(response)

    async def _send_recv_reliable(self, message: bytes, transaction_id: int):
        for i in range(RETRANSMISSION_MAX):
            self._send(message)
            response = await self.client.receive_message(transaction_id, 2**i * 15)
            if response:
                logger.debug(f"response: f{response}")
                return response
        self._connection_id = None
        logger.warning("no response was returned by tracker")
        raise TrackerCommotionError()

    def _send(self, message: bytes):
        self.client.send_message(message, (self.ip, self.port))

    @staticmethod
    def get_ip_and_port(url):
        url = url.split("/")[2]
        data = url.split(":")
        if len(data) != 2:
            raise TrackerNotSportedError()
        return data

    @staticmethod
    def generate_transaction_id():
        return random.randint(0, MAX_TRANSACTION_ID)
