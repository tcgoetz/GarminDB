#!/usr/bin/env python

#
# copyright Tom Goetz
#

import unittest, logging, os, sys

from TestSummaryDBBase import TestSummaryDBBase

sys.path.append('../.')

import HealthDB


root_logger = logging.getLogger()
handler = logging.FileHandler('summary_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
db_dir = os.environ['DB_DIR']


class TestSummaryDB(TestSummaryDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_params_dict = {}
        cls.db_params_dict['db_type'] = 'sqlite'
        cls.db_params_dict['db_path'] = db_dir
        db = HealthDB.SummaryDB(cls.db_params_dict)
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

