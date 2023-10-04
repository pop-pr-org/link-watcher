#!/usr/bin/env python
# coding=utf-8

from pprint import pprint
from datetime import datetime, timedelta
from pytz import timezone as tz
from logging import getLogger
from os import environ

from tsdb import Tsdb
from influxdb import InfluxDBClient
from config import LOGGER_NAME, OUTPUT_TIMEZONE, TSDB_TIME_FORMAT

logger = getLogger(LOGGER_NAME)


class TsdbExtractor(Tsdb):
    def connect(self, host, port, username, password, database):
        """
        Connect to TSDB and return the client object
        """
        auth = {
            "username": username,
            "password": password,
            "database": database,
            "host": host,
            "port": port,
        }
        try:
            client = InfluxDBClient(**auth, retries=2, timeout=10)
        except Exception as e:
            logger.error("error connecting to influxdb: %s", e)
            return exit(1)
        return client

    def query_iface_traffic(
        link_configs: dict, iface: str, db_client: InfluxDBClient
    ) -> list:
        """
        query TSDB for a given host interface (rx|tx) traffic with a set time range

        Params:
        - link_configs: dict with the following format:
            {
                "LINKS": [
                    {
                        "LINK_SPEED": speed in bits,
                        "LINK_NAME": name of the link in your IRM
                    },
                ]
            }
        - iface: interface name (rx|tx)
        - db_client: tsdb client object

        Returns:

        Should return a list of dicts with AT LEAST these key:value pairs:

        [
            {
                "time": timestamp,
                "value": value in bits
            },
        ]

        If no data is found, returns an empty list

        """
        data = []
        return data
