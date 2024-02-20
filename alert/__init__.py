#!/usr/bin/env python
# coding=utf-8

from pprint import pprint

from abc import ABC, abstractmethod
from logging import getLogger
from pathlib import Path
from os import listdir, environ
from datetime import datetime, timedelta
from dateutil import parser
from typing import Any, Union

from config import (
    LINKS_INFO_FILE,
    REPORT_OUTPUT_PATH,
    PERCENTILE,
    MAX_PERCENTILE_REPORTS,
    DEFAULT_MAX_TRAFFIC_PERCENTAGE,
    DEFAULT_LINK_HISTERESYS,
    WORK_HOUR_BEGIN,
    WORK_HOUR_END,
)

from tsdb.TsdbExtractor import TsdbExtractor
from utils import json_reader


logger = getLogger("watcher")


class Alert(ABC):
    def __init__(
        self,
        date_begin: str,
        date_end: str,
        time_threshold: int,
        reports_dir: str,
        LINKS_INFO_FILE: str,
        db_client: Any,
    ):
        self.date_begin = date_begin
        """
        date_begin: date to start the query (format: YYYY-MM-DD)
        """
        self.date_end = date_end
        """
        date_end: date to end the query (format: YYYY-MM-DD)
        """
        self.no_data_report = {}
        self.alert_message = ""
        self.LINKS_INFO_FILE = LINKS_INFO_FILE
        self.time_threshold = time_threshold
        self.db_client = db_client
        self.hosts_info = self.__get_hosts_info()
        self.files_to_alert = self.__get_files_by_date(
            date_begin, date_end, reports_dir
        )
        self.missing_reports_message = self.__check_for_missing_reports(
            date_begin, date_end
        )
        self.time_exceeded_report = self.__check_reports()
        self.percentile_report = self.__get_percentile_report()
        self.alert_message = self.__generate_alert_message()

    def __generate_alert_message(self) -> str:
        """
        Generates the alert message
        """
        date_begin = parser.parse(self.date_begin).strftime("%d/%m/%y")
        date_end = parser.parse(self.date_end).strftime("%d/%m/%y")

        alert_message = "Este relatório é referente ao período entre {} e {}\n\
O tráfego coletado é entre às {}h e {}h de cada dia\n".format(
            date_begin, date_end, WORK_HOUR_BEGIN, WORK_HOUR_END
        )

        # if there are PERCENTILEs
        if self.percentile_report:
            alert_message += "\nEstes são os {} links com a maior porcentagem de consumo de banda:\n".format(
                MAX_PERCENTILE_REPORTS, PERCENTILE
            )

            for index, link_name in enumerate(self.percentile_report):
                xth_PERCENTILE = self.percentile_report[link_name]["xth-PERCENTILE"]
                link_speed = self.percentile_report[link_name]["link_speed"]
                float_xth_PERCENTILE = float(xth_PERCENTILE.split(" ")[0])
                float_link_speed = float(link_speed.split(" ")[0])
                alert_message += f"\t{index+1} - {link_name}\
\n\t\tVelocidade contratada: {link_speed}\
\n\t\t{PERCENTILE}-Percentil: {xth_PERCENTILE} ({round(float_xth_PERCENTILE/float_link_speed*100, 2)}%)\n"

            alert_message += (
                "\nOs parâmetros usados para o alerta do percentil foram:\n"
            )
            alert_message += f"\t- Quantidade de links no relatório de percentil: {MAX_PERCENTILE_REPORTS}\n"
            alert_message += f"\t- Percentil: {PERCENTILE}\n"

            alert_message += "\n"

        # if there are no time exceedings
        if not self.time_exceeded_report:
            logger.info("no time exceedings found")
            alert_message += (
                "Nenhum link excedeu o limite entre as datas especificadas\n"
            )
            return alert_message

        # if there are time exceedings
        alert_message += "Os seguintes links excederam o limite de tempo entre as datas especificadas:\n"
        for link_name in self.time_exceeded_report:
            # gets the link speed from the hosts_info dict and converts it to Mbps/Gbps
            link_speed = self.hosts_info[link_name]["LINK_SPEED"]
            link_speed = int(link_speed / 1000000)
            if link_speed >= 1000:
                link_speed = f"{link_speed / 1000} Gbps"
            else:
                link_speed = f"{link_speed} Mbps"

            total_exceeded_time = self.time_exceeded_report[link_name][
                "total_exceeded_time"
            ]
            days_exceeded = self.time_exceeded_report[link_name]["days_exceeded"]
            alert_message += f"\t- {link_name} ({link_speed}): {total_exceeded_time} minutos em {days_exceeded} dias\n"

        # if there are missing reports
        if self.missing_reports_message:
            alert_message += self.missing_reports_message

        # legend for the alert message
        alert_message += (
            "\nOs parâmetros usados para o alerta do consumo de banda foram:\n"
        )
        alert_message += f"\t- Limite de tempo excedendo o consumo de banda: {self.time_threshold} minutos\n"
        alert_message += (
            f"\t- Limite de consumo de banda: {DEFAULT_MAX_TRAFFIC_PERCENTAGE*100}%\n"
        )
        alert_message += f"\t- Histerese: {DEFAULT_LINK_HISTERESYS}%\n"

        return alert_message

    def __get_percentile_report(self) -> dict:
        """
        Gets the PERCENTILE report of the greater N number links sorted by the percentual difference
        of: (xthPERCENTILE - link_speed)

        Returns a dict with the following format:
        {
            LINK_NAME: {
                "xth-PERCENTILE": XTH_PERCENTILE
            }
        }

        Where XTH_PERCENTILE is the PERCENTILE present in the `PERCENTILE` environment variable
        and N is the number of links to be shown in the report(this can be changed in the variable `MAX_PERCENTILE_REPORTS` inside the `.env` file)
        """
        tsdb_extractor = TsdbExtractor()
        percentile_report = {}
        all_links = list(self.hosts_info.keys())
        for link_name in all_links:
            # gets the link speed from the hosts_info dict and converts it to Mbps/Gbps
            link_speed = self.hosts_info[link_name]["LINK_SPEED"]
            link_speed = int(link_speed / 1000000)
            if link_speed >= 1000:
                link_speed = f"{link_speed / 1000} Gbps"
            else:
                link_speed = f"{link_speed} Mbps"

            # set the time format to the tsdb time format
            date_begin = parser.parse(self.date_begin).replace(
                hour=0, minute=0, second=0
            )
            date_begin = date_begin.strftime("%Y-%m-%d %H:%M:%S")
            date_end = parser.parse(self.date_end).replace(
                hour=23, minute=59, second=59
            )
            date_end = date_end.strftime("%Y-%m-%d %H:%M:%S")

            # gets the PERCENTILE for the current link (rx interface)
            rx_xth_percentile = tsdb_extractor.query_iface_percentile(
                PERCENTILE,
                date_begin,
                date_end,
                link_name,
                "rx",
                self.db_client,
            )
            # converts from bits to Mbps
            rx_xth_percentile = rx_xth_percentile / 1000000

            # gets the PERCENTILE for the current link (rx interface)
            tx_xth_percentile = tsdb_extractor.query_iface_percentile(
                PERCENTILE,
                date_begin,
                date_end,
                link_name,
                "tx",
                self.db_client,
            )
            # converts from bits to Mbps
            tx_xth_percentile = tx_xth_percentile / 1000000

            # gets the highest PERCENTILE between rx and tx
            xth_percentile = max(rx_xth_percentile, tx_xth_percentile)
            xth_percentile = round(xth_percentile, 2)

            # convert the PERCENTILE to Mbps/Gbps
            if xth_percentile >= 1000:
                xth_percentile = f"{round(xth_percentile / 10, 2)} Gbps"
            else:
                xth_percentile = f"{xth_percentile} Mbps"
            # if the PERCENTILE is present, updates/creates the "PERCENTILE" key
            percentile_report[link_name] = {
                "xth-PERCENTILE": xth_percentile,
                "link_speed": link_speed,
            }

        # sorts the percentile_report dict by the MAX_percentile_REPORTS first links with the highest
        # percentage of use based on the percentile if the xth-PERCENTILE is greater than 0.0
        percentile_report = dict(
            sorted(
                percentile_report.items(),
                key=lambda item: (
                    float(item[1]["link_speed"].split(" ")[0])
                    / float(item[1]["xth-PERCENTILE"].split(" ")[0])
                    * 100
                    if item[1]["xth-PERCENTILE"].split(" ")[0] > "1.0"
                    else 0.0
                ),
                reverse=True,
            )[:MAX_PERCENTILE_REPORTS]
        )

        # reverse the dict
        percentile_report = dict(
            sorted(
                percentile_report.items(),
                key=lambda item: float(item[1]["link_speed"].split(" ")[0])
                / float(item[1]["xth-PERCENTILE"].split(" ")[0])
                * 100
                if item[1]["xth-PERCENTILE"].split(" ")[0] > "0.0"
                else 0.0,
            )
        )

        return percentile_report

    def __check_reports(self) -> dict:
        """
        Checks each report file in the `files_to_alert` list

        Returns a dict with the following format:
        {
            LINK_NAME: {
                "total_exceeded_time": TOTAL_TIME_EXCEEDED,
                "days_exceeded": DAYS_EXCEEDED,
                "xth-PERCENTILE": XTH_PERCENTILE
            }
        }
        """
        hosts_info = json_reader(self.LINKS_INFO_FILE)

        # iterates over each file in the files_to_alert list
        time_exceeded_report = {}
        for file in self.files_to_alert:
            # reads the file
            current_report = json_reader(file)

            # removes the "Data" key from the report
            current_report.pop("Data", None)

            # for each key in hosts_info dict
            for link_name in hosts_info:
                # if the link_name is not present in the current_report, updates the "no_data" dict
                if (
                    link_name not in current_report
                    or current_report[link_name] == "No data"
                ):
                    self.no_data_report[file.name] = {
                        "date": file.name.split("_")[1].split(".")[0],
                        link_name: hosts_info[link_name],
                    }
                    continue

                # if the link_name is present in the current_report, updates/creates the "time_exceeded" key
                rx_time_exceeded = (
                    current_report.get(link_name, {})
                    .get("rx", {})
                    .get("total_exceeded", 0)
                )
                tx_time_exceeded = (
                    current_report.get(link_name, {})
                    .get("tx", {})
                    .get("total_exceeded", 0)
                )
                total_exceeded_time = rx_time_exceeded + tx_time_exceeded
                if total_exceeded_time >= self.time_threshold:
                    # if the current link is not present in the time_exceeded_report dict, creates it
                    if link_name not in time_exceeded_report:
                        time_exceeded_report[link_name] = {
                            "total_exceeded_time": total_exceeded_time,
                            "days_exceeded": 1,
                        }
                    # if the file is present in the time_exceeded_report dict, updates it
                    else:
                        time_exceeded_report[link_name][
                            "total_exceeded_time"
                        ] += total_exceeded_time
                        time_exceeded_report[link_name]["days_exceeded"] += 1

        # sorts the time_exceeded_report dict by the total_exceeded_time key
        time_exceeded_report = dict(
            sorted(
                time_exceeded_report.items(),
                key=lambda item: item[1]["total_exceeded_time"],
                reverse=True,
            )
        )

        return time_exceeded_report

    def __get_hosts_info(self) -> dict:
        """
        It reads the hosts information file from the `LINKS_INFO_FILE` environment variable
        and updates the `hosts_info` dict with the following format:

        {
            LINK_NAME: LINK_SPEED
        }
        """
        hosts_file = json_reader(LINKS_INFO_FILE)
        logger.info("hosts info read successfully from %s", LINKS_INFO_FILE)
        return hosts_file

    def __get_files_by_date(
        self, date_begin: str, date_end: str, reports_dir: str
    ) -> list[Path]:
        """
        Returns a list of files with the given date
        """
        logger.info("getting files from %s", reports_dir)

        reports_dir = Path(reports_dir)
        date_begin, date_end = self.__extract_separate_dates(date_begin, date_end)

        files = []
        # iterates over the files only
        for file in reports_dir.iterdir():
            if not file.is_file() or not "reports_" in file.name:
                continue

            file_date = file.name.split("_")[1].split(".")[0]
            # date may come as 2021-01-01 or 2021-01-01 00:00:00
            file_date = file_date.split(" ")[0]
            file_date = datetime.strptime(file_date, "%d-%m-%y")
            is_between_dates = date_begin <= file_date <= date_end
            if is_between_dates:
                files.append(file)

        ordered_files = sorted(
            files,
            key=lambda file: datetime.strptime(
                file.name.split("_")[1].split(".")[0], "%d-%m-%y"
            ),
        )
        return ordered_files

    def __extract_separate_dates(self, date_begin: str, date_end: str) -> tuple:
        """
        Extracts the dates from the given date strings
        Returns a tuple with the dates in the following format:
        (full_year, two_digit_year)

        Example: 2021-01-01 -> (2021, 21)
        """
        # extract the two last digits of the year
        date_begin = "-".join(reversed(date_begin.split("-")))
        date_end = "-".join(reversed(date_end.split("-")))

        # extract the two last digits of the year
        full_year = date_begin.split("-")[2]
        two_digit_year = full_year[-2:]
        # replace the year with the two last digits
        date_begin = date_begin.replace(str(full_year), str(two_digit_year))
        date_begin = datetime.strptime(date_begin, "%d-%m-%y")

        # extract the two last digits of the year
        full_year = date_end.split("-")[2]
        two_digit_year = full_year[-2:]
        # replace the year with the two last digits
        date_end = date_end.replace(str(full_year), str(two_digit_year))
        date_end = datetime.strptime(date_end, "%d-%m-%y")

        return date_begin, date_end

    def __check_for_missing_reports(self, date_begin: str, date_end: str) -> str:
        """
        Checks if there are any missing reports in the files_to_alert list

        Returns a string with a message about the missing reports, or an empty string
        """

        # if theres the same amount of files as days between the dates, there are no missing reports
        date_begin = datetime.strptime(date_begin, "%Y-%m-%d")
        date_end = datetime.strptime(date_end, "%Y-%m-%d")
        days_between_dates = (date_end - date_begin).days
        if days_between_dates == len(self.files_to_alert):
            return ""

        # checks for holes in the files_to_alert list
        missing_reports = []
        # iterates over the files only
        dates_to_check = [
            date_begin + timedelta(days=i) for i in range(days_between_dates + 1)
        ]

        for date in dates_to_check:
            date = date.strftime("%d-%m-%y")
            current_file = f"{REPORT_OUTPUT_PATH}reports_{date}.json"
            current_file = Path(current_file)
            if current_file not in self.files_to_alert:
                missing_reports.append(date)

        # if there are no missing reports, return an empty string
        if not missing_reports:
            return ""

        # if there are missing reports, return a string with the missing reports
        message = f"\nATENÇÃO: Os relatórios das seguintes datas estão faltando:\n"
        for report in missing_reports:
            logger.info("report %s is missing", report)
            message += f"\t- {report}\n"
        message += f"\nVerifique se o script está rodando corretamente ou gere os relatórios manualmente\n"
        message += f"Tenha em mente que este relatório\n\
não está considerando os possíveis tempos excedidos presentes nesses relatórios que faltam\n"

        return message

    @abstractmethod
    def send_alert(self):
        pass
