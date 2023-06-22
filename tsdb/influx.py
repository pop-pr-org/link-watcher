#!/usr/bin/env python
# coding=utf-8

from pprint import pprint
from tsdb import TSDB
from influxdb import InfluxDBClient
from logging import getLogger

from config import TIME_RANGE, LOGGER_NAME

logger = getLogger(LOGGER_NAME)


class INFLUX(TSDB):
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
        # querying influxdb
        try:
            tag = db_client.query(
                'SELECT * from "check_iface_traffic" WHERE "time" > {} AND  \
                "hostname" = \'{}\' AND "metric" = \'iface-traffic{}\''.format(
                    TIME_RANGE, link_configs["LINK_NAME"], iface
                )
            )
        except Exception as e:
            logger.error("error querying influxdb: %s", e)
            return []  # returning empty list

        # extracting points
        tag = tag.get_points()

        # data needs to be a list of dicts
        # with at least 'time' and 'value' keys
        # removing None values
        data = [t for t in tag if t["value"] is not None]

        return data
