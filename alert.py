#!/usr/bin/env python
# coding=utf-8

import argparse

from pprint import pprint
from os import listdir, path
from logging import getLogger

from utils import json_reader, send_alert
from config import TIME_THRESHOLD, LOGGER_NAME

logger = getLogger(LOGGER_NAME)


def process_args():
    parser = argparse.ArgumentParser(
        description="a cronjob to be executed every monday, checking if given\
             links have exceeded its traffic limits in the last 7 days",
        add_help=True,
    )

    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        action="store",
        help="directory where the json files are stored",
    )

    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=7,
        action="store",
        help="number of files to be checked",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default="./hosts.json",
        action="store",
        help="json file with the configuration",
    )

    args = parser.parse_args()
    return args


def main():
    logger.info("starting alert.py")
    # processing args
    args = process_args()
    directory = args.directory
    number_of_files = args.number

    if args.file is not None:
        logger.info("reading config file")
        config_file = json_reader(args.file)
        # generates a hasmap based on the "LINK_NAME" key of the config file
        config_file = {
            link["LINK_NAME"]: link["LINK_SPEED"] for link in config_file["LINKS"]
        }
    else:
        logger.info("no config file provided")
        config_file = None

    files = get_last_n_files(directory, number_of_files)

    output_reports_dict = {
        "time_exceeded_report": {},
        "no_data_report": [],
    }

    # for each file, check if it has exceeded the time limit
    #  and increment the input_report_dict
    for file in files["files"]:
        file = path.join(directory, file)
        input_report_dict = json_reader(file)
        # check if there is file is not a jsnon file
        if input_report_dict is None:
            logger.warning("file {} is not a json file".format(file))
            continue

        output_reports_dict = check_limits_in_report(
            input_report_dict, output_reports_dict
        )

    # clearing not exceeded links
    output_reports_dict["time_exceeded_report"] = clear_not_exceeded_links(
        output_reports_dict["time_exceeded_report"]
    )

    # pprint(output_reports_dict["time_exceeded_report"])

    message = build_message(config_file, output_reports_dict, files)
    # extracting the date from the first and last file names
    first_file = files["files"][0]
    last_file = files["files"][-1]
    first_file_date = first_file.split("_")[1].split(".")[0]
    last_file_date = last_file.split("_")[1].split(".")[0]

    send_alert(
        message,
        "Links excedendo o limite ({} à {})".format(first_file_date, last_file_date),
        "informational",
    )
    pprint(message)
    logger.info("alert.py finished")


def build_message(config_file: dict, output_reports_dict: dict, files: dict):
    """
    builds the message to be sent to the user
    """
    message = ""
    time_exceeded_report = output_reports_dict["time_exceeded_report"]
    # sort time_exceeded_report by time
    time_exceeded_report = dict(
        sorted(
            time_exceeded_report.items(),
            key=lambda item: item[1]["exceeded_time"],
            reverse=True,
        )
    )
    no_data_report = output_reports_dict["no_data_report"]

    # if nothing to report
    if len(time_exceeded_report) == 0 and len(no_data_report) == 0:
        logger.info("nothing to report, sending message 'nothing to report'")
        message += "Nenhum link excedeu o limite nos últimos {} dias.".format(
            files["size"]
        )
        return message

    # time exceeded case
    if len(time_exceeded_report) > 0:
        # extracting the date from the first and last file names
        first_file = files["files"][0]
        last_file = files["files"][-1]
        first_file_date = first_file.split("_")[1].split(".")[0]
        last_file_date = last_file.split("_")[1].split(".")[0]

        message += ("Nos últimos {} dias (entre {} e {}):\n").format(
            files["size"], first_file_date, last_file_date
        )

        # if exceeded the time limit
        if len([link for link in time_exceeded_report]) > 0:
            logger.info(
                "links found exceeding the time limit,\
                 sending message"
            )

            for link in time_exceeded_report:
                if config_file is not None and config_file.get(link) is not None:
                    link_speed = config_file[link] / 1000000
                    if link_speed >= 1000:
                        link_speed = link_speed / 1000
                        link_speed = " ({} Gbps)".format(int(link_speed))
                    else:
                        link_speed = " ({} Mbps)".format(int(link_speed))
                else:
                    link_speed = ""

                message += "\t{}{} - excedeu o tempo limite por {} minutos e apareceu no relatório em {} dias\n".format(
                    link,
                    link_speed,
                    time_exceeded_report[link]["exceeded_time"],
                    time_exceeded_report[link]["days"],
                )

    message += "\n"

    # no data case
    if len(no_data_report) > 0:
        logger.info(
            "no data links found, sending message \
            'no data links found'"
        )
        message += "Os seguintes links não possuem dados,\
             o que pode ser resultado de um erro:\n"
        for link in no_data_report:
            message += "\t{}\n".format(link)

    message += "\n"

    # legend
    message += "Legenda:\n - Tempo limite: {} minutos\n\
        ".format(
        TIME_THRESHOLD
    )

    return message


