"""Test summary db."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging

from garmindb import summarydb, ConfigManager

from test_summary_db_base import TestSummaryDBBase


root_logger = logging.getLogger()
handler = logging.FileHandler('summary_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestSummaryDB(TestSummaryDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_params = ConfigManager.get_db_params()
        db = summarydb.SummaryDb(db_params)
        table_dict = {
            'summary_table' : summarydb.Summary,
            'months_table' : summarydb.MonthsSummary,
            'weeks_table' : summarydb.WeeksSummary,
            'days_table' : summarydb.DaysSummary
        }
        super().setUpClass(db, table_dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
