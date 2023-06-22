#!/usr/bin/env python
# coding=utf-8

from pprint import pprint

from config import LOGGER_NAME, DEFAULT_LINK_HISTERESYS, DEFAULT_MAX_TRAFFIC_PERCENTAGE

from logging import getLogger

logger = getLogger(LOGGER_NAME)


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
        {
            "LINK_SPEED": speed in bits,
            "LINK_NAME": name of the link in your IRM
            "LINK_MAX_TRAFFIC_PERCENTAGE": max traffic percentage for the link
            "LINK_HISTERESYS": histeresys as percentage for the link
        }
        """
        host_links = hosts["LINKS"]
        for link in host_links:
            # checking if link has a max traffic percentage key
            if "MAX_TRAFFIC_PERCENTAGE" not in host_links:
                logger.debug("Setting max traffic percentage for %s", link["LINK_NAME"])
                link["LINK_MAX_TRAFFIC_PERCENTAGE"] = DEFAULT_MAX_TRAFFIC_PERCENTAGE

            # checking if link has a histerysis key
            if "LINK_HISTERESYS" not in host_links:
                logger.debug("Setting histeresys for %s", link["LINK_NAME"])
                link["LINK_HISTERESYS"] = DEFAULT_LINK_HISTERESYS

        return hosts
