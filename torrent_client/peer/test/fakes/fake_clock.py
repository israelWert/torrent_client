from torrent_client.peer.p2p_net.clock import AbstractClock
from torrent_client.peer.exceptions import PeerTimeOutError


class FakeClock(AbstractClock):
    def __init__(self):
        self.timeout = -1
        self._time_waited = 0

    async def sleep(self, sec: float) -> None:
        if self.timeout == -1:
            return
        self._time_waited += sec
        if self.timeout <= self._time_waited:
            raise PeerTimeOutError()

    def set_timeout(self, timeout: float) -> None:
        pass

    def reset(self):
        self._time_waited = 0
