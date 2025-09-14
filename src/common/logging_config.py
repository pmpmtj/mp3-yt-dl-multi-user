import logging
import logging.config
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'rotating_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'app.log'),
            'maxBytes': 1024 * 1024,  # 1MB
            'backupCount': 5,
            'formatter': 'standard',
            'mode': 'a',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'error.log'),
            'maxBytes': 512 * 1024,  # 512KB
            'backupCount': 3,
            'formatter': 'standard',
            'mode': 'a',
            'level': 'ERROR',
        },
    },

    'root': {
        'handlers': ['console', 'rotating_file', 'error_file'],
        'level': 'INFO',
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)