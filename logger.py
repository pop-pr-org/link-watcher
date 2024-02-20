#!/usr/bin/env python
# coding=utf-8

from pathlib import Path
from logging.config import dictConfig
from config import LOGGING_LEVEL, MAX_LOG_SIZE, BACKUP_COUNT, LOG_FILE, LOGGER_NAME


def init_logging():
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s - %(message)s (%(funcName)s:%(lineno)s)",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "maxBytes": 1024 * 1024 * MAX_LOG_SIZE,  # MAX_LOG_SIZE MB
                    "backupCount": BACKUP_COUNT,  # mantém os 4 arquivos de log anteriores
                    "filename": LOG_FILE,
                    "formatter": "default",
                },
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "loggers": {
                LOGGER_NAME: {
                    "level": LOGGING_LEVEL,
                    "handlers": ["default", "console"],
                    "propagate": False,
                },
                "root": {"handlers": ["default"], "level": LOGGING_LEVEL},
            },
        }
    )