def clear_not_exceeded_links(time_exceeded_report: dict):
    """
    removes the links that have not exceeded the time limit
    """
    links = list(time_exceeded_report.keys())
    for link in links:
        if time_exceeded_report[link]["exceeded_time"] == 0:
            time_exceeded_report.pop(link)

    return time_exceeded_report


def check_limits_in_report(input_report_dict: dict, output_reports_dict: dict):
    """
    checks if the reports have exceeded the time limit
     and increments the output_report
    """
    logger.info(
        "Checking limits in report \
        {}".format(
            input_report_dict["Data"]
        )
    )
    # removes the Data key from the input_report_dict
    if "Data" in input_report_dict:
        input_report_dict.pop("Data")
    else:
        logger.warning(
            "Data key not found in \
            {}".format(
                input_report_dict["Data"]
            )
        )

    # extracting the links from the input_report_dict dict
    links = list(input_report_dict.keys())

    # for each link, check if it has exceeded the time limit
    #  and increment the input_report_dict
    for link in links:
        # extracting the reports from the output_reports_dict dict
        # for better readability
        time_exceeded_report = output_reports_dict["time_exceeded_report"]
        no_data_report = output_reports_dict["no_data_report"]

        # checking if is a valid link
        if not is_valid_link(input_report_dict, link):
            logger.warning("Link {} is not valid".format(link))
            continue

        # no data case
        if "No Data" in input_report_dict[link]:
            logger.debug("No data found for link {}".format(link))
            no_data_report.append(link)
            continue

        # no exceeded time case
        if (
            input_report_dict[link]["rx"]["total_exceeded"] == 0
            and input_report_dict[link]["tx"]["total_exceeded"] == 0
        ):
            logger.debug("No exceeded time found for link {}".format(link))
            continue

        # if the link is not in the input_report_dict, add it
        if link not in time_exceeded_report:
            logger.debug(
                "Adding link {}\
                 to the time exceeded report".format(
                    link
                )
            )
            time_exceeded_report[link] = {
                "exceeded_time": 0,
                "days": 0,
            }

        # rx+tx exceeded time
        exceeded_time = (
            input_report_dict[link]["rx"]["total_exceeded"]
            + input_report_dict[link]["tx"]["total_exceeded"]
        )

        # if the link has exceeded the time limit,
        #  add it to the output_report_dict
        if exceeded_time >= TIME_THRESHOLD:
            logger.info(
                "Link {}\
                 has exceeded the time limit of {}".format(
                    link, TIME_THRESHOLD
                )
            )
            # updating link report
            time_exceeded_report[link]["exceeded_time"] += exceeded_time
            time_exceeded_report[link]["days"] += 1

    output_reports_dict["time_exceeded_report"] = time_exceeded_report
    output_reports_dict["no_data_report"] = no_data_report

    return output_reports_dict


def is_valid_link(input_report_dict: dict, link: str):
    """
    checks if the link is valid
    """
    if link not in input_report_dict:
        logger.warning("Link {} not found in report".format(link))
        return False

    if "rx" not in input_report_dict[link]:
        logger.warning("rx not found in link {}".format(link))
        return False

    if "tx" not in input_report_dict[link]:
        logger.warning("tx not found in link {}".format(link))
        return False

    return True


def sort_dates(dates):
    """
    sorts the dates in ascending order
    """
    split_dates = [date.split("-") for date in dates]
    split_dates.sort(key=lambda x: (x[2], x[1], x[0]))
    dates = ["-".join(date) for date in split_dates]
    return dates


def get_last_n_files(directory: path, number_of_files: int):
    """
    search for the last N json files in the directory
    """
    files = {}
    # getting the last N json files
    files["files"] = [  # pylint: disable=consider-using-dict-comprehension
        file
        for file in listdir(directory)
        if (file.endswith(".json") and file.startswith("report"))
    ]
    files["files"] = sort_dates(files["files"])
    files["files"] = files["files"][-number_of_files:]
    files["size"] = len(files["files"])
    logger.info("Files from the last {} days".format(number_of_files))
    logger.debug("files: {}".format(files["files"]))

    return files


if __name__ == "__main__":
    main()
