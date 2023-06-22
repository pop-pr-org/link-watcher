#!/usr/bin/env python
# coding=utf-8

from abc import ABC, abstractmethod


class Alert(ABC):
    @abstractmethod
    def __init__(self, name, alert_type, condition):
        pass

    @abstractmethod
    def send_alert(self, message):
        pass
