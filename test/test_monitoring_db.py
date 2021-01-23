"""Test Garmin monitoring database data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

from test_db_base import TestDBBase
import GarminDB
import Fit
from garmin_db_config_manager import GarminDBConfigManager
from import_garmin import GarminMonitoringFitData, GarminSummaryData
from monitoring_fit_file_processor import MonitoringFitFileProcessor
from garmin_db_plugin import GarminDbPluginManager


root_logger = logging.getLogger()
handler = logging.FileHandler('monitoring_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestMonitoringDB(TestDBBase, unittest.TestCase):
    """Class for testing Garmin monitoring database data."""

    @classmethod
    def setUpClass(cls):
        db_params = GarminDBConfigManager.get_db_params()
        cls.plugin_manager = GarminDbPluginManager(GarminDBConfigManager.get_or_create_plugins_dir(), db_params)
        cls.garmin_mon_db = GarminDB.MonitoringDB(db_params)
        table_dict = {
            'monitoring_info_table'         : GarminDB.MonitoringInfo,
            'monitoring_hr_table'           : GarminDB.MonitoringHeartRate,
            'monitoring_intensity_table'    : GarminDB.MonitoringIntensity,
            'monitoring_climb_table'        : GarminDB.MonitoringClimb,
            'monitoring_table'              : GarminDB.Monitoring,
        }
        super().setUpClass(cls.garmin_mon_db, table_dict)

    def test_garmin_mon_db_tables_exists(self):
        self.assertGreater(GarminDB.MonitoringInfo.row_count(self.db), 0)
        self.assertGreater(GarminDB.MonitoringHeartRate.row_count(self.db), 0)
        self.assertGreater(GarminDB.MonitoringIntensity.row_count(self.db), 0)
        self.assertGreater(GarminDB.MonitoringClimb.row_count(self.db), 0)
        self.assertGreater(GarminDB.Monitoring.row_count(self.db), 0)

    def test_garmin_mon_db_steps_bounds(self):
        min = GarminDB.Monitoring.get_col_min(self.db, GarminDB.Monitoring.steps)
        self.assertGreater(min, 0)
        max = GarminDB.Monitoring.get_col_max(self.db, GarminDB.Monitoring.steps)
        self.assertGreater(max, 0)
        self.assertLess(max, 100000)

    def test_garmin_mon_db_uptodate(self):
        uptodate_tables = {
            'monitoring_hr_table'   : GarminDB.MonitoringHeartRate,
            'monitoring_table'      : GarminDB.Monitoring,
        }
        for table_name, table in uptodate_tables.items():
            latest = GarminDB.MonitoringHeartRate.latest_time(self.db, GarminDB.MonitoringHeartRate.heart_rate)
            logger.info("Latest data for %s: %s", table_name, latest)
            self.assertLess(datetime.datetime.now() - latest, datetime.timedelta(days=2))

    def fit_file_import(self, db_params):
        gfd = GarminMonitoringFitData('test_files/fit/monitoring', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        self.gfd_file_count = gfd.file_count()
        if gfd.file_count() > 0:
            gfd.process_files(MonitoringFitFileProcessor(db_params, self.plugin_manager))

    def test_fit_file_import(self):
        db_params = GarminDBConfigManager.get_db_params(test_db=True)
        self.profile_function('fit_mon_import', self.fit_file_import, db_params)
        test_mon_db = GarminDB.GarminDB(db_params)
        self.check_db_tables_exists(test_mon_db, {'device_table' : GarminDB.Device})
        self.check_db_tables_exists(test_mon_db, {'file_table' : GarminDB.File, 'device_info_table' : GarminDB.DeviceInfo}, self.gfd_file_count)
        table_not_none_cols_dict = {GarminDB.Monitoring : [GarminDB.Monitoring.timestamp, GarminDB.Monitoring.activity_type, GarminDB.Monitoring.duration]}
        self.check_not_none_cols(GarminDB.MonitoringDB(db_params), table_not_none_cols_dict)

    def test_summary_json_file_import(self):
        db_params = GarminDBConfigManager.get_db_params(test_db=True)
        gjsd = GarminSummaryData(db_params, 'test_files/json/monitoring/summary', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()
        table_not_none_cols_dict = {
            GarminDB.DailySummary : [GarminDB.DailySummary.rhr, GarminDB.DailySummary.distance, GarminDB.DailySummary.steps, GarminDB.DailySummary.floors_goal]
        }
        self.check_not_none_cols(GarminDB.GarminDB(db_params), table_not_none_cols_dict)

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
        day_data = GarminDB.Monitoring.get_for_day(self.garmin_mon_db, GarminDB.Monitoring, target_day)
        self.check_day_steps(day_data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
