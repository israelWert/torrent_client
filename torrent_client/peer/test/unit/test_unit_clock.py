import pytest

from torrent_client.peer.p2p_net.clock import Clock
from torrent_client.peer.exceptions import PeerTimeOutError


class TestUnitClock:
    @pytest.mark.asyncio
    async def test_wait_timeout_zero(self):
        clock = Clock()
        with pytest.raises(PeerTimeOutError):
            await clock.sleep(0.1)

    @pytest.mark.asyncio
    async def test_wait_less_then_timeout(self):
        clock = Clock()
        clock.set_timeout(0.2)
        await clock.sleep(0.1)

    @pytest.mark.asyncio
    async def test_reset(self):
        clock = Clock()
        clock.set_timeout(0.2)
        await clock.sleep(0.15)
        clock.reset()
        await clock.sleep(0.15)

    @pytest.mark.asyncio
    async def test_reset_and_then_more_the_timeout(self):
        clock = Clock()
        clock.set_timeout(0.2)
        await clock.sleep(0.15)
        clock.reset()
        with pytest.raises(PeerTimeOutError):
            await clock.sleep(0.3)

    @pytest.mark.asyncio
    async def test_wait_twice_until_timeout(self):
        clock = Clock()
        clock.set_timeout(0.2)
        await clock.sleep(0.1)
        with pytest.raises(PeerTimeOutError):
            await clock.sleep(0.2)


