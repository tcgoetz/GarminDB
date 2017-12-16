#!/usr/bin/env python

#
# copyright Tom Goetz
#

import logging

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
    def _filter_columns(cls, values_dict):
        return { key : value for key, value in values_dict.items() if key in cls.__dict__}

    @classmethod
    def _translate_columns(cls, values_dict):
        filtered_values_dict = cls._filter_columns(values_dict)
        if len(cls.col_translations) == 0:
            logger.debug("translate_columns: done %s" % repr(filtered_values_dict))
            return filtered_values_dict
        logger.debug("translate_columns: doing %s" % repr(filtered_values_dict))
        return { key : (cls.col_translations[key](value) if key in cls.col_translations else value) for key, value in filtered_values_dict.items()}

    @classmethod
    def find(cls, db, col_value):
        logger.debug("find where %s == %s" % (cls.find_col, str(col_value)))
        return db.session().query(cls).filter(cls.find_col == col_value).all()

    @classmethod
    def find_one(cls, db, col_value):
        logger.debug("find_one where %s == %s" % (cls.find_col, str(col_value)))
        rows = cls.find(db, col_value)
        if len(rows) == 1:
            return rows[0]
        return None

    @classmethod
    def create(cls, db, values_dict):
        logger.debug("create %s" % repr(values_dict))
        session = db.session()
        session.add(cls(**cls._translate_columns(values_dict)))
#        session.add(cls(**cls._filter_columns(values_dict)))
        session.commit()

    @classmethod
    def find_or_create(cls, db, values_dict):
        logger.debug("find_or_create %s" % repr(values_dict))
        instance = cls.find_one(db, values_dict[cls.find_col.name])
        if instance is None:
            cls.create(db, values_dict)
            instance = cls.find_one(db, values_dict[cls.find_col.name])
        logger.info("find_or_create return %s" % repr(instance))
        return instance


class Device(DB.Base, DBObject):
    __tablename__ = 'devices'

    serial_number = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    manufacturer = Column(String)
    garmin_product = Column(String)
    hardware_version = Column(String)

    find_col = synonym("serial_number")
    col_translations = {}

    def __repr__(self):
        return ("<Device(timestamp=%s manufacturer='%s' garmin_product='%s' serial_number='%s' hardware_version='%s')>"
            % (self.timestamp, self.manufacturer, self.garmin_product, self.serial_number, self.hardware_version))


class ActivityType(DB.Base, DBObject):
    __tablename__ = 'activity_type'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    find_col = synonym("name")
    col_translations = {}

    def __repr__(self):
        return "<ActivityType(id='%d' name='%s')>" % (self.id, self.name)


class DeviceInfo(DB.Base, DBObject):
    __tablename__ = 'device_info'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    filename = Column(String)
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)
    software_version = Column(String)
    cum_operating_time = Column(Integer)
    batery_voltage = Column(String)

    find_col = synonym("timestamp")
    col_translations = {}

    def __repr__(self):
        return ("<DeviceInfo(id=%d timestamp=%s filename='%s' serial_number=%d software_version='%s' cum_operating_time=%s batery_voltage='%s')>" 
            % (self.id, str(self.timestamp), self.filename, self.serial_number, self.software_version,
                str(self.cum_operating_time), self.batery_voltage))


class MonitoringInfo(DB.Base, DBObject):
    __tablename__ = 'monitoring_info'

    timestamp = Column(DateTime, primary_key=True)
    filename = Column(String)
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))
    resting_metabolic_rate = Column(Integer)
    cycles_to_distance = Column(FLOAT)
    cycles_to_calories = Column(FLOAT)

    find_col = synonym("timestamp")
    col_translations = {}

    def __repr__(self):
        return ("<MonitoringInfo(timestamp=%s filename='%s' activity_type_id=%d resting_metabolic_rate=%d cycles_to_distance=%f cycles_to_calories=%f)>"
            % (str(self.timestamp), self.filename, self.activity_type_id, self.resting_metabolic_rate,
               self.cycles_to_distance, self.cycles_to_calories))


class Monitoring(DB.Base, DBObject):
    __tablename__ = 'monitoring'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))
    heart_rate = Column(Integer)
    intensity = Column(Integer)

    cum_ascent = Column(Integer)
    cum_descent = Column(Integer)
    cum_ascent_floors = Column(Integer)
    cum_descent_floors = Column(Integer)

    duration = Column(Interval)
    distance = Column(Integer)
    cum_active_time = Column(Integer)
    active_calories = Column(Integer)

    steps = Column(Integer)
    strokes = Column(Integer)
    cycles = Column(Integer)

    find_col = synonym("timestamp")
    col_translations = {
        'cum_active_time' : DBObject.timedelta_to_secs
    }

    @classmethod
    def translate_columns(cls, values_dict):
        filtered_values_dict = DBObject.filter_columns(values_dict)
        return DBObject.filter_columns(values_dict)

    def __repr__(self):
        return ("<MonitoringInfo(timestamp=%s activity_type_id=%s heart_rate=%s intensity=%s)>"
            % (str(self.timestamp), str(self.activity_type_id), str(self.heart_rate), str(self.intensity)))
