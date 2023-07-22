import pytest

from torrent_client.download.piece import Piece


class TestUnitPieceStatus:
    @pytest.mark.asyncio
    async def test_download_piece(self):
        p = Piece([], 0, b"")
        await p.download(b"")
        assert not p.is_available_to_download()

    @pytest.mark.asyncio
    async def test_occupy_piece(self):
        p = Piece([], 0, b"")
        assert p.is_available_to_download()
        p.occupy()
        assert not p.is_available_to_download()
        p.release()
        assert p.is_available_to_download()

