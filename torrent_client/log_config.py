import logging
from logging.config import dictConfig

from torrent_client.constants import MAIN_LOG_FILE, TORRENT_FILE_LOG_FILE, TRACKER_LOG_FILE, SINGLE_PEER_LOG_FILE

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            "format": "%(name)s - %(levelname)s - %(lineno)d %(message)s\t"
        }
    },
    'handlers': {
        'console_warn_handler': {
            'level': logging.WARNING,
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        "error_main_file_handler": {
            "level": logging.ERROR,
            "formatter": "simple",
            "filename": MAIN_LOG_FILE,
            "class": "logging.FileHandler"
        },
        'console_handler': {
            'level': logging.INFO,
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        "main_file_handler": {
            "level": logging.DEBUG,
            "formatter": "simple",
            "filename": MAIN_LOG_FILE,
            "class": "logging.FileHandler"
        },
        "torrent_file_handler": {
            "level": logging.DEBUG,
            "formatter": "simple",
            "filename": TORRENT_FILE_LOG_FILE,
            "class": "logging.FileHandler"
        },
        "tracker_handler": {
            "level": logging.DEBUG,
            "formatter": "simple",
            "filename": TRACKER_LOG_FILE,
            "class": "logging.FileHandler"

        },
        "single_peer_handler": {
            "level": logging.DEBUG,
            "formatter": "simple",
            "filename": SINGLE_PEER_LOG_FILE,
            "class": "logging.FileHandler"

        }
    }
    ,
    'loggers': {
        "torrent_client.client": {
            "level": logging.INFO,
            "handlers": ["main_file_handler", "console_handler"]
        },
        "torrent_client.torrent_file": {
            "level": logging.WARNING,
            "handlers": ["torrent_file_handler", "console_warn_handler", "error_main_file_handler"]
        },
        "torrent_client.tracker": {
            "level": logging.ERROR,
            "handlers": ["tracker_handler", "console_warn_handler", "error_main_file_handler"]
        },
        "torrent_client.tracker.net": {
            "level": logging.ERROR,
            "handlers": ["tracker_handler"]
        },
        "torrent_client.peer.peer": {
            "level": logging.DEBUG,
            "handlers": ["single_peer_handler"]
        }
    },



}

dictConfig(LOGGING_CONFIG)