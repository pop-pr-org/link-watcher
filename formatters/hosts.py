#!/usr/bin/env python
# coding=utf-8

from pprint import pprint

from config import LOGGER_NAME, DEFAULT_LINK_HISTERESYS, DEFAULT_MAX_TRAFFIC_PERCENTAGE

from logging import getLogger

logger = getLogger(__name__)


class Hosts:
    @staticmethod
    def format_links(hosts: dict) -> dict:
        """
        Format the links in the hosts dict to add default values

        Should only add default values if they are not already present:
        - LINK_MAX_TRAFFIC_PERCENTAGE
        - LINK_HISTERESYS

        Should return the hosts dict

        A link should have the following format:
        "LINK_NAME"(name of the link in your IRM): {
            "LINK_SPEED": speed in bits,
            "LINK_MAX_TRAFFIC_PERCENTAGE": max traffic percentage for the link
            "LINK_HISTERESYS": histeresys as percentage for the link
        }
        """
        logger.info("Formatting links")
        hosts_names = list(hosts.keys())
        for host_name in hosts_names:
            if "LINK_MAX_TRAFFIC_PERCENTAGE" not in hosts[host_name]:
                logger.debug("Adding default max traffic percentage to %s", host_name)
                hosts[host_name][
                    "LINK_MAX_TRAFFIC_PERCENTAGE"
                ] = DEFAULT_MAX_TRAFFIC_PERCENTAGE
            if "LINK_HISTERESYS" not in hosts[host_name]:
                logger.debug("Adding default histeresys to %s", host_name)
                hosts[host_name]["LINK_HISTERESYS"] = DEFAULT_LINK_HISTERESYS
        return hosts
