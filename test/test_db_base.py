"""A building block for other tests."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import cProfile
import pstats


logger = logging.getLogger(__name__)


class TestDBBase(object):

    @classmethod
    def setUpClass(cls, db, table_dict, table_not_none_cols_dict={}):
        cls.db = db
        cls.table_dict = table_dict
        cls.table_not_none_cols_dict = table_not_none_cols_dict

    def profile_function(self, output_file_prefix, func, *args):
        pr = cProfile.Profile()
        pr.runcall(func, *args)
        ps_cum = pstats.Stats(pr, stream=open(output_file_prefix + '_cum.txt', 'w')).sort_stats('cumulative')
        ps_cum.print_stats()
        ps_tot = pstats.Stats(pr, stream=open(output_file_prefix + '_tot.txt', 'w')).sort_stats('tottime')
        ps_tot.print_stats()

    def check_not_none_cols(self, db, table_not_none_cols_dict):
        for table, not_none_cols_list in table_not_none_cols_dict.items():
            for not_none_col in not_none_cols_list:
                self.assertTrue(table.row_count(db, not_none_col, None) == 0, 'table %s col %s has None values' % (table, not_none_col))

    def check_db_tables_exists(self, db, table_dict, min_rows=1):
        for table_name, table in table_dict.items():
            logger.info("Checking %s exists", table_name)
            self.assertGreaterEqual(table.row_count(db), min_rows, 'table %s has no data' % table_name)

    def test_db_exists(self):
        logger.info("Checking DB %s exists", self.db.db_name)
        self.assertIsNotNone(self.db, 'DB %s doesnt exist' % self.db.db_name)

    def test_db_tables_exists(self):
        self.check_db_tables_exists(self.db, self.table_dict)

    def test_not_none_cols(self):
        self.check_not_none_cols(self.db, self.table_not_none_cols_dict)

    def check_col_type(self, db, table, col, type):
        for value in table.get_col_distinct(db, col):
            self.assertEqual(str(type(value)), value, f'table {table} col {col} has type {type} mismatch for {value}')