"""Test Garmin monitoring database data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

import fitfile

from garmindb import GarminConnectConfigManager, GarminMonitoringFitData, GarminSummaryData, MonitoringFitFileProcessor, PluginManager
from garmindb.garmindb import GarminDb, File, Device, DeviceInfo, DailySummary
from garmindb.garmindb import MonitoringDb, Monitoring, MonitoringInfo, MonitoringHeartRate, MonitoringIntensity, MonitoringClimb

from test_db_base import TestDBBase


root_logger = logging.getLogger()
handler = logging.FileHandler('monitoring_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestMonitoringDB(TestDBBase, unittest.TestCase):
    """Class for testing Garmin monitoring database data."""

    @classmethod
    def setUpClass(cls):
        cls.gc_config = GarminConnectConfigManager()
        db_params = cls.gc_config.get_db_params()
        cls.plugin_manager = PluginManager(cls.gc_config.get_plugins_dir(), db_params)
        cls.garmin_mon_db = MonitoringDb(db_params)
        table_dict = {
            'monitoring_info_table'         : MonitoringInfo,
            'monitoring_hr_table'           : MonitoringHeartRate,
            'monitoring_intensity_table'    : MonitoringIntensity,
            'monitoring_climb_table'        : MonitoringClimb,
            'monitoring_table'              : Monitoring,
        }
        super().setUpClass(cls.garmin_mon_db, table_dict)

    def test_garmin_mon_db_tables_exists(self):
        self.assertGreater(MonitoringInfo.row_count(self.db), 0)
        self.assertGreater(MonitoringHeartRate.row_count(self.db), 0)
        self.assertGreater(MonitoringIntensity.row_count(self.db), 0)
        self.assertGreater(MonitoringClimb.row_count(self.db), 0)
        self.assertGreater(Monitoring.row_count(self.db), 0)

    def test_garmin_mon_db_steps_bounds(self):
        min = Monitoring.get_col_min(self.db, Monitoring.steps)
        self.assertGreater(min, 0)
        max = Monitoring.get_col_max(self.db, Monitoring.steps)
        self.assertGreater(max, 0)
        self.assertLess(max, 100000)

    def test_garmin_mon_db_uptodate(self):
        uptodate_tables = {
            'monitoring_hr_table'   : MonitoringHeartRate,
            'monitoring_table'      : Monitoring,
        }
        for table_name, table in uptodate_tables.items():
            latest = MonitoringHeartRate.latest_time(self.db, MonitoringHeartRate.heart_rate)
            logger.info("Latest data for %s: %s", table_name, latest)
            self.assertLess(datetime.datetime.now() - latest, datetime.timedelta(days=2))

    def fit_file_import(self, db_params):
        gfd = GarminMonitoringFitData('test_files/fit/monitoring', latest=False, measurement_system=fitfile.field_enums.DisplayMeasure.statute, debug=2)
        self.gfd_file_count = gfd.file_count()
        if gfd.file_count() > 0:
            gfd.process_files(MonitoringFitFileProcessor(db_params, self.plugin_manager))

    def test_fit_file_import(self):
        db_params = self.gc_config.get_db_params(test_db=True)
        self.profile_function('fit_mon_import', self.fit_file_import, db_params)
        test_mon_db = GarminDb(db_params)
        self.check_db_tables_exists(test_mon_db, {'device_table' : Device})
        self.check_db_tables_exists(test_mon_db, {'file_table' : File, 'device_info_table' : DeviceInfo}, self.gfd_file_count)
        table_not_none_cols_dict = {Monitoring : [Monitoring.timestamp, Monitoring.activity_type, Monitoring.duration]}
        self.check_not_none_cols(MonitoringDb(db_params), table_not_none_cols_dict)

    def test_summary_json_file_import(self):
        db_params = self.gc_config.get_db_params(test_db=True)
        gjsd = GarminSummaryData(db_params, 'test_files/json/monitoring/summary', latest=False, measurement_system=fitfile.field_enums.DisplayMeasure.statute, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()
        table_not_none_cols_dict = {
            DailySummary : [DailySummary.rhr, DailySummary.distance, DailySummary.steps, DailySummary.floors_goal]
        }
        self.check_not_none_cols(GarminDb(db_params), table_not_none_cols_dict)

    def check_day_steps(self, data):
        last_steps = {}
        last_steps_timestamp = None
        for monitoring in data:
            if monitoring.steps is not None:
                steps = monitoring.steps
                activity_type = monitoring.activity_type
                if activity_type in last_steps:
                    activity_last_steps = last_steps[activity_type]
                    self.assertGreaterEqual(steps, activity_last_steps,
                                            f'{repr(monitoring)} - steps at {monitoring.timestamp} not greater than last steps at {last_steps_timestamp}')
                last_steps[activity_type] = steps
                last_steps_timestamp = monitoring.timestamp

    def test_db_data_integrity(self):
        target_day = (datetime.datetime.now() - datetime.timedelta(days=2)).date()
        day_data = Monitoring.get_for_day(self.garmin_mon_db, Monitoring, target_day)
        self.check_day_steps(day_data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
