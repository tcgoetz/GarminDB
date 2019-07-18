"""Objects for implementing databse versioning."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import key_value


class DbVersionObject(key_value.KeyValueObject):
    """Objects for managing databse versioning."""

    __tablename__ = 'version'

    def __version_check_key(self, db, version_key, version_number):
        self.set_if_unset(db, version_key, version_number)
        return self.get_int(db, version_key)

    def version_check(self, db, version_number):
        """Check if the databse version in the database is the same as in the code."""
        self.version = self.__version_check_key(db, 'version', version_number)
        if self.version != version_number:
            raise RuntimeError("DB: %s version mismatch. The DB schema has been updated. Please rebuild the %s DB. (%s vs %s)" %
                               (db.db_name, db.db_name, self.version, version_number))

    def table_version_check(self, db, table_object):
        """Check if the table version in the database is the same as in the code."""
        self.version = self.__version_check_key(db, table_object.__tablename__ + '_version', table_object.table_version)
        if self.version != table_object.table_version:
            raise RuntimeError("DB: %s table %s version mismatch. The DB schema has been updated. Please rebuild the %s DB. (%s vs %s)" %
                               (db.db_name, table_object.__tablename__, db.db_name, self.version, table_object.table_version))

    def view_version_check(self, db, table_object):
        """Check if the view version in the database is the same as in the code."""
        if hasattr(table_object, 'view_version'):
            self.version = self.__version_check_key(db, table_object.__tablename__ + '_view_version', table_object.view_version)
            return self.version == table_object.view_version
        return True

    def update_version(self, db, version_key, version_number):
        """Update the copy of the database version stored in the databse."""
        self.set(db, version_key, version_number)
