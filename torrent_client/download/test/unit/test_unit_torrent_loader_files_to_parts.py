import pytest

from torrent_client.download.file_loading.torrent_loader import TorrentLoader
from torrent_client.download.part import Part
from torrent_client.download.test.fakes.fake_file_loader import FakeFileLoader


class TestUnitTorrentLoaderFileToParts:
    def test_one_file_one_part_full_pieces(self):
        file = FakeFileLoader(
                [
                    Part(None, 10, 0),
                ]
        )

        t_loader = TorrentLoader(files_loaders=[file])
        pieces = t_loader.get_files_parts_in_pieces(10)
        assert len(pieces) == 1
        assert isinstance(pieces[0], list)
        assert file.start_part_size == 10
        assert file.normal_part_size == 10

    @pytest.mark.parametrize("number_of_parts", [1, 2, 3])
    def test_one_file_combine_n_to_piece(self, number_of_parts):
        piece_size = 6
        part_size = piece_size//number_of_parts
        file = FakeFileLoader(
            [
                Part(None, part_size, part_ind*part_size) for part_ind in range(number_of_parts)
            ]
        )
        t_loader = TorrentLoader(files_loaders=[file])
        pieces = t_loader.get_files_parts_in_pieces(piece_size)
        assert len(pieces) == 1
        assert isinstance(pieces[0], list)
        assert file.start_part_size == piece_size
        assert file.normal_part_size == piece_size
        assert sum(piece.size for piece in pieces[0]) == piece_size

    @pytest.mark.parametrize("number_of_files", [1, 2, 3])
    def test_combine_n_files_one_part(self, number_of_files: int):
        piece_size = 6
        block_size = piece_size//number_of_files
        files = [FakeFileLoader([Part(None, block_size, file_ind*block_size)]) for file_ind in range(number_of_files)]
        t_loader = TorrentLoader(files_loaders=files)
        pieces = t_loader.get_files_parts_in_pieces(piece_size)
        assert len(pieces) == 1
        assert isinstance(pieces[0], list)
        for ind, file in enumerate(files):
            assert file.start_part_size == piece_size-ind*block_size
            assert file.normal_part_size == piece_size


    def test_half_part_at_end(self):
        piece_size = 6
        number_of_blocks = 3
        block_size = piece_size//2
        file = FakeFileLoader(
            [
                Part(None, block_size, block_ind*block_size) for block_ind in range(number_of_blocks)
            ]
        )
        t_loader = TorrentLoader(files_loaders=[file])
        pieces = t_loader.get_files_parts_in_pieces(piece_size)
        assert len(pieces) == 2
        assert isinstance(pieces[0], list)
        assert isinstance(pieces[1], list)
        assert sum(part.size for part in pieces[0]) == piece_size
        assert sum(piece.size for piece in pieces[1]) == piece_size/2


