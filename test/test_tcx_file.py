#!/usr/bin/env python

"""Test FIT file parsing."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import sys
import datetime
import re

sys.path.append('../.')

from utilities import FileProcessor
import tcx_file


root_logger = logging.getLogger()
handler = logging.FileHandler('tcx_file.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestTcxFile(unittest.TestCase):
    """Class for testing FIT file parsing."""

    @classmethod
    def setUpClass(cls):
        cls.file_path = 'test_files/tcx'
        cls.tcx_filename_regex = r'.*\.tcx'

    def check_activity_file(self, filename):
        tcx = tcx_file.TcxFile(filename)
        end_time = tcx.get_date('completed_at')
        start_time = tcx.get_date('started_at')
        (manufacturer, product) = tcx.get_manufacturer_and_product()
        serial_number = tcx.get_value('creator_version')
        laps = tcx.get_lap_count()
        distance = tcx.get_value('distance')
        sport = tcx.get_sport()
        calories = tcx.get_value('calories')
        start_lat = tcx.get_value('start_latitude')
        start_long = tcx.get_value('start_longitude')
        stop_lat = tcx.get_value('end_latitude')
        stop_long = tcx.get_value('end_longitude')
        avg_hr = tcx.get_value('hr_avg')
        max_hr = tcx.get_value('hr_max')
        max_speed = tcx.get_value('speed_max')
        max_cadence = tcx.get_value('cadence_max')
        avg_cadence = tcx.get_value('cadence_avg')
        logger.info("%s: sport %r end_time %r start_time %r manufacturer %r product %r serial_number %r laps %r distance %r calories %r start %r, %r end %r, %r hr %r, %r max speed %r cadence %r, %r",
                    filename, sport, end_time, start_time, manufacturer, product, serial_number, laps, distance, calories, start_lat, start_long,
                    stop_lat, stop_long, avg_hr, max_hr, max_speed, avg_cadence, max_cadence)

    def test_parse_activity(self):
        file_names = FileProcessor.dir_to_files(self.file_path, self.tcx_filename_regex, False)
        for file_name in file_names:
            self.check_activity_file(file_name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
