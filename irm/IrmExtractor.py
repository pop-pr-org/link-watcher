#!/usr/bin/env python
# coding=utf-8
from irm import Irm

import pynetbox

from pprint import pprint
from logging import getLogger
from config import LOGGER_NAME, IGNORE_LIST


logger = getLogger(__name__)


class IrmExtractor(Irm):
    def connect(self, url: str, token: str) -> pynetbox.api:
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

    def get_hosts_speed(self, irm_api: pynetbox.api) -> dict:
        """
        Get hosts info from Netbox
        Infos are:
        - Hostname
        - Speed (in bits)

        Should return a dict with the following format:

        {
            "Link1"(link name in your IRM): {
                    "LINK_SPEED": speed in bits,
                },
            "Link2": {
                    "LINK_SPEED": speed in bits,
                },
            ...
            LinkN: {
                    "LINK_SPEED": speed in bits,
                },
        }
        """

        ignore_list = IGNORE_LIST

        # extract name and speed from netbox from every circuit
        all_sites = irm_api.dcim.sites.all()
        all_sites = list(all_sites)
        logger.info("Got %d sites from Netbox", len(all_sites))

        # empty dict to store the info
        site_circuits = {}

        # retrieve all circuits from Netbox with type RNP and status active
        circuit_rnp = irm_api.circuits.circuit_types.get(slug="rnp")
        circuits = irm_api.circuits.circuits.filter(
            type_id=circuit_rnp.id, status="active"
        )

        # for each circuit, get the site name and the speed
        for circuit in circuits:
            # but this change will break the alerting system
            site_name = circuit.termination_z.site.slug
            circuit_speed = circuit.commit_rate * 1000

            # ignore sites in the ignore list
            if site_name in ignore_list:
                continue

            site_circuits[str(site_name)] = {"LINK_SPEED": circuit_speed}

        logger.info("Got %d circuits from Netbox", len(site_circuits))

        return site_circuits
