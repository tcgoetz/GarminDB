"""A building block for other db tests."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging

from test_db_base import TestDBBase


logger = logging.getLogger(__name__)


class TestSummaryDBBase(TestDBBase):

    def test_db_cols_have_values(self):
        logger.info("Checking DB %s months table has values", self.db.db_name)
        months_table = self.table_dict['months_table']
        self.assertGreater(months_table.get_col_max(self.db, months_table.hr_avg), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.hr_min), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.hr_max), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.rhr_avg), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.rhr_min), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.rhr_max), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.weight_avg), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.weight_min), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.weight_max), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.stress_avg), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.calories_avg), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.calories_bmr_avg), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.calories_active_avg), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.activities), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.activities_calories), 0)
        self.assertGreater(months_table.get_col_max(self.db, months_table.activities_distance), 0)
