import asyncio
import struct
from collections import OrderedDict
from typing import Optional
from urllib import parse

import aiohttp
import bencode
from aiohttp import ClientConnectorError
from bencode import BencodeDecodeError

from torrent_client.tracker.event import Event
from torrent_client.tracker.exceptions import TrackerCommotionError
from torrent_client.tracker.net.tracker_protocol import TrackerProtocol
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse

import logging
logger = logging.getLogger(__name__)


class HttpTracker(TrackerProtocol):
    def __init__(self, tracker_url):
        self._tracker_url = tracker_url
        logger.info("http tracker was created")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def send_message(self, req: TrackerRequest, with_response: bool = True) -> Optional[TrackerResponse]:
        logger.info(f"tracker {self} sending request")
        req = self._create_request(req)
        response = await self._talk_with_tracker(req)
        if with_response:
            logger.debug(f"we got new response {response}")
            r = self._decode_response(response)
            logger.debug(f"decoded response {r}")
            return r

    async def _talk_with_tracker(self, req: str) -> bytes:
        try:
            async with await self.session.get(req) as response:
                return await response.read()
        except ClientConnectorError:
            logger.warning("tracker connection closed")
            raise TrackerCommotionError()


    def _create_request(self, req: TrackerRequest) -> str:
        params = {
            'info_hash': req.info_hash,
            'peer_id': req.peer_id,
            'port': req.port,
            'uploaded': req.uploaded,
            'downloaded': req.downloaded,
            'left': req.left}
        if req.event:
            params["event"] = Event.to_http(req.event)
        params = parse.urlencode(params)
        res = f"{self._tracker_url}?{params}"
        logger.debug(f"request : {res}")
        return res

    @staticmethod
    def _encode_peers(peers_data):
        if isinstance(peers_data, OrderedDict):
            peers = []
            for peer in peers_data:
                ip = peer["ip"]
                port = peer["port"]
                peers.append({'ip': ip, 'port': port})
        else:
            peers = []
            for i in range(0, len(peers_data), 6):
                ip = f"{peers_data[i]}.{peers_data[i+1]}.{peers_data[i+2]}.{peers_data[i+3]}"
                port = struct.unpack("!H", peers_data[i+4:i+6])[0]
                peers.append({'ip': ip, 'port': port})
        return peers

    def _decode_response(self, data: bytes) -> TrackerResponse:
        try:
            decoded = bencode.decode(data)
        except BencodeDecodeError:
            logger.info(f"the tracker {self._tracker_url} send message {data}")
            raise TrackerCommotionError()
        logger.debug(f"message after decoding bencoding {decoded}")
        interval = decoded['interval']
        peers = self._encode_peers(decoded["peers"])
        return TrackerResponse(interval, peers)

    def get_tracker_url(self):
        return self._tracker_url


    def is_connected(self):
        return not self.session.closed
