import asyncio
import logging
import struct
from collections import OrderedDict
from typing import Optional
from urllib import parse

import aiohttp
import bencode
from aiohttp import ClientConnectorError
from bencodepy import BencodeDecodeError

from torrent_client.tracker.event import Event
from torrent_client.tracker.exceptions import TrackerCommotionError
from torrent_client.tracker.net.tracker_protocol import TrackerProtocol
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse


logger = logging.getLogger(__name__)


class HttpTracker(TrackerProtocol):

    def __init__(self, tracker_url):
        self._tracker_url = tracker_url
        self._task = None
        logger.info("http tracker was created")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def send_message(self, req: TrackerRequest, with_response: bool = True) -> None:
        self._task = asyncio.create_task(self._send_request(req, with_response))

    async def get_response(self) -> Optional[TrackerResponse]:
        if self._task:
            if self._task.done():
                res = self._task.result()
                self._task = None
                if isinstance(res, Exception):
                    raise res
                return res

    async def _send_request(self, req: TrackerRequest, with_response: bool = True):
        logger.info(f"tracker {self._tracker_url} sending request")
        req = self._create_request(req)
        try:
            if not with_response:
                async with await self.session.get(req):
                    return
            async with await self.session.get(req) as response:
                return self._decode_response(await response.read())
        except ClientConnectorError:
            logger.warning("tracker connection closed")
            return TrackerCommotionError()
        except Exception as e:
            return e

    def _create_request(self, req: TrackerRequest) -> str:
        params = {
            'info_hash': req.info_hash,
            'peer_id': req.peer_id,
            'port': req.port,
            'uploaded': req.uploaded,
            'downloaded': req.downloaded,
            'left': req.left, }
        if req.event:
            params["event"] = Event.to_http(req.event)
        params = parse.urlencode(params)
        res = f"{self._tracker_url}?{params}"
        logger.debug(f"request : {res}")
        return res

    @staticmethod
    def _encode_peers(peers_data: OrderedDict):
        peers = []
        for peer in peers_data:
            ip = peer["ip"]
            port = peer["port"]
            peers.append({'ip': ip, 'port': port})
        return peers

    def _decode_response(self, data) -> TrackerResponse:
        try:
            decoded = bencode.decode(data)
        except BencodeDecodeError:
            logger.info(f"the tracker {self._tracker_url} send message {data}")
            raise TrackerCommotionError()
        interval = decoded['interval']
        peers = self._encode_peers(decoded["peers"])
        return TrackerResponse(interval, peers)

    def get_tracker_url(self):
        return self._tracker_url
