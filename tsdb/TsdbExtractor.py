#!/usr/bin/env python
# coding=utf-8

from pprint import pprint
from datetime import datetime, timedelta
from pytz import timezone as tz
from logging import getLogger
from os import environ

from tsdb import Tsdb
from influxdb import InfluxDBClient
from config import LOGGER_NAME, OUTPUT_TIMEZONE, TSDB_TIME_FORMAT, PERCENTILE

logger = getLogger("watcher")


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
        self, current_link_name: str, iface: str, db_client: InfluxDBClient
    ) -> list:
        """
        query TSDB for a given host interface (rx|tx) traffic with a set time range

        Params:
        - current_link_name: current link name
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

    def query_iface_percentile(
        self,
        percentile: str,
        starting_time,
        ending_time,
        current_link_name: str,
        iface: str,
        db_client: InfluxDBClient,
    ):
        """
        query TSDB for a given host interface (rx|tx) percentile of the traffic with a set time range

        Return the percentile value of the traffic for the given time range
        """
        data = []

        return data
