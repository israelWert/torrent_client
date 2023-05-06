import asyncio
import pytest

from torrent_client.tracker.exceptions import TrackerCommotionError
from torrent_client.tracker.test.fakes.fake_clock import FakeClock
from torrent_client.tracker.test.fakes.fake_tracker_bridge import FakeTrackerBridge
from torrent_client.tracker.test.fakes.fake_tracker_logic import FakeTrackerLogic
from torrent_client.tracker.test.fakes.fake_tracker_protocol import FakeTrackerProtocol
from torrent_client.tracker.tracker import Tracker
from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse


def create_request():
    return TrackerRequest(b"", "", 0, 0, 0, 0,  None)


def create_response():
    return TrackerResponse(0, [])


async def tracker_event(tracker_logic: FakeTrackerLogic, protocol, response_or_error, request):
    tracker_logic.request = request
    protocol.response_or_error = response_or_error
    tracker_logic.is_time_for_next = True
    await asyncio.sleep(0.001)


class TestUnitTracker:

    @pytest.fixture
    def tracker_init_data(self):
        tracker_logic = FakeTrackerLogic()
        protocol = FakeTrackerProtocol()
        bridge = FakeTrackerBridge()
        clock = FakeClock()
        tracker = Tracker(logic=tracker_logic, protocol=protocol, download_bridge=bridge, clock=clock)
        tracker_logic.stop_function = tracker.stop
        return tracker, tracker_logic, protocol

    @pytest.mark.asyncio
    async def test_start_and_close(self, tracker_init_data):
        tracker, tracker_logic, protocol = tracker_init_data
        tracker.start()
        await asyncio.sleep(0.001)
        assert protocol.has_entered
        tracker.stop()
        await asyncio.sleep(0.001)
        assert protocol.has_exit

    @pytest.mark.asyncio
    async def test_one_response(self, tracker_init_data):
        tracker, tracker_logic, protocol = tracker_init_data
        response, request = create_response(), create_request()
        tracker.start()
        assert not tracker.get_peers()
        await tracker_event(tracker_logic, protocol, response, request)
        assert isinstance(tracker.get_peers(), list)
        assert isinstance(tracker_logic.response, TrackerResponse)
        assert tracker_logic.response is response
        assert isinstance(protocol.request, TrackerRequest)
        assert protocol.request is request
        tracker.stop()
        await asyncio.sleep(0.001)
        assert tracker.has_stopped()

    @pytest.mark.asyncio
    async def test_with_error(self, tracker_init_data):
        tracker, tracker_logic, protocol = tracker_init_data
        tracker.start()
        error = TrackerCommotionError()
        await tracker_event(tracker_logic, protocol, error, create_request())
        assert tracker_logic.connection_errors == 1
        tracker.stop()
        await asyncio.sleep(0.001)
