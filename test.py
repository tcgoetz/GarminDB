#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest, os, logging

import GarminDB


logger = logging.getLogger(__name__)

db_dir = None


class TestGarminDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = {}
        cls.db_params_dict['db_type'] = 'sqlite'
        cls.db_params_dict['db_path'] = db_dir

    def test_garmindb_exists(self):
        garmindb = GarminDB.GarminDB(self.db_params_dict)
        self.assertIsNotNone(garmindb)

    def test_garmindb_tables_exists(self):
        garmindb = GarminDB.GarminDB(self.db_params_dict)
        self.assertGreater(GarminDB.Attributes.row_count(garmindb), 0)
        self.assertGreater(GarminDB.Device.row_count(garmindb), 0)
        self.assertGreater(GarminDB.DeviceInfo.row_count(garmindb), 0)
        self.assertGreater(GarminDB.File.row_count(garmindb), 0)
        self.assertGreater(GarminDB.Weight.row_count(garmindb), 0)
        self.assertGreater(GarminDB.Stress.row_count(garmindb), 0)
        self.assertGreater(GarminDB.Sleep.row_count(garmindb), 0)
        self.assertGreater(GarminDB.SleepEvents.row_count(garmindb), 0)
        self.assertGreater(GarminDB.RestingHeartRate.row_count(garmindb), 0)


class TestActivitiesDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = {}
        cls.db_params_dict['db_type'] = 'sqlite'
        cls.db_params_dict['db_path'] = db_dir

    def test_garmin_act_db_exists(self):
        garmin_act_db = GarminDB.ActivitiesDB(self.db_params_dict)
        self.assertIsNotNone(garmin_act_db)

    def test_garmin_act_db_tables_exists(self):
        garmin_act_db = GarminDB.ActivitiesDB(self.db_params_dict)
        self.assertGreater(GarminDB.Activities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityLaps.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityRecords.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.RunActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.WalkActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.PaddleActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.CycleActivities.row_count(garmin_act_db), 0)
        self.assertGreater(GarminDB.EllipticalActivities.row_count(garmin_act_db), 0)


class TestMonitoringDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = {}
        cls.db_params_dict['db_type'] = 'sqlite'
        cls.db_params_dict['db_path'] = db_dir

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


class TestGarminSummaryDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = {}
        cls.db_params_dict['db_type'] = 'sqlite'
        cls.db_params_dict['db_path'] = db_dir

    def test_garminsumdb_exists(self):
        garminsumdb = GarminDB.GarminSummaryDB(self.db_params_dict)
        self.assertIsNotNone(garminsumdb)

    def test_garminsumdb_tables_exists(self):
        garminsumdb = GarminDB.GarminSummaryDB(self.db_params_dict)
        self.assertTrue(GarminDB.Summary.row_count(garminsumdb) > 0)
        self.assertTrue(GarminDB.MonthsSummary.row_count(garminsumdb) > 0)
        self.assertTrue(GarminDB.WeeksSummary.row_count(garminsumdb) > 0)
        self.assertTrue(GarminDB.DaysSummary.row_count(garminsumdb) > 0)

    def test_garminsumdb_cols_have_values(self):
        garminsumdb = GarminDB.GarminSummaryDB(self.db_params_dict)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.hr_avg), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.hr_min), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.hr_max), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.rhr_avg), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.rhr_min), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.rhr_max), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.weight_avg), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.weight_min), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.weight_max), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.stress_avg), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.calories_avg), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.calories_bmr_avg), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.calories_active_avg), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.activities), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.activities_calories), 0)
        self.assertGreater(GarminDB.MonthsSummary.get_col_max(garminsumdb, GarminDB.MonthsSummary.activities_distance), 0)


if __name__ == '__main__':
    db_dir = os.environ['DB_DIR']
    unittest.main(verbosity=2)

