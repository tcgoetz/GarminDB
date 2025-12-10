"""Objects representing a database and database objects for storing health monitoring data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import logging
import datetime
from sqlalchemy import Column, Integer, DateTime, Time, Float, Enum, FLOAT, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.ext.hybrid import hybrid_property

import fitfile
import idbutils


logger = logging.getLogger(__name__)

MonitoringDb = idbutils.DB.create('garmin_monitoring', 7, "Database for storing daily health monitoring data from a Garmin device.")


class MonitoringInfo(MonitoringDb.Base, idbutils.DbObject):
    """Class representing data from a health monitoring file."""

    __tablename__ = 'monitoring_info'

    db = MonitoringDb
    table_version = 1

    timestamp = Column(DateTime)
    file_id = Column(Integer, nullable=False)
    activity_type = Column(Enum(fitfile.field_enums.ActivityType))
    resting_metabolic_rate = Column(Integer)
    cycles_to_distance = Column(FLOAT)
    cycles_to_calories = Column(FLOAT)

    __table_args__ = (
        PrimaryKeyConstraint("timestamp", "activity_type"),
    )

    @classmethod
    def s_get_from_dict(cls, session, values_dict):
        """Return a single DeviceInfo instance for the given id."""
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp']).filter(cls.activity_type == values_dict['activity_type']).one_or_none()

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


class MonitoringHeartRate(MonitoringDb.Base, idbutils.DbObject):
    """Class that reprsents a database table holding resting heart rate data."""

    __tablename__ = 'monitoring_hr'

    db = MonitoringDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    heart_rate = Column(Integer, nullable=False)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'hr_avg' : cls.s_get_col_avg(session, cls.heart_rate, start_ts, end_ts, True),
            'hr_min' : cls.s_get_col_min(session, cls.heart_rate, start_ts, end_ts, True),
            'hr_max' : cls.s_get_col_max(session, cls.heart_rate, start_ts, end_ts),
        }

    @classmethod
    def get_resting_heartrate(cls, db, wake_ts):
        """Return a resting heart rate value for the day specified."""
        start_ts = wake_ts - datetime.timedelta(0, 0, 0, 0, 10)
        return cls.get_col_min(db, cls.heart_rate, start_ts, wake_ts, True)


class MonitoringIntensity(MonitoringDb.Base, idbutils.DbObject):
    """Class representing monitoring data about cardio minutes."""

    __tablename__ = 'monitoring_intensity'

    db = MonitoringDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    moderate_activity_time = Column(Time, nullable=False, default=datetime.time.min)
    vigorous_activity_time = Column(Time, nullable=False, default=datetime.time.min)

    __table_args__ = (
        UniqueConstraint("timestamp", "moderate_activity_time", "vigorous_activity_time"),
    )

    @hybrid_property
    def intensity_time(self):
        """Return the total cardio minutes, moderate and vigorous, with vigorous counted double."""
        return fitfile.conversions.add_time(self.moderate_activity_time, self.vigorous_activity_time, 2)

    @intensity_time.expression
    def intensity_time(cls):
        return cls._time_from_secs(2 * cls._secs_from_time(cls.vigorous_activity_time) + cls._secs_from_time(cls.moderate_activity_time))

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'intensity_time'            : cls.s_get_time_col_sum(session, cls.intensity_time, start_ts, end_ts),
            'moderate_activity_time'    : cls.s_get_time_col_sum(session, cls.moderate_activity_time, start_ts, end_ts),
            'vigorous_activity_time'    : cls.s_get_time_col_sum(session, cls.vigorous_activity_time, start_ts, end_ts),
        }


class MonitoringClimb(MonitoringDb.Base, idbutils.DbObject):
    """Class representing monitoring data about elvation gained."""

    __tablename__ = 'monitoring_climb'

    db = MonitoringDb
    table_version = 1

    feet_to_floors = 10
    meters_to_floors = 3

    timestamp = Column(DateTime, primary_key=True)
    # meters or feet
    ascent = Column(Float)
    descent = Column(Float)
    cum_ascent = Column(Float)
    cum_descent = Column(Float)

    __table_args__ = (
        UniqueConstraint("timestamp", "ascent", "descent", "cum_ascent", "cum_descent"),
    )

    @classmethod
    def get_stats(cls, session, func, start_ts, end_ts, measurement_system):
        """Return a dict of stats for table entries within the time span."""
        cum_ascent = func(session, cls.cum_ascent, start_ts, end_ts)
        if cum_ascent:
            if measurement_system is fitfile.field_enums.DisplayMeasure.metric:
                floors = cum_ascent / cls.feet_to_floors
            else:
                floors = cum_ascent / cls.meters_to_floors
        else:
            floors = 0
        return {'floors' : floors}

    @classmethod
    def get_daily_stats(cls, session, day_ts, measurement_system):
        """Return a dict of stats for table entries for the given day."""
        stats = cls.get_stats(session, cls.s_get_col_max, day_ts, day_ts + datetime.timedelta(1), measurement_system)
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, session, first_day_ts, measurement_system):
        """Return a dict of stats for table entries for the week day."""
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(7), measurement_system)
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, session, first_day_ts, last_day_ts, measurement_system):
        """Return a dict of stats for table entries for the month."""
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, last_day_ts, measurement_system)
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_yearly_stats(cls, session, year, measurement_system):
        """Return a dict of stats for table entries for the year."""
        first_day_ts = datetime.datetime(year, 1, 1)
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(365), measurement_system)
        stats['first_day'] = first_day_ts
        return stats


class Monitoring(MonitoringDb.Base, idbutils.DbObject):
    """A table containing monitoring data."""

    __tablename__ = 'monitoring'

    db = MonitoringDb
    table_version = 2

    timestamp = Column(DateTime, nullable=False)
    activity_type = Column(Enum(fitfile.field_enums.ActivityType))
    intensity = Column(Integer)
    duration = Column(Time, nullable=False, default=datetime.time.min)
    distance = Column(Float)
    cum_active_time = Column(Time, nullable=False, default=datetime.time.min)
    active_calories = Column(Integer)
    steps = Column(Integer)
    strokes = Column(Integer)
    cycles = Column(Float)

    __table_args__ = (PrimaryKeyConstraint("timestamp", "activity_type"),)

    @classmethod
    def s_get_from_dict(cls, session, values_dict):
        """Return a single DeviceInfo instance for the given id."""
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp']).filter(cls.activity_type == values_dict['activity_type']).one_or_none()

    @classmethod
    def get_active_calories(cls, session, activity_type, start_ts, end_ts):
        """Return the total calories burned during activity during the indicated period."""
        active_calories = cls.s_get_col_avg_of_max_per_day_for_value(session, cls.active_calories, cls.activity_type, activity_type, start_ts, end_ts)
        return active_calories if active_calories is not None else 0

    @classmethod
    def get_stats(cls, session, func, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'steps': func(session, cls.steps, start_ts, end_ts),
            'calories_active_avg': (
                cls.get_active_calories(session, fitfile.field_enums.ActivityType.running, start_ts, end_ts)
                + cls.get_active_calories(session, fitfile.field_enums.ActivityType.cycling, start_ts, end_ts)
                + cls.get_active_calories(session, fitfile.field_enums.ActivityType.walking, start_ts, end_ts)
            )
        }

    @classmethod
    def get_daily_stats(cls, session, day_ts):
        """Return a dict of stats for table entries for the given day."""
        stats = cls.get_stats(session, cls.s_get_col_max, day_ts, day_ts + datetime.timedelta(1))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, session, first_day_ts):
        """Return a dict of stats for table entries for the given week."""
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, session, first_day_ts, last_day_ts):
        """Return a dict of stats for table entries for the given week."""
        stats = cls.get_stats(session, cls.s_get_col_sum_of_max_per_day, first_day_ts, last_day_ts)
        stats['first_day'] = first_day_ts
        return stats


class MonitoringRespirationRate(MonitoringDb.Base, idbutils.DbObject):
    """Class that represents a database table holding respiration rate measured in breaths per minute."""

    __tablename__ = 'monitoring_rr'

    db = MonitoringDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    rr = Column(Float, nullable=False)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'rr_avg' : cls.s_get_col_avg(session, cls.rr, start_ts, end_ts, True),
            'rr_min' : cls.s_get_col_min(session, cls.rr, start_ts, end_ts, True),
            'rr_max' : cls.s_get_col_max(session, cls.rr, start_ts, end_ts),
        }


class MonitoringPulseOx(MonitoringDb.Base, idbutils.DbObject):
    """Class that represents a database table holding pulse ox measurements in percent."""

    __tablename__ = 'monitoring_pulse_ox'

    db = MonitoringDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    pulse_ox = Column(Float, nullable=False)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'pulse_ox_avg' : cls.s_get_col_avg(session, cls.pulse_ox, start_ts, end_ts, True),
            'pulse_ox_min' : cls.s_get_col_min(session, cls.pulse_ox, start_ts, end_ts, True),
            'pulse_ox_max' : cls.s_get_col_max(session, cls.pulse_ox, start_ts, end_ts),
        }


class MonitoringHrvValue(MonitoringDb.Base, idbutils.DbObject):
    """Class that represents a database table holding individual HRV (RMSSD) readings during sleep."""

    __tablename__ = 'monitoring_hrv_value'

    db = MonitoringDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    hrv = Column(Float, nullable=False)  # RMSSD in milliseconds

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'hrv_avg' : cls.s_get_col_avg(session, cls.hrv, start_ts, end_ts, True),
            'hrv_min' : cls.s_get_col_min(session, cls.hrv, start_ts, end_ts, True),
            'hrv_max' : cls.s_get_col_max(session, cls.hrv, start_ts, end_ts),
        }


class MonitoringHrvStatus(MonitoringDb.Base, idbutils.DbObject):
    """Class that represents a database table holding daily HRV status summaries."""

    __tablename__ = 'monitoring_hrv_status'

    db = MonitoringDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    weekly_average = Column(Float)       # Weekly average RMSSD in milliseconds
    last_night = Column(Float)           # Last night's RMSSD in milliseconds
    last_night_average = Column(Float)   # Last night's average RMSSD
    baseline_low = Column(Float)         # Baseline low bound
    baseline_high = Column(Float)        # Baseline high bound
    status = Column(Integer)             # HRV status: 0=unknown, 2=poor, 3=low, 4=balanced
    reading_count = Column(Integer)      # Number of readings

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dict of stats for table entries within the time span."""
        return {
            'hrv_weekly_avg' : cls.s_get_col_avg(session, cls.weekly_average, start_ts, end_ts, True),
            'hrv_last_night_avg' : cls.s_get_col_avg(session, cls.last_night, start_ts, end_ts, True),
            'hrv_baseline_low_avg' : cls.s_get_col_avg(session, cls.baseline_low, start_ts, end_ts, True),
            'hrv_baseline_high_avg' : cls.s_get_col_avg(session, cls.baseline_high, start_ts, end_ts, True),
        }
