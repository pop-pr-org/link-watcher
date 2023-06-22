#!/usr/bin/env python
# coding=utf-8

import argparse
import zulu
import logging
import requests
import json


from pprint import pprint
from datetime import datetime
from pathlib import Path
from requests.auth import HTTPBasicAuth
from os.path import join

from utils import save_json, json_reader
from logger import init_logging
from tsdb.influx import INFLUX
from formatters.hosts import Hosts
from irm.netbox import Netbox

from config import (
    LOGGER_NAME,
    API_HOST,
    API_USER,
    API_PASS,
    IRM_HOST,
    IRM_TOKEN,
    TSDB_AUTH,
)


# arguments
def process_args():
    parser = argparse.ArgumentParser(
        description="A script to check if the traffic of a given list of links \
        is exceding the configured thresholds.",
        add_help=True,
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        action="store",
        help="json file with the configuration",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./reports/",
        action="store",
        help="path where the json output will be stored",
    )

    parser.add_argument(
        "--alert",
        type=str,
        default="",
        action="store",
        help="If given, ONLY sends the alert",
    )

    args = parser.parse_args()
    return args


init_logging()
logger = logging.getLogger(LOGGER_NAME)


def main():
    logger.info("starting watcher.py")

    # parsing args
    args = process_args()
    logger.info("args used: %s", args)
    output_path = Path(args.output)

    # getting hosts info
    hosts_config = choose_host_config_source(args.file, output_path)
    db_client = INFLUX.connect(INFLUX, **TSDB_AUTH)

    # creating reports dict
    reports = {}
    date = datetime.now().strftime("%d-%m-%y")
    reports["Data"] = date

    # checking each link
    for link_configs in hosts_config["LINKS"]:
        # send_link_to_api(link_configs["LINK_NAME"]) working on it
        check_exceeded_intervals(db_client, reports, link_configs)

    # saving json output
    file_path = create_report_file_name(output_path)
    save_json(reports, file_path)

    logger.info("finished watcher.py")


def choose_host_config_source(args_file: str, output_path) -> dict:
    """
    If an input file is given, use it.
    Else, get the info from IRM.
    """
    if args_file:
        logger.info("retrieving info from json file at: %s", args_file)
        hosts_config = Hosts.format_links(json_reader(args_file))
    else:
        logger.info("retrieving info from IRM at: %s", IRM_HOST)
        hosts_config = Hosts.format_links(extract_hosts_info())
        with open("/tmp/watcher/hosts.json", "w+") as outfile:
            logger.info("droppping hosts.json at: %s", output_path)
            json.dump(hosts_config, outfile, indent=6)
    return hosts_config


def create_report_file_name(output_path: str) -> str:
    """
    Creates the name of the json output file
    Returns the relative path
    """
    today = str(datetime.now().strftime("%d-%m-%y"))
    file_name = "reports_" + today + ".json"
    # creating absolute path
    file_path = join(output_path, file_name)
    return file_path


def extract_hosts_info() -> dict:
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
    netbox_api = Netbox.connect(IRM_HOST, IRM_TOKEN)
    hosts_info = Netbox.get_hosts_speed(netbox_api)
    return hosts_info


