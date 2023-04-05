import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List

import bencode

from torrent_client import env
from torrent_client.torrent_file.file import File


PIECE_HASH_LENGTH = 20


class AbstractDecoder(ABC):
    @abstractmethod
    def decode(self, file_name: str) -> File:
        pass


class Decoder(AbstractDecoder):
    @staticmethod
    def _read(file: str) -> bytes:
        path = os.path.join(env.root_path, file)
        with open(path, "rb") as f:
            return f.read()

    @staticmethod
    def _decode_pieces(pieces) -> List[bytes]:
        pieces_lst = []
        for index in range(0, len(pieces)-PIECE_HASH_LENGTH+1, PIECE_HASH_LENGTH):
            pieces_lst.append(pieces[index:index+PIECE_HASH_LENGTH])
        return pieces_lst

    @staticmethod
    def _encapsulate(data: OrderedDict) -> File:
        info = data["info"]
        is_multi_file = info.get("files")

        return File(
            announce_list=data["announce-list"] if data.get("announce-list") else data["announce"],
            name=info["name"],
            piece_length=info["piece length"],
            pieces=Decoder._decode_pieces(info["pieces"]),
            is_single=not is_multi_file,
            files=info.get("files") if is_multi_file else [
                {"length": info["length"], "path": info["name"]}
            ],
        )

    def decode(self, file_name: str) -> File:
        data = self._read(file_name)
        bencoded_data = bencode.decode(data)
        return self._encapsulate(bencoded_data)
