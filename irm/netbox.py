#!/usr/bin/env python
# coding=utf-8
from irm import Irm

import pynetbox

from pprint import pprint
from logging import getLogger
from config import LOGGER_NAME


logger = getLogger(LOGGER_NAME)


class Netbox(Irm):
    def connect(url: str, token: str) -> pynetbox.api:
        """
        Connect to Netbox
        should return a pynetbox.api object
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

        ignore_list = []  # list of sites to ignore

        # extract name and speed from netbox from every circuit
        all_sites = irm_api.dcim.sites.all()
        all_sites = list(all_sites)
        logger.info("Got %d sites from Netbox", len(all_sites))

        site_circuits = {"LINKS": []}
        # every site may have one or more circuits
        for site in all_sites:
            # get all circuits from the site
            circuits = irm_api.circuits.circuits.filter(
                site_id=site.id, status="active"
            )
            # if there are circuits in the site
            if circuits is not None:
                circuits = list(circuits)  # turn the object into a list
                # for every circuit in the site
                for circuit in circuits:
                    # filter circuits where the type is not "RNP"
                    if circuit.type.name == "RNP":
                        if site.name in ignore_list:
                            continue
                        # get the commit rate of the circuit in bits
                        circuit_speed = circuit.commit_rate * 1000
                        site_circuits["LINKS"].append(
                            {"LINK_SPEED": circuit_speed, "LINK_NAME": site.name}
                        )

        logger.info("Got %d circuits from Netbox", len(site_circuits["LINKS"]))
        return site_circuits
