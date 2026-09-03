"""Objects representing a database and database objects for storing sleep data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import logging
from sqlalchemy import Column, Integer, DateTime, Time, Float, String, Enum, func

import fitfile
import idbutils


logger = logging.getLogger(__name__)


SleepDb = idbutils.DB.create('sleep', 1, "Database for storing sleep data from a Garmin device.")


class SleepEvents(SleepDb.Base, idbutils.DbObject):
    """Table that stores events recorded during sleep."""

    __tablename__ = 'sleep_events'

    db = SleepDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    event = Column(Enum(fitfile.fields.SleepActivityLevel))
    duration = Column(Time, nullable=False, default=datetime.time.min)

    @classmethod
    def get_wake_time(cls, db, day_date):
        """Return the wake time for a given date."""
        day_start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        day_stop_ts = datetime.datetime.combine(day_date, datetime.time.max)
        values = cls.get_col_values(db, cls.timestamp, cls.event, 'wake_time', day_start_ts, day_stop_ts)
        if len(values) > 0:
            return values[0][0]

    @classmethod
    def get_level_time(cls, session, day_date, sleep_level):
        """Return the time in a given sleep level for a given date."""
        day_start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        day_stop_ts = datetime.datetime.combine(day_date, datetime.time.max)
        result = cls._s_query(session, cls._time_from_secs(func.sum(cls._secs_from_time(cls.duration))), None, day_start_ts, day_stop_ts,
                              cls._secs_from_time(cls.duration)).filter(cls.event == sleep_level).scalar()
        return result if result is not None else datetime.time.min

    @classmethod
    def get_day_stats(cls, session, day_date):
        """Return a dictionary of aggregate statistics for the given time period."""
        deep_sleep = cls.get_level_time(session, day_date, 'deep_sleep')
        light_sleep = cls.get_level_time(session, day_date, 'light_sleep')
        rem_sleep = cls.get_level_time(session, day_date, 'rem_sleep')
        awake = cls.get_level_time(session, day_date, 'awake')
        total_sleep = fitfile.conversions.add_time(
            fitfile.conversions.add_time(deep_sleep, light_sleep), rem_sleep
        )
        return {
            'total_sleep': total_sleep,
            'deep_sleep': deep_sleep,
            'light_sleep': light_sleep,
            'rem_sleep': rem_sleep,
            'awake': awake
        }


class Sleep(SleepDb.Base, idbutils.DbObject):
    """Class representing a sleep session. Data in this table comes for FIT files"""

    __tablename__ = 'sleep'

    db = SleepDb
    table_version = 1

    day = Column(DateTime, primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime)
    total_sleep = Column(Time, nullable=False, default=datetime.time.min)
    deep_sleep = Column(Time, nullable=False, default=datetime.time.min)
    light_sleep = Column(Time, nullable=False, default=datetime.time.min)
    rem_sleep = Column(Time, nullable=False, default=datetime.time.min)
    awake = Column(Time, nullable=False, default=datetime.time.min)
    avg_spo2 = Column(Float)
    avg_rr = Column(Float)
    avg_stress = Column(Float)
    score = Column(Integer)
    qualifier = Column(String)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'sleep_avg'         : cls.s_get_time_col_avg(session, cls.total_sleep, start_ts, end_ts),
            'sleep_min'         : cls.s_get_time_col_min(session, cls.total_sleep, start_ts, end_ts),
            'sleep_max'         : cls.s_get_time_col_max(session, cls.total_sleep, start_ts, end_ts),
            'rem_sleep_avg'     : cls.s_get_time_col_avg(session, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_min'     : cls.s_get_time_col_min(session, cls.rem_sleep, start_ts, end_ts),
            'rem_sleep_max'     : cls.s_get_time_col_max(session, cls.rem_sleep, start_ts, end_ts),
            'sleep_score_avg'   : cls.s_get_col_avg(session, cls.score, start_ts, end_ts),
            'sleep_score_min'   : cls.s_get_col_min(session, cls.score, start_ts, end_ts),
            'sleep_score_max'   : cls.s_get_col_max(session, cls.score, start_ts, end_ts),
        }


class SleepAssessments(SleepDb.Base, idbutils.DbObject):
    """Table that stores sleep assessments."""

    __tablename__ = 'sleep_assessments'

    db = SleepDb
    table_version = 1

    day = Column(DateTime, primary_key=True)
    combined_awake_score = Column(Integer)
    awake_time_score = Column(Integer)
    awakenings_count_score = Column(Integer)
    sleep_duration_score = Column(Integer)
    light_sleep_score = Column(Integer)
    overall_sleep_score = Column(Integer)
    sleep_quality_score = Column(Integer)
    sleep_recovery_score = Column(Integer)
    rem_sleep_score = Column(Integer)
    sleep_restlessness_score = Column(Integer)
    awakenings_count = Column(Integer)
