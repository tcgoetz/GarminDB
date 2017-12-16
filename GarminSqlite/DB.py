#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, logging

from sqlalchemy import *
from sqlalchemy.ext.declarative import *
from sqlalchemy.orm import *

logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)


class DB():
    Base = declarative_base()

    def __init__(self, filename, debug=False):
        url = "sqlite:///" + filename
        self.engine = create_engine(url, echo=debug)
        DB.Base.metadata.create_all(self.engine)
        self.session_maker = sessionmaker(bind=self.engine)

    def session(self):
        return self.session_maker()


class DBObject():

    @classmethod
    def timedelta_to_secs(cls, timedelta):
        return (timedelta.days * 3600) + timedelta.seconds

    @classmethod
    def filename_from_pathname(cls, pathname):
        return os.path.basename(pathname)

    @classmethod
    def _filter_columns(cls, values_dict):
        filtered_cols = { key : value for key, value in values_dict.items() if key in cls.__dict__}
        if len(filtered_cols) != len(values_dict):
            logger.debug("filtered some cols for %s from %s" % (cls.__tablename__, repr(values_dict)))
        return filtered_cols

    @classmethod
    def _translate_columns(cls, values_dict):
        if len(cls.col_translations) == 0:
            return values_dict
        return {
            key :
            (cls.col_translations[key](value) if key in cls.col_translations else value)
            for key, value in values_dict.items()
        }

    @classmethod
    def _translate_column(cls, col_name, col_value):
        if len(cls.col_translations) == 0:
            return col_value
        return (cls.col_translations[col_name](col_value) if col_name in cls.col_translations else col_value)

    @classmethod
    def _rewrite_columns(cls, db, values_dict):
        if len(cls.col_rewrites) == 0:
            return values_dict
        return {
            (cls.col_rewrites[key][0] if key in cls.col_rewrites else key) :
            (cls.col_rewrites[key][1](db, value) if key in cls.col_rewrites else value)
            for key, value in values_dict.items()
        }

    @classmethod
    def _rewrite_column(cls, db, col_name, col_value):
        if len(cls.col_rewrites) == 0:
            return col_value
        return (cls.col_rewrites[col_name][1](db, col_value) if col_name in cls.col_rewrites else col_value)

    @classmethod
    def find(cls, db, col_value):
        name = cls.find_col.name
        value = cls._translate_column(name, (cls._rewrite_column(db, name, col_value)))
        return db.session().query(cls).filter(cls.find_col == value).all()

    @classmethod
    def find_one(cls, db, col_value):
        rows = cls.find(db, col_value)
        if len(rows) == 1:
            return rows[0]
        return None

    @classmethod
    def find_or_create_id(cls, db, col_value):
        instance = cls.find_one(db, col_value)
        if instance is None:
            cls.create(db, {cls.find_col.name : col_value})
            instance = cls.find_one(db, col_value)
        return instance.id

    @classmethod
    def create(cls, db, values_dict):
        session = db.session()
        session.add(cls(**cls._translate_columns(cls._filter_columns(cls._rewrite_columns(db, values_dict)))))
        session.commit()

    @classmethod
    def find_or_create(cls, db, values_dict):
        instance = cls.find_one(db, values_dict[cls.find_col.name])
        if instance is None:
            cls.create(db, values_dict)
            instance = cls.find_one(db, values_dict[cls.find_col.name])
        return instance

    def __repr__(self):
        classname = self.__class__.__name__
        col_name = cls.find_col.name
        col_value = self.__dict__[col_name]
        return ("<%s(timestamp=%s %s=%s)>" % (classname, col.name, col_value))


class Device(DB.Base, DBObject):
    __tablename__ = 'devices'

    serial_number = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    manufacturer = Column(String)
    garmin_product = Column(String)
    hardware_version = Column(String)

    find_col = synonym("serial_number")
    col_translations = {}
    col_rewrites = {}


class File(DB.Base, DBObject):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    find_col = synonym("name")
    col_translations = {
        'name' : DBObject.filename_from_pathname
    }
    col_rewrites = {}


class ActivityType(DB.Base, DBObject):
    __tablename__ = 'activity_type'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    find_col = synonym("name")
    col_translations = {}
    col_rewrites = {}


class DeviceInfo(DB.Base, DBObject):
    __tablename__ = 'device_info'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    file_id = Column(Integer, ForeignKey('files.id'))
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)
    software_version = Column(String)
    cum_operating_time = Column(Integer)
    battery_voltage = Column(String)

    find_col = synonym("timestamp")
    col_translations = {}
    col_rewrites = {
        'filename' : ('file_id', File.find_or_create_id)
    }


class MonitoringInfo(DB.Base, DBObject):
    __tablename__ = 'monitoring_info'

    timestamp = Column(DateTime, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))
    resting_metabolic_rate = Column(Integer)
    cycles_to_distance = Column(FLOAT)
    cycles_to_calories = Column(FLOAT)

    find_col = synonym("timestamp")
    col_translations = {}
    col_rewrites = {
        'filename' : ('file_id', File.find_or_create_id),
        'activity_type' : ('activity_type_id', ActivityType.find_or_create_id)
    }


class Monitoring(DB.Base, DBObject):
    __tablename__ = 'monitoring'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))
    heart_rate = Column(Integer)

    intensity = Column(Integer)
    intensity_mins = Column(Integer)
    moderate_activity = Column(Integer)
    vigorous_activity = Column(Integer)

    ascent = Column(Integer)
    descent = Column(Integer)
    ascent_floors = Column(Integer)
    descent_floors = Column(Integer)

    cum_ascent = Column(Integer)
    cum_descent = Column(Integer)
    cum_ascent_floors = Column(Integer)
    cum_descent_floors = Column(Integer)

    duration = Column(Integer)
    distance = Column(Integer)
    cum_active_time = Column(Integer)
    active_calories = Column(Integer)

    steps = Column(Integer)
    strokes = Column(Integer)
    cycles = Column(Integer)

    find_col = synonym("timestamp")
    col_translations = {
        'moderate_activity' : DBObject.timedelta_to_secs,
        'vigorous_activity' : DBObject.timedelta_to_secs,
        'duration' : DBObject.timedelta_to_secs,
        'cum_active_time' : DBObject.timedelta_to_secs
    }
    col_rewrites = {
        'activity_type' : ('activity_type_id', ActivityType.find_or_create_id)
    }
