"""Test garmin summary db."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import unittest
import logging

from garmindb import ConfigManager
from garmindb.garmindb import GarminSummaryDb, Summary, MonthsSummary, WeeksSummary, DaysSummary

from test_summary_db_base import TestSummaryDBBase


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_summary_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestGarminSummaryDB(TestSummaryDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_params = ConfigManager.get_db_params()
        db = GarminSummaryDb(db_params)
        table_dict = {
            'summary_table' : Summary,
            'months_table' : MonthsSummary,
            'weeks_table' : WeeksSummary,
            'days_table' : DaysSummary
        }
        super().setUpClass(db, table_dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
