#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest, logging, os, sys

from TestSummaryDBBase import TestSummaryDBBase

sys.path.append('../.')

import GarminDB

import GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_summary_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestGarminSummaryDB(TestSummaryDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_params_dict = GarminDBConfigManager.get_db_params()
        db = GarminDB.GarminSummaryDB(db_params_dict)
        super(TestGarminSummaryDB, cls).setUpClass(db,
            {
                'summary_table' : GarminDB.Summary,
                'months_table' : GarminDB.MonthsSummary,
                'weeks_table' : GarminDB.WeeksSummary,
                'days_table' : GarminDB.DaysSummary
            }
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)

