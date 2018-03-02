#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *
from Fit import Conversions


logger = logging.getLogger(__name__)


class MonitoringDB(DB):
    Base = declarative_base()
    db_name = 'garmin_monitoring'
    db_version = 2

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("MonitoringDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        MonitoringDB.Base.metadata.create_all(self.engine)
        self.version = SummaryDB.DbVersion()
        self.version.version_check(self, self.db_version)


class ActivityType(MonitoringDB.Base, DBObject):
    __tablename__ = 'activity_type'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.name == values_dict['name'])

    @classmethod
    def get_id(cls, db, name):
        return cls.find_or_create_id(db, {'name' : name})


class MonitoringInfo(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_info'

    timestamp = Column(DateTime, primary_key=True)
    file_id = Column(Integer, nullable=False)
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))
    resting_metabolic_rate = Column(Integer)
    cycles_to_distance = Column(FLOAT)
    cycles_to_calories = Column(FLOAT)

    _relational_mappings = {
        'activity_type' : ('activity_type_id', ActivityType.get_id)
    }
    min_row_values = 3

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])


class MonitoringHeartRate(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_hr'

    timestamp = Column(DateTime, primary_key=True)
    heart_rate = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("timestamp", "heart_rate"),
    )

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

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

    @classmethod
    def get_resting_heartrate(cls, db, wake_ts):
        start_ts = wake_ts - datetime.timedelta(0, 0, 0, 0, 30)
        return cls.get_col_min(db, cls.heart_rate, start_ts, wake_ts, True)


class MonitoringIntensity(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_intensity'

    timestamp = Column(DateTime, primary_key=True)
    moderate_activity_time = Column(Time)
    vigorous_activity_time = Column(Time)

    __table_args__ = (
        UniqueConstraint("timestamp", "moderate_activity_time", "vigorous_activity_time"),
    )

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_stats(cls, db, func, start_ts, end_ts):
        moderate_activity_time = func(db, cls.moderate_activity_time, start_ts, end_ts)
        vigorous_activity_time = func(db, cls.vigorous_activity_time, start_ts, end_ts)
        intensity_time = datetime.time.min
        if moderate_activity_time:
            intensity_time = Conversions.add_time(intensity_time, moderate_activity_time)
        if vigorous_activity_time:
            intensity_time = Conversions.add_time(intensity_time, vigorous_activity_time, 2)
        stats = {
            'intensity_time'            : intensity_time,
            'moderate_activity_time'    : moderate_activity_time,
            'vigorous_activity_time'    : vigorous_activity_time,
        }
        return stats

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_stats(db, cls.get_time_col_sum, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts,
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_stats(db,cls.get_time_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts,
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_stats(db, cls.get_time_col_sum, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts,
        return stats


class MonitoringClimb(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_climb'

    feet_to_floors = 10
    meters_to_floors = 3

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    # meters or feet
    ascent = Column(Float)
    descent = Column(Float)
    cum_ascent = Column(Float)
    cum_descent = Column(Float)

    __table_args__ = (
        UniqueConstraint("timestamp", "ascent", "descent", "cum_ascent", "cum_descent"),
    )

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
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
    timestamp = Column(DateTime, nullable=False)
    activity_type_id = Column(Integer, ForeignKey('activity_type.id'))

    intensity = Column(Integer)

    duration = Column(Time)
    distance = Column(Float)
    cum_active_time = Column(Time)
    active_calories = Column(Integer)

    steps = Column(Integer)
    strokes = Column(Integer)
    cycles = Column(Float)

    __table_args__ = (
        UniqueConstraint("timestamp", "activity_type_id", "intensity", "duration"),
    )

    time_col = synonym("timestamp")
    _relational_mappings = {
        'activity_type' : ('activity_type_id', ActivityType.get_id)
    }
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_activity(cls, db, start_ts, end_ts):
        return db.query_session().query(cls.timestamp, cls.activity_type_id, cls.intensity).filter(cls.time_col >= start_ts).filter(cls.time_col < end_ts).all()

    @classmethod
    def get_activity_avg(cls, db, start_ts, end_ts):
        return cls.get_col_avg(db, cls.intensity, start_ts, end_ts)

    @classmethod
    def get_stats(cls, db, func, start_ts, end_ts):
        return {
            'steps'     : func(db, cls.steps, start_ts, end_ts),
        }

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

    @classmethod
    def get_inactive(cls, db, func, start_ts, end_ts):
        return session.query(cls).filter(cls.intensity == 0)

