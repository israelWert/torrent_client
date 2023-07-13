from torrent_client.peer.p2p_net.tcp_client import AbstractTcpClient


class FakeTcpClient(AbstractTcpClient):

    def __init__(self):
        self.data = b""
        self.send_list = []
        self.response_size = 1

    def close(self):
        pass

    async def init(self):
        pass

    async def recv(self, size: int) -> bytes:
        self.data, result = self.data[self.response_size:], self.data[:self.response_size]
        return result

    def send(self, payload: bytes) -> None:
        self.send_list.append(payload)
