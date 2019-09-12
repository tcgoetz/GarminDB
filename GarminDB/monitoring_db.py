"""Objects representing a database and database objects for storing health monitoring data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import datetime
from sqlalchemy import Column, Integer, DateTime, Time, Float, Enum, FLOAT, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

import Fit
import HealthDB


logger = logging.getLogger(__name__)


class MonitoringDB(HealthDB.DB):
    """Class representing a databse storing daily health monitoring data from a Garmin device."""

    Base = declarative_base()
    db_name = 'garmin_monitoring'
    db_version = 5

    class _DbVersion(Base, HealthDB.DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        """
        Return an instance of MonitoringDB.

        Paramters:
            db_params_dict (dict): Config data for accessing the database
            debug (Boolean): enable debug logging
        """
        super(MonitoringDB, self).__init__(db_params_dict, debug)
        MonitoringDB.Base.metadata.create_all(self.engine)
        self.version = MonitoringDB._DbVersion()
        self.version.version_check(self, self.db_version)
        #
        self.tables = [MonitoringInfo, MonitoringHeartRate, MonitoringIntensity, MonitoringClimb, Monitoring]
        for table in self.tables:
            self.version.table_version_check(self, table)
            if not self.version.view_version_check(self, table):
                table.delete_view(self)


class MonitoringInfo(MonitoringDB.Base, HealthDB.DBObject):
    """Class representing data from a health monitoring file."""

    __tablename__ = 'monitoring_info'
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    file_id = Column(Integer, nullable=False)
    activity_type = Column(Enum(Fit.field_enums.ActivityType))
    resting_metabolic_rate = Column(Integer)
    cycles_to_distance = Column(FLOAT)
    cycles_to_calories = Column(FLOAT)

    time_col_name = 'timestamp'

    @classmethod
    def get_daily_bmr(cls, db, day_ts):
        """Return the base metabolic rate for the given day."""
        return cls.get_col_avg_of_max_per_day(db, cls.resting_metabolic_rate, day_ts, day_ts + datetime.timedelta(1))

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        stats = {
            'calories_bmr_avg' : cls.s_get_col_avg(session, cls.resting_metabolic_rate, start_ts, end_ts),
        }
        return stats


class MonitoringHeartRate(MonitoringDB.Base, HealthDB.DBObject):
    __tablename__ = 'monitoring_hr'
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    heart_rate = Column(Integer, nullable=False)

    time_col_name = 'timestamp'

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'hr_avg' : cls.s_get_col_avg(session, cls.heart_rate, start_ts, end_ts, True),
            'hr_min' : cls._get_col_min(session, cls.heart_rate, start_ts, end_ts, True),
            'hr_max' : cls._get_col_max(session, cls.heart_rate, start_ts, end_ts),
        }

    @classmethod
    def get_resting_heartrate(cls, db, wake_ts):
        start_ts = wake_ts - datetime.timedelta(0, 0, 0, 0, 10)
        return cls.get_col_min(db, cls.heart_rate, start_ts, wake_ts, True)


class MonitoringIntensity(MonitoringDB.Base, HealthDB.DBObject):
    """Class representing monitoring data about cardio minutes."""

    __tablename__ = 'monitoring_intensity'
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    moderate_activity_time = Column(Time, nullable=False, default=datetime.time.min)
    vigorous_activity_time = Column(Time, nullable=False, default=datetime.time.min)

    __table_args__ = (
        UniqueConstraint("timestamp", "moderate_activity_time", "vigorous_activity_time"),
    )

    time_col_name = 'timestamp'

    @hybrid_property
    def intensity_time(self):
        """Return the total cardio minutes, moderate and vigorous, with vigorous counted double."""
        return Fit.conversions.add_time(self.moderate_activity_time, self.vigorous_activity_time, 2)

    @intensity_time.expression
    def intensity_time(cls):
        return cls.time_from_secs(2 * cls._secs_from_time(cls.vigorous_activity_time) + cls._secs_from_time(cls.moderate_activity_time))

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'intensity_time'            : cls.s_get_time_col_sum(session, cls.intensity_time, start_ts, end_ts),
            'moderate_activity_time'    : cls.s_get_time_col_sum(session, cls.moderate_activity_time, start_ts, end_ts),
            'vigorous_activity_time'    : cls.s_get_time_col_sum(session, cls.vigorous_activity_time, start_ts, end_ts),
        }


class MonitoringClimb(MonitoringDB.Base, HealthDB.DBObject):
    """Class representing monitoring data about elvation gained."""

    __tablename__ = 'monitoring_climb'
    table_version = 1

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

    time_col_name = 'timestamp'

    @classmethod
    def get_stats(cls, session, func, start_ts, end_ts, measurement_system):
        """Return a dict of stats for table entries within the time span."""
        cum_ascent = func(session, cls.cum_ascent, start_ts, end_ts)
        if cum_ascent:
            if measurement_system is Fit.field_enums.DisplayMeasure.metric:
                floors = cum_ascent / cls.feet_to_floors
            else:
                floors = cum_ascent / cls.meters_to_floors
        else:
            floors = 0
        return {'floors' : floors}

    @classmethod
    def get_daily_stats(cls, session, day_ts, measurement_system):
        """Return a dict of stats for table entries for the given day."""
        stats = cls.get_stats(session, cls._get_col_max, day_ts, day_ts + datetime.timedelta(1), measurement_system)
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, session, first_day_ts, measurement_system):
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(7), measurement_system)
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, session, first_day_ts, last_day_ts, measurement_system):
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, last_day_ts, measurement_system)
        stats['first_day'] = first_day_ts
        return stats


class Monitoring(MonitoringDB.Base, HealthDB.DBObject):
    __tablename__ = 'monitoring'
    table_version = 1

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    activity_type = Column(Enum(Fit.field_enums.ActivityType))
    intensity = Column(Integer)
    duration = Column(Time, nullable=False, default=datetime.time.min)
    distance = Column(Float)
    cum_active_time = Column(Time, nullable=False, default=datetime.time.min)
    active_calories = Column(Integer)
    steps = Column(Integer)
    strokes = Column(Integer)
    cycles = Column(Float)

    __table_args__ = (
        UniqueConstraint("timestamp", "activity_type", "intensity", "duration"),
    )

    time_col_name = 'timestamp'

    @classmethod
    def get_active_calories(cls, session, activity_type, start_ts, end_ts):
        active_calories = cls.s_get_col_avg_of_max_per_day_for_value(session, cls.active_calories, cls.activity_type, activity_type, start_ts, end_ts)
        if active_calories is not None:
            return active_calories
        return 0

    @classmethod
    def get_stats(cls, session, func, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'steps'                 : func(session, cls.steps, start_ts, end_ts),
            'calories_active_avg'   : (
                cls.get_active_calories(session, Fit.field_enums.ActivityType.running, start_ts, end_ts) +
                cls.get_active_calories(session, Fit.field_enums.ActivityType.cycling, start_ts, end_ts) +
                cls.get_active_calories(session, Fit.field_enums.ActivityType.walking, start_ts, end_ts)
            )
        }

    @classmethod
    def get_daily_stats(cls, session, day_ts):
        """Return a dict of stats for table entries for the given day."""
        stats = cls.get_stats(session, cls._get_col_max, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, session, first_day_ts):
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, session, first_day_ts, last_day_ts):
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts
        return stats
