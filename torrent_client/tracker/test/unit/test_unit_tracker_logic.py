from torrent_client.torrent_file.file import File
from torrent_client.tracker.event import Event
from torrent_client.tracker.exceptions import TrackerFailedTooManyTimesError
from torrent_client.tracker.test.fakes.fake_clock import FakeClock
from torrent_client.tracker.tracker_logic import TrackerLogic, MAX_FAILURES

from pytest import fixture, raises

from torrent_client.tracker.tracker_request import TrackerRequest
from torrent_client.tracker.tracker_response import TrackerResponse


def check_message(message: TrackerRequest,
                  uploaded_and_downloaded: tuple,
                  file: File,
                  peer_id: bytes):
    assert isinstance(message, TrackerRequest)
    assert uploaded_and_downloaded == (message.uploaded, message.downloaded)
    assert message.peer_id == peer_id
    assert message.left == file.total_size - sum(uploaded_and_downloaded)
    assert message.info_hash == file.info_hash


class TestUnitTrackerLogic:

    @fixture
    def tracker_logic_init_data(self):
        file = File(
            ["_class", "b"],
            "name",
            1,
            [b"_class", b"b"],
            True,
            [{}, {}],
            b"info_hash",
            2)
        clock = FakeClock()
        peer_id = b"_peer_id"
        logic = TrackerLogic(file, peer_id, clock)
        uploaded_and_downloaded = (6, 5)
        return file, clock, peer_id, logic, uploaded_and_downloaded

    def test_first_message(self, tracker_logic_init_data):
        file, clock, peer_id, logic, uploaded_and_downloaded = tracker_logic_init_data
        message = logic.update(*uploaded_and_downloaded)
        check_message(message, uploaded_and_downloaded, file, peer_id)
        assert Event.Start == message.event

    def test_message_after_response(self, tracker_logic_init_data):
        file, clock, peer_id, logic, uploaded_and_downloaded = tracker_logic_init_data
        interval = 5
        logic.update(0, 0)
        logic.update(*uploaded_and_downloaded, response=TrackerResponse(interval, []))
        assert not logic.update(0, 0)
        clock.current_time += interval
        message = logic.update(*uploaded_and_downloaded)
        check_message(message, uploaded_and_downloaded, file, peer_id)
        assert not message.event

    def test_last_message(self, tracker_logic_init_data):
        file, clock, peer_id, logic, uploaded_and_downloaded = tracker_logic_init_data
        logic.update(0, 0)
        logic.update(0, 0, response=TrackerResponse(0, []))
        message = logic.update(*uploaded_and_downloaded, downloading=False)
        check_message(message, uploaded_and_downloaded, file, peer_id)
        assert Event.Complete == message.event

    def test_with_error(self, tracker_logic_init_data):
        file, clock, peer_id, logic, uploaded_and_downloaded = tracker_logic_init_data
        logic.update(0, 0)
        for error_number in range(MAX_FAILURES):
            logic.update(0, 0, connection_error=True)
            clock.current_time += 2**error_number * 5
            message = logic.update(*uploaded_and_downloaded)
            check_message(message, uploaded_and_downloaded, file, peer_id)
            assert Event.Start == message.event
        with raises(TrackerFailedTooManyTimesError):
            logic.update(0, 0, connection_error=True)
