#!/usr/bin/env python
# coding=utf-8

from dotenv import load_dotenv
from os import getenv

load_dotenv()


TSDB_AUTH = {
    "host": getenv("TSDB_HOST"),
    "port": getenv("TSDB_PORT"),
    "username": getenv("TSDB_USER"),
    "password": getenv("TSDB_PASS"),
    "database": getenv("TSDB_DB"),
}
TSDB_TIME_FORMAT = str(getenv("TSDB_TIME_FORMAT"))


# NETBOX
IRM_HOST = getenv("IRM_HOST")
IRM_TOKEN = getenv("IRM_TOKEN")
# NETBOX
# WATCHER
HOSTS_INFO_FILE = getenv("HOSTS_INFO_FILE")
TIME_BEGIN = int(getenv("TIME_BEGIN"))  # hour to start the query
TIME_END = int(getenv("TIME_END"))  # hour to end the query
QUERY_BEGIN = getenv(
    "QUERY_BEGIN"
)  # (will be overwritten throughout the script) timestamp to start the query
QUERY_END = getenv(
    "QUERY_END"
)  # (will be overwritten throughout the script) timestamp to end the query
DEFAULT_MAX_TRAFFIC_PERCENTAGE = float(getenv("DEFAULT_MAX_TRAFFIC_PERCENTAGE"))
DEFAULT_LINK_HISTERESYS = float(getenv("DEFAULT_LINK_HISTERESYS"))  # in percentage
TIME_THRESHOLD = int(getenv("TIME_THRESHOLD"))  # in minutes
IGNORE_LIST = getenv("IGNORE_LIST").split(",")

OUTPUT_INDENT_LEVEL = int(getenv("OUTPUT_IDENT_LEVEL"))
REPORT_OUTPUT_PATH = getenv("REPORT_OUTPUT_PATH")
# WATCHER

# REST API
API_HOST = getenv("API_HOST")
API_USER = getenv("API_USER")
API_PASS = getenv("API_PASS")
# REST API


# ALERT
ALERTA_IP = getenv("ALERTA_IP")
ALERTA_URL = getenv("ALERTA_URL")
EMAILS_TO_ALERT = getenv("EMAILS_TO_ALERT").split(",")
# ALERT

# LOGGING
LOGGING_LEVEL = getenv("LOGGING_LEVEL")  # [DEBUG, INFO, WARNING, ERROR, CRITICAL]
MAX_LOG_SIZE = int(getenv("MAX_LOG_SIZE"))  # in MB
BACKUP_COUNT = int(getenv("BACKUP_COUNT"))  # number of log files to keep
LOG_FILE = getenv("LOG_FILE")  # path to log file inside the container
LOGGER_NAME = getenv("LOGGER_NAME")
# LOGGING
