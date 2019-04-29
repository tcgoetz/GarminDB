#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class KeyValueObject(DBObject):

    timestamp = Column(DateTime)
    key = Column(String, primary_key=True)
    value = Column(String)

    time_col_name = 'timestamp'
    match_col_names = ['key']

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.key == values_dict['key'])

    @classmethod
    def set(cls, db, key, value, timestamp=datetime.datetime.now()):
        cls.create_or_update(db, {'timestamp' : timestamp, 'key' : key, 'value' : str(value)})

    @classmethod
    def set_newer(cls, db, key, value, timestamp=datetime.datetime.now()):
        item = cls.find_one(db, {'key' : key})
        if item is None or item.timestamp < timestamp:
            cls.create_or_update(db, {'timestamp' : timestamp, 'key' : key, 'value' : str(value)})

    @classmethod
    def set_if_unset(cls, db, key, value, timestamp=datetime.datetime.now()):
        return cls.find_or_create(db, {'timestamp' : timestamp, 'key' : key, 'value' : str(value)})

    @classmethod
    def get(cls, db, key):
        try:
            return cls.find_one(db, {'key' : key}).value
        except Exception:
            return None

    @classmethod
    def get_int(cls, db, key):
        return int(cls.get(db, key))

    @classmethod
    def get_time(cls, db, key):
        try:
            return datetime.datetime.strptime(cls.get(db, key), "%H:%M:%S").time()
        except Exception:
            return None

