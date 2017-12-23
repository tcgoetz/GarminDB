#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


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
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'hr_avg' : cls.get_col_avg(db, cls.heart_rate, start_ts, end_ts, True),
            'hr_min' : cls.get_col_min(db, cls.heart_rate, start_ts, end_ts, True),
            'hr_max' : cls.get_col_max(db, cls.heart_rate, start_ts, end_ts),
        }
        return stats

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_stats(db, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_stats(db, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts
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
    def get_stats(cls, db, func, start_ts, end_ts):
        moderate_activity_mins = func(db, cls.moderate_activity_mins, start_ts, end_ts)
        vigorous_activity_mins = func(db, cls.vigorous_activity_mins, start_ts, end_ts)
        intensity_mins = 0
        if moderate_activity_mins:
            intensity_mins += moderate_activity_mins
        if vigorous_activity_mins:
            intensity_mins += vigorous_activity_mins * 2
        stats = {
            'intensity_mins' : intensity_mins,
            'moderate_activity_mins' : moderate_activity_mins,
            'vigorous_activity_mins' : vigorous_activity_mins,
        }
        return stats

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1))
        stats['first_day'] = day_ts,
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_stats(db,cls.get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts,
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_stats(db, cls.get_col_sum_of_max_per_day, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts,
        return stats


class MonitoringClimb(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_climb'

    feet_to_floors = 10
    meters_to_floors = 3

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
    def get_stats(cls, db, func, start_ts, end_ts, english_units=False):
        cum_ascent = func(db, cls.cum_ascent, start_ts, end_ts)
        if cum_ascent:
            if english_units:
                floors = cum_ascent / cls.feet_to_floors
            else:
                floors = cum_ascent / cls.meters_to_floors
        else:
            floors = 0
        return { 'floors' : floors }

    @classmethod
    def get_daily_stats(cls, db, day_ts, english_units=False):
        stats = cls.get_stats(db, cls.get_col_max, day_ts, day_ts + datetime.timedelta(1), english_units)
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts, english_units=False):
        stats = cls.get_stats(db, cls.get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(7), english_units)
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts, english_units=False):
        stats = cls.get_stats(db, cls.get_col_sum_of_max_per_day, first_day_ts, last_day_ts, english_units)
        stats['first_day'] = first_day_ts
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
    def get_stats(cls, db, func, start_ts, end_ts):
        return { 'steps' : func(db, cls.steps, start_ts, end_ts) }

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_stats(db, cls.get_col_max, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_stats(db, cls.get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_stats(db, cls.get_col_sum_of_max_per_day, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts
        return stats
