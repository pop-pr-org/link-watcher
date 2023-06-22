#!/usr/bin/env python
# coding=utf-8

import requests
import os
import json

from logging import getLogger
from datetime import datetime

from config import OUTPUT_IDENT_LEVEL, ALERTA_URL, LOGGER_NAME, EMAILS_TO_ALERT

logger = getLogger(LOGGER_NAME)


def save_json(input: dict, output_path: str):
    """
    saves a dict to a json file in the given path
    """
    logger.info("saving json file to %s", output_path)
    # writing report json
    with open(output_path, "w+") as outfile:
        json.dump(input, outfile, indent=OUTPUT_IDENT_LEVEL)


def json_reader(json_file_path: os.path):
    """
    reads a json file and returns a dict with the content
    """
    logger.info("reading json file from %s", json_file_path)
    with open(json_file_path, "r") as f:
        j: dict = json.load(f)
        return j


def send_alert(
    message: str,
    event: str,
    severity: str,  # [major, minor, warning, informational, debug, trace, ok, normal, security, critical, unknown]
):
    """
    sends an email to the user
    """
    header = {"Content-Type": "application/json"}
    data = {
        "environment": "Default",
        "event": event,
        "resource": "<IP do Alerta>",
        "origin": "Link Watcher",
        "text": message,
        "severity": severity,
        "value": "",
        "type": "linkWatcherAlert",
        "service": ["watcherCheck"],
        "group": "watcher",
        "rawData": {
            "contacts": ["email"],
            "telegram": [],
            "email": EMAILS_TO_ALERT,
            "sms": [],
            "ticket": [],
            "discord": [],
            "teams": [],
        },
    }
    try:
        r = requests.post(ALERTA_URL, headers=header, data=json.dumps(data))
        logger.info("alert sent to alerta")
    except Exception as e:
        logger.error("error sending alert to alerta: %s", e)
