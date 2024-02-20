#!/usr/bin/env python
# coding=utf-8
from abc import ABC, abstractmethod
from logging import getLogger
from json import dump

from config import IRM_HOST, LINKS_INFO_FILE, IRM_TOKEN
from utils import json_reader
from formatters.hosts import Hosts

logger = getLogger("watcher")


class Irm(ABC):
    @abstractmethod
    def connect(self, url: str, token: str):
        """
        Connect to IRM and return the API object
        """
        pass

    @abstractmethod
    def get_hosts_speed(self, irm_api) -> dict:
        """
        Get hosts info from IRM
        Infos are:
        - Hostname
        - Speed (in bits)

        Should return a dict with the following format:

        {
            "LINKS": [
                {
                    "LINK_SPEED": speed in bits,
                    "LINK_NAME": name of the link in your IRM
                },
            ]
        }
        """
        pass

    def choose_link_config_source(self, args_file: str, output_path) -> dict:
        """
        If an input file is given, use it.
        Else, get the info from IRM.
        """
        if args_file:
            logger.info("retrieving info from json file at: %s", args_file)
            hosts_config = Hosts.format_links(json_reader(args_file))
        else:
            logger.info("retrieving info from IRM at: %s", IRM_HOST)
            hosts_config = Hosts.format_links(self.extract_hosts_info())
            with open(LINKS_INFO_FILE, "w+") as outfile:
                logger.info("droppping hosts.json at: %s", output_path)
                dump(hosts_config, outfile, indent=6)
        return hosts_config

    def extract_hosts_info(self) -> dict:
        """
        Extracts hosts info from IRM
        Has to return a dict with the following format:
        {
            "LINKS": [
                {
                    "LINK_SPEED": speed in bits,
                    "LINK_NAME": name of the link in your IRM
                },
            ]
        }
        """
        netbox_api = self.connect(IRM_HOST, IRM_TOKEN)
        hosts_info = self.get_hosts_speed(netbox_api)
        return hosts_info
