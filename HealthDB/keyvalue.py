"""Objects for implementing key-value database objects."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import traceback
import datetime
import logging
from sqlalchemy import Column, String, DateTime

import db


logger = logging.getLogger(__name__)


class KeyValueObject(db.DBObject):
    """Base class for implementing key-value databse objects."""

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
    def _set_newer(cls, session, key, value, timestamp=datetime.datetime.now()):
        item = cls._find_one(session, {'key' : key})
        if item is None or item.timestamp < timestamp:
            cls._create_or_update(session, {'timestamp' : timestamp, 'key' : key, 'value' : str(value)})

    @classmethod
    def set_newer(cls, db, key, value, timestamp=datetime.datetime.now()):
        with db.managed_session() as session:
            cls._set_newer(session, key, value, timestamp)

    @classmethod
    def set_if_unset(cls, db, key, value, timestamp=datetime.datetime.now()):
        logger.debug("%s::set_if_unset {%s : %s}", cls.__name__, key, value)
        return cls.find_or_create(db, {'timestamp' : timestamp, 'key' : key, 'value' : str(value)})

    @classmethod
    def get(cls, db, key):
        logger.debug("%s::get %s", cls.__name__, key)
        try:
            with db.managed_session() as session:
                instance = cls._find_one(session, {'key' : key})
                return instance.value
        except Exception:
            logger.warning("%s::get failed to get %s: %s", cls.__name__, key, traceback.format_exc())
            return None

    @classmethod
    def get_int(cls, db, key):
        value = cls.get(db, key)
        if value is not None:
            return int(value)

    @classmethod
    def get_time(cls, db, key):
        try:
            return datetime.datetime.strptime(cls.get(db, key), "%H:%M:%S").time()
        except Exception:
            return None
