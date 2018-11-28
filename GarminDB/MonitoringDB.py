#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *
from Fit import Conversions, FieldEnums


logger = logging.getLogger(__name__)


class MonitoringDB(DB):
    Base = declarative_base()
    db_name = 'garmin_monitoring'
    db_version = 3

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("MonitoringDB: %s debug: %s ", repr(db_params_dict), str(debug))
        DB.__init__(self, db_params_dict, debug)
        MonitoringDB.Base.metadata.create_all(self.engine)
        self.version = MonitoringDB.DbVersion()
        self.version.version_check(self, self.db_version)


class MonitoringInfo(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_info'

    timestamp = Column(DateTime, primary_key=True)
    file_id = Column(Integer, nullable=False)
    activity_type = Column(Enum(FieldEnums.ActivityType))
    resting_metabolic_rate = Column(Integer)
    cycles_to_distance = Column(FLOAT)
    cycles_to_calories = Column(FLOAT)

    time_col = synonym("timestamp")
    min_row_values = 3

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_daily_bmr(cls, db, day_ts):
        return cls.get_col_avg_of_max_per_day(db, cls.resting_metabolic_rate, day_ts, day_ts + datetime.timedelta(1))

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'calories_bmr_avg' : cls.get_col_avg(db, cls.resting_metabolic_rate, start_ts, end_ts),
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


class MonitoringHeartRate(MonitoringDB.Base, DBObject):
    __tablename__ = 'monitoring_hr'

    timestamp = Column(DateTime, primary_key=True)
    heart_rate = Column(Integer, nullable=False)

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
        start_ts = wake_ts - datetime.timedelta(0, 0, 0, 0, 10)
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
    def get_stats(cls, db, start_ts, end_ts):
        moderate_activity_time = cls.get_time_col_sum(db, cls.moderate_activity_time, start_ts, end_ts)
        vigorous_activity_time = cls.get_time_col_sum(db, cls.vigorous_activity_time, start_ts, end_ts)
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
    activity_type = Column(Enum(FieldEnums.ActivityType))
    intensity = Column(Integer)
    duration = Column(Time)
    distance = Column(Float)
    cum_active_time = Column(Time)
    active_calories = Column(Integer)
    steps = Column(Integer)
    strokes = Column(Integer)
    cycles = Column(Float)

    __table_args__ = (
        UniqueConstraint("timestamp", "activity_type", "intensity", "duration"),
    )

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_activity(cls, db, start_ts, end_ts):
        return db.query_session().query(cls.timestamp, cls.activity_type, cls.intensity).filter(cls.time_col >= start_ts).filter(cls.time_col < end_ts).all()

    @classmethod
    def get_active_calories(cls, db, activity_type, start_ts, end_ts):
        active_calories = cls.get_col_avg_of_max_per_day_for_value(db, cls.active_calories, cls.activity_type, activity_type, start_ts, end_ts)
        if active_calories is not None:
            return active_calories
        return 0

    @classmethod
    def get_stats(cls, db, func, start_ts, end_ts):
        return {
            'steps'                 : func(db, cls.steps, start_ts, end_ts),
            'calories_active_avg'   : (
                cls.get_active_calories(db, FieldEnums.ActivityType.running, start_ts, end_ts) +
                cls.get_active_calories(db, FieldEnums.ActivityType.cycling, start_ts, end_ts) +
                cls.get_active_calories(db, FieldEnums.ActivityType.walking, start_ts, end_ts)
            )
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

