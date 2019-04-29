#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class DbVersionObject(KeyValueObject):
    __tablename__ = 'version'

    def version_check_key(self, db, version_key, version_number):
        self.set_if_unset(db, version_key, version_number)
        return self.get_int(db, version_key)

    def version_check(self, db, version_number):
        self.version = self.version_check_key(db, 'version', version_number)
        if self.version != version_number:
            raise RuntimeError("DB %s version mismatch. Please rebuild the %s DB. (%s vs %s)" %
                    (db.db_name, db.db_name, self.version, version_number))

    def update_version(self, db, version_key, version_number):
        self.set(db, version_key, version_number)
