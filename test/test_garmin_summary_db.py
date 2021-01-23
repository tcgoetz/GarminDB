"""Test garmin summary db."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import unittest
import logging

from test_summary_db_base import TestSummaryDBBase
import GarminDB
from garmin_db_config_manager import GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_summary_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestGarminSummaryDB(TestSummaryDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_params = GarminDBConfigManager.get_db_params()
        db = GarminDB.GarminSummaryDB(db_params)
        table_dict = {
            'summary_table' : GarminDB.Summary,
            'months_table' : GarminDB.MonthsSummary,
            'weeks_table' : GarminDB.WeeksSummary,
            'days_table' : GarminDB.DaysSummary
        }
        super().setUpClass(db, table_dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