def check_interval_size(
    data: dict,
    link_configs: dict,
    reports: dict,
    iface: str,
    i: int,
):
    """
    iterates over the points array checking for exceeded values
    and building the reports dict.

    returns the index of the last point checked
    """

    # if is already the last point of the array, return
    if i >= len(data):
        return len(data)

    interval_counter = len(reports[link_configs["LINK_NAME"]][iface]["intervals"]) + 1

    # formatting start time display
    # it has to be the time of the previous point 'cause if the current point is above limit,
    # it means that the previous point was the start of the interval
    point_dt = zulu.parse(data[i - 1]["time"])
    time_begin = point_dt.subtract(hours=3).format("%d/%m/%y-%H:%M:%S")

    # extracting values for better readability
    max_value = data[i]["value"] * 8  # max value of the interval in bits
    min_value = max_value  # min value of the interval in bits
    limit_speed = (
        link_configs["LINK_SPEED"] * link_configs["LINK_MAX_TRAFFIC_PERCENTAGE"]
    )
    limit_speed_histeresys = limit_speed * link_configs["LINK_HISTERESYS"]
    limit_speed_accounting_for_histeresys = limit_speed - limit_speed_histeresys

    # iterates checking interval size
    exceeded_points = 0
    while (i < len(data)) and (
        data[i]["value"] * 8 >= limit_speed_accounting_for_histeresys
    ):
        current_point_value = data[i]["value"] * 8

        # checking for max value
        if current_point_value > max_value:
            max_value = current_point_value
        # checking for min value
        if current_point_value < min_value:
            min_value = current_point_value

        exceeded_points += 1
        # iterate
        i += 1

    exceeded_time = exceeded_points * 5  # in minutes

    # if interval not exceeded, returns the last index checked
    if exceeded_points == 0:
        return i

    # if got to the end of the array, returns the last index
    if i >= len(data):
        i -= 1

    # formatting end time display
    point_dt = zulu.parse(data[i]["time"])
    time_end = point_dt.subtract(hours=3).format("%d/%m/%y-%H:%M:%S")

    # Mean value of interval (in bytes)
    mean_value = round((min_value + max_value) / 2, 1)
    # if mean value exceeds limit speed, removes the interval
    # this means that this particular interval has a point
    # where the link was down and got back up causing a spike
    if (mean_value >= 6 * limit_speed) or ("e" in str(mean_value)):
        logger.info(
            "ignoring interval beetwen %s and %s (probably link was down)",
            time_begin,
            time_end,
        )
        return i
    # setting max and min values to bytes
    max_value = round(max_value, 1)
    min_value = round(min_value, 1)

    # adding interval to report
    add_interval_to_report(
        reports[link_configs["LINK_NAME"]][iface],
        time_begin,
        time_end,
        interval_counter,
        exceeded_time,
        mean_value,
        max_value,
        min_value,
    )

    #
    link_configs_api_info = {
        "LINK_NAME": link_configs["LINK_NAME"],
        "LINK_SPEED": link_configs["LINK_SPEED"],
        "LINK_MAX_TRAFFIC_PERCENTAGE": link_configs["LINK_MAX_TRAFFIC_PERCENTAGE"],
        "LINK_HISTERESYS": link_configs["LINK_HISTERESYS"],
    }

    send_interval_to_api(
        link_configs_api_info,
        iface,
        time_begin,
        time_end,
        exceeded_time,
        mean_value,
        max_value,
        min_value,
    )
    return i


def send_link_to_api(link_name):
    """
    sends the link to the api
    """
    # sending link to api
    try:
        url = API_HOST + "watcher/"
        data = {"slug": link_name, "owner": API_USER}
        response = requests.post(
            url,
            data=json.dumps(data),
            auth=HTTPBasicAuth(API_USER, API_PASS),
            headers={"Content-Type": "application/json"},
            timeout=3,
        )
        logger.info("link %s sent to api", link_name)
        logger.info("response: %s", response.text)
    except Exception as e:
        logger.error("error sending link to api: %s", e)


def send_interval_to_api(
    current_link_configs,
    iface,
    time_begin,
    time_end,
    exceeded_time,
    mean_value,
    max_value,
    min_value,
):
    """
    sends the interval to the api
    """
    # sending interval to api
    try:
        url = API_HOST + "watcher/interval/"
        time_begin = datetime.strptime(time_begin, "%d/%m/%y-%H:%M:%S")
        time_begin = time_begin.strftime("%Y-%m-%dT%H:%M:%SZ")
        time_end = datetime.strptime(time_end, "%d/%m/%y-%H:%M:%S")
        time_end = time_end.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = {
            "link_slug": current_link_configs["LINK_NAME"],
            "speed": current_link_configs["LINK_SPEED"],
            "speed_limit": current_link_configs["LINK_MAX_TRAFFIC_PERCENTAGE"],
            "limit_histeresys": current_link_configs["LINK_HISTERESYS"],
            "interface": iface,
            "date_begin": time_begin,
            "date_end": time_end,
            "exceeded_time": exceeded_time,
            "max_value": max_value,
            "mean_value": mean_value,
            "min_value": min_value,
            "owner": 1,  # 1 is the id of the 'root' user
        }
        r = requests.post(
            url,
            json=data,
            auth=HTTPBasicAuth(API_USER, API_PASS),
            headers={"Content-Type": "application/json"},
            timeout=3,
        )
        logger.info("api response: %s and response %s", r.reason, r.text)
    except requests.exceptions.RequestException as e:
        logger.error("error adding interval to api: %s", e)


