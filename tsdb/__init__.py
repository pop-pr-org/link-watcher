#!/usr/bin/env python
# coding=utf-8


class Tsdb:
    def connect(self):
        """
        Connect to TSDB and return the client object
        """
        raise (NotImplementedError)

    def query_iface_traffic(link_configs: dict, iface: str, client) -> list:
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
        raise (NotImplementedError)

    def query_iface_percentiles(
        PERCENTILE: str,
        starting_time: str,
        ending_time: str,
        reports: dict,
        current_link_name: dict,
        iface: str,
        db_client,
    ) -> float:
        """
        query TSDB for a given host interface (rx|tx), its

        """
        raise (NotImplementedError)
