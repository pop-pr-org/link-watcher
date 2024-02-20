#!/usr/bin/env python
# coding=utf-8

from alert import Alert

from requests import post
from logging import getLogger
from dateutil import parser
from json import dumps

from config import ALERTA_URL, EMAILS_TO_ALERT, TELEGRAM_CHAT_IDS, ALERTA_IP

logger = getLogger(__name__)


class Alerta(Alert):
    """
    Sends an alert to the user
    """

    def send_alert(self):
        message = self.alert_message
        date_begin = parser.parse(self.date_begin).strftime("%d/%m/%y")
        date_end = parser.parse(self.date_end).strftime("%d/%m/%y")
        event = "Links excedendo o limite ({} à {})".format(date_begin, date_end)
        header = {"Content-Type": "application/json"}
        data = {
            "environment": "Default",
            "event": event,
            "resource": ALERTA_IP,
            "origin": "Link Watcher",
            "text": message,
            "severity": "informational",
            "value": "",
            "type": "linkWatcherAlert",
            "service": ["watcherCheck"],
            "group": "watcher",
            "rawData": {
                "contacts": ["email", "telegram"],
                "telegram": TELEGRAM_CHAT_IDS,
                "email": EMAILS_TO_ALERT,
                "sms": [],
                "ticket": [],
                "discord": [],
                "teams": [],
            },
        }

        try:
            r = post(ALERTA_URL, headers=header, data=dumps(data))
            logger.info("alert sent to alerta")
        except Exception as e:
            logger.error("error sending alert to alerta: %s", e)
