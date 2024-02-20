#!/usr/bin/env python
# coding=utf-8

import argparse
import zulu
import logging
import requests
import json


from pprint import pprint
from datetime import datetime, timedelta
from pytz import timezone as tz
from dateutil import parser
from pathlib import Path
from requests.auth import HTTPBasicAuth
from os.path import join
from os import environ


from utils import save_json, json_reader
from logger import init_logging
from tsdb.TsdbExtractor import TsdbExtractor
from formatters.hosts import Hosts
from irm.IrmExtractor import IrmExtractor
from alert.Alerta import Alerta
from dateManipulator.dateManipulator import DateManipulator
from reportManipulator.reportManipulator import ReportManipulator

from config import (
    LOGGER_NAME,
    API_HOST,
    API_USER,
    API_PASS,
    IRM_HOST,
    IRM_TOKEN,
    TSDB_AUTH,
    TSDB_TIME_FORMAT,
    LINKS_INFO_FILE,
    WORK_HOUR_BEGIN,
    WORK_HOUR_END,
    IGNORE_LIST,
    REPORT_OUTPUT_PATH,
    OUTPUT_TIMEZONE,
    TIME_THRESHOLD,
    LINKS_INFO_FILE,
    PERCENTILE,
)

logger = logging.getLogger("watcher")


def is_alert():
    """
    Checks if the script is running in alert mode
    if so, returns "alert"
    """
    return "alert"


def is_watcher():
    """
    Checks if the script is running in watcher mode
    if so, returns "watcher"
    """
    return "watcher"


