#!/usr/bin/env python
# coding=utf-8

from pprint import pprint
from datetime import datetime, timedelta
from tsdb import Tsdb
from influxdb import InfluxDBClient
from logging import getLogger
from os import environ

from config import LOGGER_NAME

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
        query TSDB for a given host iface traffic with a set time range

        Should return a list of dicts with AT LEAST these key:value pairs:

        [
            {
                "time": timestamp,

                "value": value in bits
            },
        ]

        """

        starting_time = environ["QUERY_BEGIN"]
        starting_time = datetime.strptime(starting_time, "%Y-%m-%d %H:%M:%S")
        # set the time format
        # Influx is using utc so we need to add 3 hours to get the correct time
        # during the report building process we will subtract 3 hours
        starting_time = starting_time + timedelta(hours=3)

        ending_time = environ["QUERY_END"]
        ending_time = datetime.strptime(ending_time, "%Y-%m-%d %H:%M:%S")
        # Influx is using utc so we need to add 3 hours to get the correct time
        # during the report building process we will subtract 3 hours
        ending_time = ending_time + timedelta(hours=3)

        # querying influxdb
        try:
            query = 'SELECT * from "check_iface_traffic" WHERE "time" >= \'{}\' AND "time" <= \'{}\' AND  \
                "hostname" = \'{}\' AND "metric" = \'iface-traffic{}\''.format(
                starting_time, ending_time, link_configs["LINK_NAME"], iface
            )
            tag = db_client.query(query)
        except Exception as e:
            logger.error("error querying influxdb: %s", e)
            return []  # returning empty list

        # extracting points
        tag = tag.get_points()

        # data needs to be a list of dicts
        # with at least 'time' and 'value' keys
        # removing None values
        data = [t for t in tag if t["value"] is not None]
        # pprint(data)

        return data
