#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest
import logging
import sys

from TestSummaryDBBase import TestSummaryDBBase

sys.path.append('../.')

import HealthDB
import GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('summary_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestSummaryDB(TestSummaryDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_params_dict = GarminDBConfigManager.get_db_params()
        db = HealthDB.SummaryDB(db_params_dict)
        super(TestSummaryDB, cls).setUpClass(db,
            {
                'summary_table' : HealthDB.Summary,
                'months_table' : HealthDB.MonthsSummary,
                'weeks_table' : HealthDB.WeeksSummary,
                'days_table' : HealthDB.DaysSummary
            }
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
