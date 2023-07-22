from typing import List, Optional

from torrent_client.download.file_loading.file_loader import FileLoader
from torrent_client.download.part import Part
from torrent_client.download.test.fakes.fake_os_wrapper import FakeOsWrapper
from torrent_client.torrent_file.file_to_download import FileToDownload


def create_parts(start_part: int, file_length: int, piece_size: int) -> tuple[FileLoader, List[Part]]:
    f = FileLoader(FileToDownload(file_length, []), FakeOsWrapper())
    parts = f.create_file_parts(start_part, piece_size)
    return f, parts


def check_fist_part(file: FileLoader,
                    first_part: Part,
                    start_part_size: int,
                    expected_start_part_size: Optional[int] = None) -> None:
    first_part_check_size = expected_start_part_size if expected_start_part_size else start_part_size
    assert first_part == Part(file, first_part_check_size, 0)


def check_last_part(file: FileLoader,
                    file_length: int,
                    last_part: Part,
                    end_part_size: int) -> None:
    assert last_part == Part(file, end_part_size, file_length - end_part_size)


def check_middle_parts(file: FileLoader,
                       piece_size: int,
                       start_part_size: int,
                       parts: List[Part]) -> None:
    rest_parts = parts[1:-1]
    for part in rest_parts:
        begins = piece_size * rest_parts.index(part) + start_part_size
        assert part == Part(file, piece_size, begins)


def use_file_case_parts(file_length: int,
                        start_part_size: int,
                        end_part_size: int,
                        piece_size: int,
                        num_of_parts: int,
                        expected_start_part_size: Optional[int] = None):
    file, parts = create_parts(start_part_size, file_length, piece_size)
    assert len(parts) == num_of_parts
    if num_of_parts == 0:
        return
    check_fist_part(file, parts[0], start_part_size, expected_start_part_size)
    if num_of_parts == 1:
        return
    check_last_part(file, file_length, parts[-1], end_part_size)
    check_middle_parts(file, piece_size, start_part_size, parts)


class TestUnitFileLoaderGetParts:
    def test_no_split_piece(self):
        use_file_case_parts(
            file_length=100,
            start_part_size=10,
            end_part_size=10,
            piece_size=10,
            num_of_parts=10
        )

    def test_start_part_split_piece(self):
        use_file_case_parts(
            file_length=103,
            start_part_size=3,
            end_part_size=10,
            piece_size=10,
            num_of_parts=11
        )

    def test_end_part_split_piece(self):
        use_file_case_parts(
            file_length=103,
            start_part_size=10,
            end_part_size=3,
            piece_size=10,
            num_of_parts=11
        )

    def test_start_and_end_part_split_piece(self):
        use_file_case_parts(
            file_length=100,
            start_part_size=3,
            end_part_size=7,
            piece_size=10,
            num_of_parts=11
        )

    def test_one_split_piece(self):
        use_file_case_parts(
            file_length=3,
            start_part_size=10,
            end_part_size=0,
            piece_size=10,
            num_of_parts=1,
            expected_start_part_size=3
        )
