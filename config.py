#!/usr/bin/env python
# coding=utf-8

from dotenv import load_dotenv
from os import getenv

load_dotenv()

# WATCHER
LINKS_INFO_FILE = getenv("LINKS_INFO_FILE")
WORK_HOUR_BEGIN = int(getenv("WORK_HOUR_BEGIN"))  # hour to start the query
WORK_HOUR_END = int(getenv("WORK_HOUR_END"))  # hour to end the query
QUERY_DATE_BEGIN = getenv(
    "QUERY_DATE_BEGIN"
)  # (will be overwritten throughout the script) timestamp to start the query
QUERY_DATE_END = getenv(
    "QUERY_DATE_END"
)  # (will be overwritten throughout the script) timestamp to end the query
DEFAULT_MAX_TRAFFIC_PERCENTAGE = float(getenv("DEFAULT_MAX_TRAFFIC_PERCENTAGE"))
DEFAULT_LINK_HISTERESYS = float(getenv("DEFAULT_LINK_HISTERESYS"))  # in percentage
TIME_THRESHOLD = int(getenv("TIME_THRESHOLD"))  # in minutes
IGNORE_LIST = getenv("IGNORE_LIST").split(",")

OUTPUT_INDENT_LEVEL = int(getenv("OUTPUT_IDENT_LEVEL"))
REPORT_OUTPUT_PATH = getenv("REPORT_OUTPUT_PATH")
OUTPUT_TIMEZONE = getenv("OUTPUT_TIMEZONE")
PERCENTILE = getenv("PERCENTILE")
# WATCHER

# TSDB
TSDB_AUTH = {
    "host": getenv("TSDB_HOST"),
    "port": getenv("TSDB_PORT"),
    "username": getenv("TSDB_USER"),
    "password": getenv("TSDB_PASS"),
    "database": getenv("TSDB_DB"),
}
TSDB_TIME_FORMAT = str(getenv("TSDB_TIME_FORMAT"))
TSDB_TIMEZONE = getenv("TSDB_TIMEZONE")
# TSDB

# IRM
IRM_HOST = getenv("IRM_HOST")
IRM_TOKEN = getenv("IRM_TOKEN")
# IRM

# REST API
API_HOST = getenv("API_HOST")
API_USER = getenv("API_USER")
API_PASS = getenv("API_PASS")
# REST API

# ALERT
ALERTA_IP = getenv("ALERTA_IP")
ALERTA_URL = getenv("ALERTA_URL")
EMAILS_TO_ALERT = getenv("EMAILS_TO_ALERT").split(",")
TELEGRAM_CHAT_IDS = getenv("TELEGRAM_CHAT_IDS").split(",")
LINKS_INFO_FILE = getenv("LINKS_INFO_FILE")
MAX_PERCENTILE_REPORTS = int(getenv("MAX_PERCENTILE_REPORTS"))
# ALERT

# LOGGING
LOGGING_LEVEL = getenv("LOGGING_LEVEL")  # [DEBUG, INFO, WARNING, ERROR, CRITICAL]
MAX_LOG_SIZE = int(getenv("MAX_LOG_SIZE"))  # in MB
BACKUP_COUNT = int(getenv("BACKUP_COUNT"))  # number of log files to keep
LOG_FILE = getenv("LOG_FILE")  # path to log file inside the container
LOGGER_NAME = getenv("LOGGER_NAME")
# LOGGING
