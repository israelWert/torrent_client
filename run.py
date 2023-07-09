from torrent_client import client


if __name__ == "__main__":
    c = client.Client("4.torrent")
    file = c.download()
