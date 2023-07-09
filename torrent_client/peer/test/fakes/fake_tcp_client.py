from torrent_client.peer.peer_net.tcp_client import AbstractTcpClient


class FakeTcpClient(AbstractTcpClient):
    def __init__(self):
        self.data = b""
        self.send_list = []

    async def init(self):
        pass

    async def recv(self, size: int) -> bytes:
        self.data, result = self.data[size:], self.data[:size]
        return result

    def send(self, payload: bytes) -> None:
        self.send_list.append(payload)
