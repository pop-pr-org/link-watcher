#!/usr/bin/env python
# coding=utf-8

from os.path import join
from logging import getLogger

from pprint import pprint

logger = getLogger("watcher")

class ReportManipulator():
    def create_report_file_name(self, current_report_date, output_path) -> str:
        """
        Creates the name of the json output file
        @Returns: a string that contains the relative path of the file to be created
        """
        file_name = "reports_" + current_report_date + ".json"
        # creating absolute path
        file_path = join(output_path, file_name)
        logger.info("creating report file at: %s", file_path)
        return file_path
    
    def add_interval_to_report(self,
    link_iface_report: dict,
    time_begin: str,
    time_end: str,
    interval_counter: int,
    exceeded_time: int
    ):
        """
        adds an interval to the report dict in the format:
        "intervals": {
            "1": {
                "begin": "2021-01-01T00:00:00Z",
                "end": "2021-01-01T01:00:00Z",
                "exceeded_time": "20min"
            },
            "2": {
                "begin": "2021-01-01T01:00:00Z",
                "end": "2021-01-01T02:00:00Z",
                "exceeded_time": "20min"
            },
            ...
        }
        updates the interval report dict
        """ 
        # register Interval start
        link_iface_report["intervals"].update({interval_counter: {"begin": time_begin}})
        # Interval end
        link_iface_report["intervals"][interval_counter].update({"end": time_end})

        # Exceeded time
        link_iface_report["intervals"][interval_counter].update(
            {"exceeded_time": str(exceeded_time) + "min"}
        )

        # total exceeded time
        link_iface_report["total_exceeded"] += exceeded_time
