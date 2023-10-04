#!/usr/bin/env python
# coding=utf-8
from irm import Irm

import pynetbox

from pprint import pprint
from logging import getLogger
from config import LOGGER_NAME


logger = getLogger(LOGGER_NAME)


class IrmExtractor(Irm):
    def connect(url: str, token: str) -> pynetbox.api:
        """
        Connect to Netbox
        Should return a pynetbox.api object
        """
        try:
            nb = pynetbox.api(url, token=token)
            logger.info("Connected to Netbox")
        except Exception as e:
            logger.error("Error connecting to Netbox: %s", e)
            raise e
        return nb

    def get_hosts_speed(irm_api: pynetbox.api) -> dict:
        """
        Get hosts info from Netbox
        Infos are:
        - Hostname
        - Speed (in bits)

        Should return a dict with the following format:

        {
            "LINKS": [
                {
                    "LINK_SPEED": speed in bits,
                    "LINK_NAME": name of the link in your IRM
                }
            ]
        }
        """
        hosts_speed = {}

        return hosts_speed
