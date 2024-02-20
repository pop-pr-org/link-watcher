#!/usr/bin/env python
# coding=utf-8

import argparse 

from os import environ
from datetime import datetime, timedelta
from logging import getLogger
from dateutil import parser

from config import WORK_HOUR_BEGIN, WORK_HOUR_END, TSDB_TIME_FORMAT

logger = getLogger("watcher")

class DateManipulator():
    def check_work_hour_interval(self) -> None | ValueError:
        """
        Checks if the WORK_HOUR_BEGIN and WORK_HOUR_END vars time interval is valid    
        return: None|ValueError
        """
        if WORK_HOUR_BEGIN > WORK_HOUR_END:
            logger.error(
                "WORK_HOUR_BEGIN var is greater than WORK_HOUR_END var. Check your .env file and fix it"
            )
            raise ValueError(
                "WORK_HOUR_BEGIN var is greater than WORK_HOUR_END var. Check your .env file and fix it"
            )
        return


    def change_tsdb_time_interval(self, iterator: int) -> dict:
        """
        Calculates the next time interval to be used in the query
        @return: dict with the new time interval in the format:
        {
            "begin": "2021-01-01T00:00:00Z",
            "end": "2021-01-01T01:00:00Z",
        }
        """

        # this needs to be checked because the first time the script runs,
        # it shouldn't add 1 day to the begin date
        sum_day = 0 if iterator == 0 else 1

        current_report_query_date_begin = datetime.strptime(
            environ["QUERY_DATE_BEGIN"], TSDB_TIME_FORMAT
        ) + timedelta(days=sum_day)

        current_report_query_date_end = current_report_query_date_begin.replace(
            hour=WORK_HOUR_END
        )
        current_report_query_date_begin = current_report_query_date_begin.replace(
            hour=WORK_HOUR_BEGIN
        )

        # formatting dates to query TSDB
        current_report_query_date_begin = current_report_query_date_begin.strftime(
            TSDB_TIME_FORMAT
        )
        current_report_query_date_end = current_report_query_date_end.strftime(
            TSDB_TIME_FORMAT
        )

        current_report_query_date_interval = {
            "begin": current_report_query_date_begin,
            "end": current_report_query_date_end,
        }

        return current_report_query_date_interval


    def set_tsdb_date_interval(self, date_begin, date_end):
        """
        Set the environment variables QUERY_DATE_BEGIN and QUERY_DATE_END to be used in the query
        """
        date_begin = parser.parse(date_begin).replace(
            hour=WORK_HOUR_BEGIN, minute=0, second=0
        )
        date_end = parser.parse(date_end).replace(hour=WORK_HOUR_END, minute=0, second=0)
        # setting env vars
        environ["QUERY_DATE_BEGIN"] = str(date_begin)
        environ["QUERY_DATE_END"] = str(date_end)


    def set_report_date(self) -> str:
        report_date = environ["QUERY_DATE_BEGIN"].split(" ")[0]
        report_date = datetime.strptime(report_date, "%Y-%m-%d")
        # set the report date to %d-%m-%y
        report_date = report_date.strftime("%d-%m-%y")
        return report_date


    def extract_qntd_days_to_check(self) -> int:
        """
        Extracts the number of days to check from the --date-begin and --date-end flags
        @return: number of days to check
        """

        # extracting env vars
        date_begin = environ["QUERY_DATE_BEGIN"]
        date_end = environ["QUERY_DATE_END"]

        # parsing dates to datetime
        date_begin = str(date_begin)
        date_end = str(date_end)

        # formatting dates to query TSDB
        date_begin = datetime.strptime(date_begin, TSDB_TIME_FORMAT)
        date_end = datetime.strptime(date_end, TSDB_TIME_FORMAT)

        qntd_days_to_check = (date_end - date_begin).days
        return qntd_days_to_check


    def check_date_range_dependency(self,
        args: argparse.Namespace, parser: argparse.ArgumentParser
    ):
        """
        Checks if both date_start and date_end flags are given
        """

        if (args.date_begin and not args.date_end) or (
            args.date_end and not args.date_begin
        ):
            logger.error("--date-begin and --date-end are required together")
            parser.error("--date-begin and --date-end are required together")

        return


    def check_time_interval(self,
        date_begin: str, date_end: str, parser: argparse.ArgumentParser
    ):
        """
        Checks if the date_begin is greater than date_end
        """
        if date_begin > date_end:
            logger.error("flag date-begin is greater than date-end")
            logger.error("date-begin: %s", date_begin)
            logger.error("date-end: %s", date_end)
            parser.error("flag date-begin is greater than date-end")

        return

