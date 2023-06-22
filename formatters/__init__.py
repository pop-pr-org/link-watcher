#!/usr/bin/env python
# coding=utf-8
from abc import ABC, abstractmethod


class Hosts(ABC):
    @abstractmethod
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
        raise NotImplementedError("Subclass must implement this method")
