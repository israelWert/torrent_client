import os

from torrent_client import env

def read(file_name):
    with open(os.path.join(env.torrent_files_path, file_name) , "rb") as f:
        return f.read()


single_file = read("single_file.torrent")
multi_file = read("multi_file.torrent")

