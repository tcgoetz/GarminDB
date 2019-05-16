#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest, os, logging, sys, datetime, re

from sqlalchemy.exc import IntegrityError

sys.path.append('../.')

import GarminDB
import Fit
from FileProcessor import *

import GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('monitoring_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestMonitoringDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = GarminDBConfigManager.get_db_params()

    def test_garmin_mon_db_exists(self):
        garmin_mon_db = GarminDB.MonitoringDB(self.db_params_dict)
        self.assertIsNotNone(garmin_mon_db)

    def test_garmin_mon_db_tables_exists(self):
        garmin_mon_db = GarminDB.MonitoringDB(self.db_params_dict)
        self.assertGreater(GarminDB.MonitoringInfo.row_count(garmin_mon_db), 0)
        self.assertGreater(GarminDB.MonitoringHeartRate.row_count(garmin_mon_db), 0)
        self.assertGreater(GarminDB.MonitoringIntensity.row_count(garmin_mon_db), 0)
        self.assertGreater(GarminDB.MonitoringClimb.row_count(garmin_mon_db), 0)
        self.assertGreater(GarminDB.Monitoring.row_count(garmin_mon_db), 0)

    def test_garmin_mon_db_steps_bounds(self):
        garmin_mon_db = GarminDB.MonitoringDB(self.db_params_dict)
        min = GarminDB.Monitoring.get_col_min(garmin_mon_db, GarminDB.Monitoring.steps)
        self.assertGreater(min, 0)
        max = GarminDB.Monitoring.get_col_max(garmin_mon_db, GarminDB.Monitoring.steps)
        self.assertGreater(max, 0)
        self.assertLess(max, 100000)


if __name__ == '__main__':
    unittest.main(verbosity=2)