def add_interval_to_report(
    link_iface_report: dict,
    time_begin: str,
    time_end: str,
    interval_counter: int,
    exceeded_time: int,
    mean_value: float,
    max_value: float,
    min_value: float,
):
    """
    adds an interval to the report dict
    """

    # register Interval start
    link_iface_report["intervals"].update({interval_counter: {"begin": time_begin}})
    # Interval end
    link_iface_report["intervals"][interval_counter].update({"end": time_end})

    # Exceeded time
    link_iface_report["intervals"][interval_counter].update(
        {"exceeded_time": str(exceeded_time) + "min"}
    )

    # max value
    link_iface_report["intervals"][interval_counter].update(
        {"max_value": str(max_value)}
    )

    # mean value
    link_iface_report["intervals"][interval_counter].update(
        {"mean_value": str(mean_value)}
    )

    # min value
    link_iface_report["intervals"][interval_counter].update(
        {"min_value": str(min_value)}
    )

    # total exceeded time
    link_iface_report["total_exceeded"] += exceeded_time


def check_exceeded_intervals(db_client, reports: dict, link_configs: dict):
    """
    checks if the given link exceeded its traffic limits
    """

    # if link already in reports, exits
    if link_configs["LINK_NAME"] in reports:
        logger.error("link %s is duplicated", link_configs["LINK_NAME"])
        exit(1)

    # initializing reports
    reports[link_configs["LINK_NAME"]] = {
        "rx": {"total_exceeded": 0, "intervals": {}},
        "tx": {"total_exceeded": 0, "intervals": {}},
    }

    # queries for rx and tx
    logger.info("checking ifaces for %s", link_configs["LINK_NAME"])

    data = INFLUX.query_iface_traffic(link_configs, "rx", db_client)
    check_link_data(data, reports, link_configs, "rx")

    data = INFLUX.query_iface_traffic(link_configs, "tx", db_client)
    check_link_data(data, reports, link_configs, "tx")

    # send_api_request(link_configs, reports[link_configs["LINK_NAME"]])


def check_link_data(data: list[dict], reports: dict, link_configs: dict, iface: str):
    """
    checks if the given link exceeded its traffic limits

    updates the report dict
    """

    logger.info("checking collected data for %s:%s", link_configs["LINK_NAME"], iface)

    # if no data, skips
    if len(data) == 0:
        logger.warning("no data for %s:%s", link_configs["LINK_NAME"], iface)
        reports[link_configs["LINK_NAME"]] = "No data"
        return

    # iterates over all points
    i = 0
    while i < len(data):
        traffic_value_in_bits = data[i]["value"] * 8
        traffic_limit_in_bits = (
            link_configs["LINK_SPEED"] * link_configs["LINK_MAX_TRAFFIC_PERCENTAGE"]
        )

        # if exceeds limit: checks how much time it exceeded
        if traffic_value_in_bits >= traffic_limit_in_bits:
            i = check_interval_size(
                data,
                link_configs,
                reports,
                iface,
                i + 1,
            )
        # while iterating
        i += 1


def send_api_request(link_configs: dict, link_report: dict):
    """
    sends the reports to the api
    """
    link_name = link_configs["LINK_NAME"]
    logger.info("sending reports to api for %s", link_name)


if __name__ == "__main__":
    main()
