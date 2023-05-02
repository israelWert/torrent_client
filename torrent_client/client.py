import logging

from torrent_client.torrent_file.decoder import AbstractDecoder, Decoder
from torrent_client import log_config

from torrent_client.torrent_file.file import File
logger = logging.getLogger(__name__)


class Client:
    def __init__(self, file_name=None, decoder: AbstractDecoder = None):
        self.file_name = file_name
        self.decoder = decoder if decoder else Decoder(file_name)

    def download(self,):
        logger.info("************* start download *************")
        file = self.decoder.decode()
        logger.info(f"the file {self.file_name} was decoded successfully")
        logger.debug(f"decoded file: {file}")
        logger.info("************* end client *************")
        return file


