#!/usr/bin/env python

#
# copyright Tom Goetz
#

from DB import *


class MonitoringDB(DB):
    Base = declarative_base()
    db_name = 'garmin_monitoring.db'

    def __init__(self, db_path, debug=False):
        DB.__init__(self, db_path + "/" + MonitoringDB.db_name, debug)
        MonitoringDB.Base.metadata.create_all(self.engine)


class Device(MonitoringDB.Base, DBObject):
    __tablename__ = 'devices'

    serial_number = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    manufacturer = Column(String)
    garmin_product = Column(String)
    hardware_version = Column(String)

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 2

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.serial_number == values_dict['serial_number'])


class ActivityType(MonitoringDB.Base, DBObject):
    __tablename__ = 'activity_type'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 1

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.name == values_dict['name'])

    @classmethod
    def get_id(cls, db, name):
        return cls.find_or_create_id(db, {'name' : name})


class DeviceInfo(MonitoringDB.Base, DBObject):
    __tablename__ = 'device_info'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    file_id = Column(Integer, unique=True)
    serial_number = Column(Integer, ForeignKey('devices.serial_number'), nullable=False)
    software_version = Column(String)
    cum_operating_time = Column(Integer)
    battery_voltage = Column(String)

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 3

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])


class MonitoringInfo(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_info'

    timestamp = Column(DateTime, primary_key=True)
    file_id = Column(Integer, unique=True)
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))
    resting_metabolic_rate = Column(Integer)
    cycles_to_distance = Column(FLOAT)
    cycles_to_calories = Column(FLOAT)

    _relational_mappings = {
        'activity_type' : ('activity_type_id', ActivityType.get_id)
    }
    col_translations = {}
    min_row_values = 3

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])


class MonitoringHeartRate(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_hr'

    timestamp = Column(DateTime, primary_key=True)
    heart_rate = Column(Integer)

    __table_args__ = (
        UniqueConstraint("timestamp", "heart_rate"),
    )

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 2

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        end_ts = day_ts + datetime.timedelta(1)
        stats = {
            'day' : day_ts,
            'hr_avg' : cls.get_col_avg(db, cls.heart_rate, day_ts, end_ts),
            'hr_min' : cls.get_col_min(db, cls.heart_rate, day_ts, end_ts),
            'hr_max' : cls.get_col_max(db, cls.heart_rate, day_ts, end_ts),
        }
        return stats


class MonitoringIntensityMins(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_intensity_mins'

    timestamp = Column(DateTime, primary_key=True)
    moderate_activity_mins = Column(Integer)
    vigorous_activity_mins = Column(Integer)

    __table_args__ = (
        UniqueConstraint("timestamp", "moderate_activity_mins", "vigorous_activity_mins"),
    )

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 2

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        end_ts = day_ts + datetime.timedelta(1)
        stats = {
            'day' : day_ts,
            'moderate_activity_mins' : cls.get_col_sum(db, cls.moderate_activity_mins, day_ts, end_ts),
            'vigorous_activity_mins' : cls.get_col_sum(db, cls.vigorous_activity_mins, day_ts, end_ts),
        }
        return stats


class MonitoringClimb(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_climb'

    feet_to_floors = 10

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    ascent = Column(Integer)
    descent = Column(Integer)
    cum_ascent = Column(Integer)
    cum_descent = Column(Integer)

    __table_args__ = (
        UniqueConstraint("timestamp", "ascent", "descent", "cum_ascent", "cum_descent"),
    )

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 2

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        end_ts = day_ts + datetime.timedelta(1)
        stats = {
            'day' : day_ts,
            'floors' : cls.get_col_max(db, cls.cum_ascent, day_ts, end_ts) / cls.feet_to_floors,
        }
        return stats


class Monitoring(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))

    intensity = Column(Integer)

    duration = Column(Integer)
    distance = Column(Integer)
    cum_active_time = Column(Integer)
    active_calories = Column(Integer)

    steps = Column(Integer)
    strokes = Column(Integer)
    cycles = Column(Integer)

    __table_args__ = (
        UniqueConstraint("timestamp", "activity_type_id", "intensity", "duration"),
    )

    _relational_mappings = {
        'activity_type' : ('activity_type_id', ActivityType.get_id)
    }
    col_translations = {}
    min_row_values = 2

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        end_ts = day_ts + datetime.timedelta(1)
        stats = {
            'day' : day_ts,
            'steps' : cls.get_col_max(db, cls.steps, day_ts, end_ts),
        }
        return stats
