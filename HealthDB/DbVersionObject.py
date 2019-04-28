#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class DbVersionObject(KeyValueObject):
    __tablename__ = 'version'

    def __init__(self):
        self.set_query_params()
        super(DbVersionObject, self).__init()

    def version_check(self, db, version_number):
        self.set_if_unset(db, 'version', version_number)
        self.version = self.get_int(db, 'version')
        if self.version != version_number:
            raise RuntimeError("DB %s version mismatch. Please rebuild the %s DB. (%s vs %s)" %
                    (db.db_name, db.db_name, self.version, version_number))
