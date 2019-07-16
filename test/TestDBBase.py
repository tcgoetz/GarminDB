#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging


logger = logging.getLogger(__name__)


class TestDBBase(object):

    @classmethod
    def setUpClass(cls, db, table_dict, table_not_none_cols_dict={}):
        cls.db = db
        cls.table_dict = table_dict
        cls.table_not_none_cols_dict = table_not_none_cols_dict

    def test_db_exists(self):
        logger.info("Checking DB %s exists", self.db.db_name)
        self.assertIsNotNone(self.db, 'DB %s doesnt exist' % self.db.db_name)

    def test_db_tables_exists(self):
        for table_name, table in self.table_dict.iteritems():
            logger.info("Checking %s exists", table_name)
            self.assertTrue(table.row_count(self.db) > 0, 'table %s has no data' % table_name)

    def test_not_none_cols(self):
        for table, not_none_cols_list in self.table_not_none_cols_dict.iteritems():
            for not_none_col in not_none_cols_list:
                self.assertTrue(table.row_count(self.db, not_none_col, None) == 0, 'table %s col %s has None values' % (table, not_none_col))
