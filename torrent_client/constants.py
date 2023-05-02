import os

root_path = os.path.dirname(os.path.abspath(__file__))
torrent_files_path = os.path.join(root_path, "test\\data")
input_files_path = os.path.join(root_path, "input_files")

MAIN_LOG_FILE = os.path.join(root_path, "main.log")
TORRENT_FILE_LOG_FILE = os.path.join(root_path, r"torrent_file\torrent_file.log")
TRACKER_LOG_FILE = os.path.join(root_path, r"tracker\tracker.log")
