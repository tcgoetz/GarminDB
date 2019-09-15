#!/usr/bin/env python

"""Test Garmin monitoring database data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import sys
import datetime

from test_db_base import TestDBBase

sys.path.append('../.')

import GarminDB
import Fit
from file_processor import FileProcessor
import garmin_db_config_manager as GarminDBConfigManager
from import_garmin import GarminMonitoringFitData, GarminSummaryData


root_logger = logging.getLogger()
handler = logging.FileHandler('monitoring_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestMonitoringDB(TestDBBase, unittest.TestCase):
    """Class for testing Garmin monitoring database data."""

    @classmethod
    def setUpClass(cls):
        db_params_dict = GarminDBConfigManager.get_db_params()
        garmin_mon_db = GarminDB.MonitoringDB(db_params_dict)
        super(TestMonitoringDB, cls).setUpClass(garmin_mon_db,
            {
                'monitoring_info_table'         : GarminDB.MonitoringInfo,
                'monitoring_hr_table'           : GarminDB.MonitoringHeartRate,
                'monitoring_intensity_table'    : GarminDB.MonitoringIntensity,
                'monitoring_climb_table'        : GarminDB.MonitoringClimb,
                'monitoring_table'              : GarminDB.Monitoring,
            }
        )

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
                'monitoring_hr_table'           : GarminDB.MonitoringHeartRate,
                'monitoring_table'              : GarminDB.Monitoring,
            }
        for table_name, table in uptodate_tables.iteritems():
            latest = GarminDB.MonitoringHeartRate.latest_time(self.db, GarminDB.MonitoringHeartRate.heart_rate)
            logger.info("Latest data for %s: %s", table_name, latest)
            self.assertLess(datetime.datetime.now() - latest, datetime.timedelta(days=2))

    def test_fit_file_import(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        gfd = GarminMonitoringFitData('test_files/fit/monitoring', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        if gfd.file_count() > 0:
            gfd.process_files(db_params_dict)
        test_mon_db = GarminDB.GarminDB(db_params_dict)
        self.check_db_tables_exists(test_mon_db, {'device_table' : GarminDB.Device})
        self.check_db_tables_exists(test_mon_db, {'file_table' : GarminDB.File, 'device_info_table' : GarminDB.DeviceInfo}, gfd.file_count())
        self.check_not_none_cols(GarminDB.MonitoringDB(db_params_dict),
            {GarminDB.Monitoring : [GarminDB.Monitoring.timestamp, GarminDB.Monitoring.activity_type, GarminDB.Monitoring.duration]}
        )

    def test_summary_json_file_import(self):
        db_params_dict = GarminDBConfigManager.get_db_params(test_db=True)
        gjsd = GarminSummaryData(db_params_dict, 'test_files/json/monitoring/summary', latest=False, measurement_system=Fit.field_enums.DisplayMeasure.statute, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()
        self.check_not_none_cols(GarminDB.GarminDB(db_params_dict),
            {GarminDB.DailySummary : [GarminDB.DailySummary.rhr, GarminDB.DailySummary.distance, GarminDB.DailySummary.steps, GarminDB.DailySummary.floors_goal]}
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
