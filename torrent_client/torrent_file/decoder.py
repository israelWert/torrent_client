import logging
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from hashlib import sha1
from typing import List

import bencode

from torrent_client import constants
from torrent_client.torrent_file.exception import TorrentFileNotFound, InvalidTorrentFile
from torrent_client.torrent_file.file_to_download import FileToDownload
from torrent_client.torrent_file.torrent_file import TorrentFile


PIECE_HASH_LENGTH = 20


logger = logging.getLogger(__name__)


class AbstractDecoder(ABC):
    @abstractmethod
    def decode(self) -> TorrentFile:
        pass


class Decoder(AbstractDecoder):
    def __init__(self, file_name):
        self.file_name = file_name

    def decode(self) -> TorrentFile:
        logger.info("start decoding file")
        data = self._read()
        logger.info("file was load into to the code properly")
        bencoded_data = bencode.decode(data)
        logger.info("code was bencod decoded")
        logger.debug(f" the bencoded decoded data : {bencoded_data}")
        encapsulated_data = self._encapsulate(bencoded_data)
        logger.info("file was encapsulated properly")
        logger.debug(f"encapsulated data {encapsulated_data}")
        logger.info("file was decoded successfully")
        return encapsulated_data

    def _read(self) -> bytes:
        path = os.path.join(constants.input_files_path, self.file_name)
        try:
            with open(path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"the file '{self.file_name}' isn't in the input folder")
            raise TorrentFileNotFound

    @staticmethod
    def _decode_pieces(pieces) -> List[bytes]:
        pieces_lst = []
        for index in range(0, len(pieces)-PIECE_HASH_LENGTH+1, PIECE_HASH_LENGTH):
            pieces_lst.append(pieces[index:index+PIECE_HASH_LENGTH])
        return pieces_lst


    @staticmethod
    def _decode_files_to_download(info: OrderedDict) -> List[FileToDownload]:
        files = info.get("files")
        if files:
            decoded_files = []
            for file in files:
                decoded_files.append(FileToDownload(file["length"], file["path"]))
            return decoded_files
        return [FileToDownload(info["length"], [info["name"]])]

    @staticmethod
    def _encapsulate(data: OrderedDict) -> TorrentFile:
        try:
            info = data["info"]
            files = Decoder._decode_files_to_download(info)

            file = TorrentFile(
                announce_list=[lst[0] for lst in data["announce-list"]] if data.get("announce-list") else [data["announce"]],
                name=info["name"],
                piece_length=info["piece length"],
                pieces=Decoder._decode_pieces(info["pieces"]),
                is_single=len(files) == 1,
                files=files,
                info_hash=sha1(bencode.encode(data["info"])).digest(),
                total_size=sum([file.length for file in files])
            )
        except KeyError as e:
            logger.error("torrent file didn't have all it's keys")
            raise InvalidTorrentFile() from e
        return file

