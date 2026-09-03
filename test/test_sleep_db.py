"""Test garmin db."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

import fitfile

from garmindb import GarminConnectConfigManager, GarminSleepFitData, SleepFitFileProcessor
from garmindb.garmindb import SleepDb, SleepEvents, Sleep 

from test_db_base import TestDBBase


root_logger = logging.getLogger()
handler = logging.FileHandler('test_sleep_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class TestGarminDb(TestDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        gc_config = GarminConnectConfigManager()
        db_params = gc_config.get_db_params()
        cls.test_db_params = gc_config.get_db_params(test_db=True)
        print(f"db params {repr(cls.test_db_params)}")
        cls.sleep_db = SleepDb(db_params)
        cls.measurement_system = fitfile.MeasurementSystem.statute
        table_dict = {
            'sleep_events_table': SleepEvents,
        }
        super().setUpClass(cls.sleep_db, table_dict, table_can_be_empty=['sleep_events_table'])

    def check_col_stat(self, value_name, value, bounds):
        min_value, max_value = bounds
        self.assertGreaterEqual(value, min_value, '%s value %s less than min %s' % (value_name, value, min_value))
        self.assertLessEqual(value, max_value, '%s value %s greater than max %s' % (value_name, value, max_value))
        logger.info("%s: %s", value_name, value)

    def check_col_stats(self, db, table, col, col_name, ignore_le_zero, time_col,
                        records_bounds, max_bounds, min_bounds, avg_bounds, latest_bounds):
        self.check_col_stat(col_name + ' records', table.row_count(db), records_bounds)
        if table.row_count(db) == 0:
            logger.info("Skipping bounds check for %s: no data", col_name)
            return
        if time_col:
            maximum = table.get_time_col_max(db, col)
        else:
            maximum = table.get_col_max(db, col)
        self.check_col_stat(col_name + ' max', maximum, max_bounds)
        if time_col:
            minimum = table.get_time_col_min(db, col, None, None)
        else:
            minimum = table.get_col_min(db, col, None, None, ignore_le_zero)
        self.check_col_stat(col_name + ' min', minimum, min_bounds)
        if time_col:
            average = table.get_time_col_avg(db, col, None, None)
        else:
            average = table.get_col_avg(db, col, None, None, ignore_le_zero)
        self.check_col_stat(col_name + ' avg', average, avg_bounds)
        latest = table.get_time_col_latest(db, col) if time_col else table.get_col_latest(db, col, ignore_le_zero)
        self.check_col_stat(col_name + ' latest', latest, latest_bounds)

    def test_garmindb_tables_bounds(self):
        self.check_col_stats(
            self.sleep_db, Sleep, Sleep.total_sleep, 'Sleep', True, True,
            (0, 10000000),
            (datetime.time(8), datetime.time(16)),
            (datetime.time(0), datetime.time(4)),
            (datetime.time(4), datetime.time(10)),
            (datetime.time(2), datetime.time(16))
        )
        self.check_col_stats(
            self.sleep_db, Sleep, Sleep.rem_sleep, 'REM Sleep', True, True,
            (0, 10000000),
            (datetime.time(2), datetime.time(8)),           # max
            (datetime.time(0), datetime.time(2)),           # min
            (datetime.time(minute=30), datetime.time(6)),   # avg
            (datetime.time(minute=5), datetime.time(6))    # latest
        )

    def test_sleep_import(self):
        gfd = GarminSleepFitData('test_files/fit/sleep', latest=False, measurement_system=self.measurement_system, debug=2)
        self.gfd_file_count = gfd.file_count()
        if gfd.file_count() > 0:
            gfd.process_files(SleepFitFileProcessor(self.test_db_params))


if __name__ == '__main__':
    unittest.main(verbosity=2)
