#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest, os, logging, sys, datetime, re

sys.path.append('../.')

import GarminDB


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_summary_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
db_dir = os.environ['DB_DIR']


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
    unittest.main(verbosity=2)

