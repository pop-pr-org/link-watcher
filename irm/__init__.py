#!/usr/bin/env python
# coding=utf-8
from abc import ABC, abstractmethod


class Irm(ABC):
    @abstractmethod
    def connect(url: str, token: str):
        """
        Connect to IRM and return the API object
        """
        pass

    @abstractmethod
    def get_hosts_speed(irm_api) -> dict:
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
