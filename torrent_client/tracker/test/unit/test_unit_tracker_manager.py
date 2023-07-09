import asyncio

import pytest

from torrent_client.tracker.exceptions import TrackerStoppedNoUnknownReasonError, TrackerFailedTooManyTimesError, \
    TrackerNotRespondingError, NoTrackerLeftError
from torrent_client.tracker.test.fakes.fake_clock import FakeClock
from torrent_client.tracker.test.fakes.fake_tracker import FakeTracker
from torrent_client.tracker.test.fakes.fake_tracker_factory import FakeTrackerFactory
from torrent_client.tracker.tracker_manager import TrackerManager


class TestUnitTrackerManager:
    @pytest.fixture
    def tracker_manager_init(self):
        factory, clock = FakeTrackerFactory(), FakeClock()
        return factory, clock, TrackerManager(factory=factory, clock=clock)

    def test_start_trackers(self, tracker_manager_init):
        factory, clock, tracker_manager = tracker_manager_init
        trackers = [FakeTracker(), FakeTracker()]
        factory.list = trackers
        tracker_manager.start_trackers()
        for tracker in trackers:
            assert tracker.has_started

    @pytest.mark.asyncio
    async def test_stop_trackers(self, tracker_manager_init):
        factory, clock, tracker_manager = tracker_manager_init
        trackers = [FakeTracker(), FakeTracker()]
        factory.list = trackers
        tracker_manager.start_trackers()
        task = asyncio.create_task(tracker_manager.stop())
        await asyncio.sleep(0)

        assert not task.done()
        for tracker in trackers:
            assert tracker.was_stop_called
            tracker.has_stop_return = True
        await asyncio.sleep(0)
        assert task.done()

    def test_get_peers(self, tracker_manager_init):
        factory, clock, tracker_manager = tracker_manager_init
        trackers = [FakeTracker(), FakeTracker()]
        peers = [{"1": 0}, {"2", 0}]
        for tracker in trackers:
            tracker.peers_to_return = peers
        factory.list = trackers
        tracker_manager.start_trackers()
        assert tracker_manager.get_peers() == peers*2

    def test_with_errors(self, tracker_manager_init):
        factory, clock, tracker_manager = tracker_manager_init
        tracker_0 = FakeTracker()
        tracker_1 = FakeTracker()
        tracker_2 = FakeTracker()
        factory.list = [tracker_1, tracker_0, tracker_2]
        tracker_manager.start_trackers()
        tracker_0.error = TrackerStoppedNoUnknownReasonError()
        tracker_manager.get_peers()
        assert tracker_0 not in tracker_manager._trackers
        tracker_1.error = TrackerFailedTooManyTimesError(1)
        tracker_manager.get_peers()
        assert tracker_1 not in tracker_manager._trackers
        tracker_2.error = TrackerNotRespondingError()
        with pytest.raises(NoTrackerLeftError):
            tracker_manager.get_peers()
            assert tracker_2 not in tracker_manager._trackers
