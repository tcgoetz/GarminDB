#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging, sys


logger = logging.getLogger(__name__)


class TestDBBase(object):

    @classmethod
    def setUpClass(cls, db, table_dict):
        cls.db = db
        cls.table_dict = table_dict

    def test_db_exists(self):
        logger.info("Checking DB %s exists", self.db.db_name)
        self.assertIsNotNone(self.db)

    def test_db_tables_exists(self):
        for table_name, table in self.table_dict.iteritems():
            logger.info("Checking %s exists", table_name)
            self.assertTrue(table.row_count(self.db) > 0)

