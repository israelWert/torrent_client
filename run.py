from torrent_client import client


if __name__ == "__main__":
    c = client.Client("1.torrent")
    file = c.download()