# arguments
def process_args():
    # Root parser
    parser = argparse.ArgumentParser(
        description="A script to analyze bandwidth usage of a given list of links\n\
and alert if they exceed the configured thresholds",
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(required=True)

    ## watcher subparser

    ### watcher general flags
    subparser_watcher = subparsers.add_parser(
        "watcher",
        help="Queries the TSDB for the given links and checks if they exceeded the configured thresholds",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparser_watcher.set_defaults(func=is_watcher)

    subparser_watcher.add_argument(
        "-f",
        "--file",
        type=str,
        action="store",
        help="json file with the configuration for each link.",
    )

    subparser_watcher.add_argument(
        "-o",
        "--output",
        type=str,
        default=REPORT_OUTPUT_PATH,
        action="store",
        help="path where the json output will be stored",
    )

    ### watcher date range
    watcher_date_group = subparser_watcher.add_argument_group(
        "date range",
        "Used to specify the date range to be used in the query/alert.\n\
If not given, the default date range will be used(from today {}h to today {}h defined in your .env file).\n\
BOTH FLAGS MUST BE BETWEEN DOUBLE QUOTES".format(
            WORK_HOUR_BEGIN, WORK_HOUR_END
        ),
    )

    watcher_date_group.add_argument(
        "--date-begin",
        type=str,
        action="store",
        default=datetime.now()
        .replace(hour=WORK_HOUR_BEGIN, minute=0, second=0)
        .strftime(TSDB_TIME_FORMAT),
        help='starting date to be used in the query. In the format: "YYYY-MM-DD"',
    )

    watcher_date_group.add_argument(
        "--date-end",
        type=str,
        action="store",
        default=datetime.now()
        .replace(hour=WORK_HOUR_END, minute=0, second=0)
        .strftime(TSDB_TIME_FORMAT),
        help='Ending date to be used in the query. In the format: "YYYY-MM-DD"',
    )

    ## alert subparser
    subparser_alert = subparsers.add_parser(
        "alert",
        help="Checks the reports created by watcher mode for the given links and alerts if they exceeded the configured thresholds",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparser_alert.set_defaults(func=is_alert)

    ### alert general flags
    subparser_alert.add_argument(
        "-d",
        "--directory",
        action="store",
        type=str,
        help="Directory where the reports are stored (alert mode will search for the reports in this directory).\
Default: {}\n\
Can be changed in your .env file".format(
            REPORT_OUTPUT_PATH
        ),
        default=REPORT_OUTPUT_PATH,
    )

    subparser_alert.add_argument(
        "-f",
        "--file",
        type=str,
        action="store",
        help='file containing the links info. Default: "{}\n"'.format(LINKS_INFO_FILE),
        default=LINKS_INFO_FILE,
    )

    subparser_alert.add_argument(
        "--time-threshold",
        action="store",
        type=int,
        help="Time(in minutes) threshold for a given link to be alerted. Default: {}\n\
Example: If a certain link summed up to {} or more minutes above the limit, in the given time range: \
this link will be added to the alert".format(
            TIME_THRESHOLD, TIME_THRESHOLD
        ),
        default=TIME_THRESHOLD,
    )

    ### alert date range
    alert_date_group = subparser_alert.add_argument_group(
        "date range",
        "Used to specify the date range to be used in the alert.\n\
If not given, the default date range will be used: {} to {}(7 days from now)".format(
            (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d"),
        ),
    )

    alert_date_group.add_argument(
        "--date-begin",
        action="store",
        type=str,
        default=(
            datetime.now().replace(hour=0, minute=0, second=0).date()
            - timedelta(days=7)
        ).strftime("%Y-%m-%d"),
        help='Starting date to be used in the alert. In the format: "YYYY-MM-DD"',
    )

    alert_date_group.add_argument(
        "--date-end",
        action="store",
        type=str,
        default=datetime.now()
        .replace(hour=23, minute=59, second=59)
        .date()
        .strftime("%Y-%m-%d"),
        help='Ending date to be used in the alert. In the format: "YYYY-MM-DD"',
    )

    args = parser.parse_args()
    date_manipulator = DateManipulator()
    # checking if the user provided a valid time range
    date_manipulator.check_time_interval(args.date_begin, args.date_end, parser)
    date_manipulator.check_work_hour_interval()
    date_manipulator.check_date_range_dependency(args, parser)
    date_manipulator.set_tsdb_date_interval(args.date_begin, args.date_end)

    return args


def main():
    logger.info("starting watcher.py")

    # parsing args
    args = process_args()
    logger.debug("args used: %s", args)

    ## checking which mode to run
    # choices: alert, watcher
    running_mode = args.func()
    tsdb_extractor = TsdbExtractor()
    date_manipulator = DateManipulator()
    db_client = tsdb_extractor.connect(**TSDB_AUTH)

    match running_mode:
        case "alert":
            logger.info("Starting alert mode")
            alerta = Alerta(
                args.date_begin,
                args.date_end,
                args.time_threshold,
                args.directory,
                args.file,
                db_client,
            )
            alerta.send_alert()
            logger.info("finished alert mode")
        case "watcher":
            logger.info("Starting watcher mode")
            output_path = Path(args.output)

            # checking if wants a range of days to check
            qntd_days_to_check = date_manipulator.extract_qntd_days_to_check()
            logger.info("number of days to check: %s", qntd_days_to_check)

            # getting hosts info
            extractor = IrmExtractor()
            report_manipulator = ReportManipulator()
            links_config = extractor.choose_link_config_source(args.file, output_path)

            # checking each day
            for i in range(0, qntd_days_to_check + 1):
                # changing current report time interval
                current_report_query_date_interval = (
                    date_manipulator.change_tsdb_time_interval(i)
                )
                date_manipulator.set_tsdb_date_interval(
                    current_report_query_date_interval["begin"],
                    current_report_query_date_interval["end"],
                )
                # creating reports dict
                current_report = {}
                current_report["Data"] = date_manipulator.set_report_date()
                # checking each link
                for key, value in links_config.items():
                    if key in IGNORE_LIST:
                        logger.info(
                            "link %s is marked to be ignored, skipping it",
                            key,
                        )
                        continue
                    # send_link_to_api(link["LINK_NAME"])
                    check_exceeded_intervals(db_client, current_report, key, value)
                # saving json output
                file_path = report_manipulator.create_report_file_name(
                    current_report["Data"], output_path
                )
                save_json(current_report, file_path)
                logger.info("finished watcher mode")
        case _:
            logger.error("invalid running mode: %s", running_mode)
            exit(1)

    logger.info("finished watcher.py")
    exit(0)


def check_interval_size(
    data: list[dict],
    current_link_name: str,
    current_link_config: dict,
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

    interval_counter = len(reports[current_link_name][iface]["intervals"]) + 1
    current_timezone_offset = (
        datetime.now(tz(OUTPUT_TIMEZONE)).utcoffset().total_seconds() / 3600
    )

    # formatting start time display
    # it has to be the time of the previous point 'cause if the current point is above limit,
    # it means that the previous point was the start of the interval
    point_dt = zulu.parse(data[i - 1]["time"])
    time_begin = point_dt + timedelta(hours=current_timezone_offset)
    time_begin = time_begin.format("%d/%m/%y-%H:%M:%S")

    # extracting values for better readability
    max_value = data[i]["value"] * 8  # max value of the interval in bits
    min_value = max_value  # min value of the interval in bits
    limit_speed = (
        current_link_config["LINK_SPEED"]
        * current_link_config["LINK_MAX_TRAFFIC_PERCENTAGE"]
    )
    limit_speed_histeresys = limit_speed * current_link_config["LINK_HISTERESYS"]
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
    time_end = point_dt + timedelta(hours=current_timezone_offset)
    time_end = time_end.format("%d/%m/%y-%H:%M:%S")

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

    # adding interval to report
    report_manipulator = ReportManipulator()
    report_manipulator.add_interval_to_report(
        reports[current_link_name][iface],
        time_begin,
        time_end,
        interval_counter,
        exceeded_time,
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


def check_exceeded_intervals(
    db_client, reports: dict, current_link_name: str, current_link_config: dict
):
    """
    checks if the given link exceeded its traffic limits

    updates the report dict
    """

    # if link already in reports, exits
    if current_link_name in reports:
        logger.error("link %s is duplicated", current_link_name)
        exit(1)

    # initializing reports
    reports[current_link_name] = {
        "rx": {
            "total_exceeded": 0,
            "intervals": {},
            "percentile": 0,
        },
        "tx": {
            "total_exceeded": 0,
            "intervals": {},
            "percentile": 0,
        },
    }

    # queries for rx and tx
    logger.info("checking ifaces for %s", current_link_name)
    # querying for rx
    tsdb_extractor = TsdbExtractor()
    data = tsdb_extractor.query_iface_traffic(current_link_name, "rx", db_client)
    reports[current_link_name]["rx"]["percentile"] = (
        tsdb_extractor.query_iface_percentile(
            PERCENTILE,
            environ["QUERY_DATE_BEGIN"],
            environ["QUERY_DATE_END"],
            current_link_name,
            "rx",
            db_client,
        )
    )
    check_link_data(data, reports, current_link_name, current_link_config, "rx")

    # querying for tx
    data = tsdb_extractor.query_iface_traffic(current_link_name, "tx", db_client)
    reports[current_link_name]["tx"]["percentile"] = (
        tsdb_extractor.query_iface_percentile(
            PERCENTILE,
            environ["QUERY_DATE_BEGIN"],
            environ["QUERY_DATE_END"],
            current_link_name,
            "tx",
            db_client,
        )
    )
    check_link_data(data, reports, current_link_name, current_link_config, "tx")

    # send_api_request(current_link, reports[current_link])


def check_link_data(
    data: list[dict],
    reports: dict,
    current_link_name: str,
    current_link_config: dict,
    iface: str,
):
    """
    checks if the given link exceeded its traffic limits

    updates the report dict
    """

    logger.info("checking collected data for %s:%s", current_link_name, iface)

    # if no data, skips
    if len(data) == 0:
        logger.warning("no data for %s:%s", current_link_name, iface)
        return

    # iterates over all points
    i = 0
    while i < len(data):
        traffic_value_in_bits = data[i]["value"] * 8
        traffic_limit_in_bits = (
            current_link_config["LINK_SPEED"]
            * current_link_config["LINK_MAX_TRAFFIC_PERCENTAGE"]
        )

        # if exceeds limit: checks how much time it exceeded
        if traffic_value_in_bits >= traffic_limit_in_bits:
            i = check_interval_size(
                data,
                current_link_name,
                current_link_config,
                reports,
                iface,
                i + 1,
            )
        # while iterating
        i += 1


def send_api_request(current_link: dict, link_report: dict):
    """
    sends the reports to the api
    """
    logger.info("sending reports to api for %s", current_link)


if __name__ == "__main__":
    init_logging()
    main()
