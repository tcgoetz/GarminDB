#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class GarminSummaryDB(DB):
    Base = declarative_base()
    db_name = 'garmin_summary'
    db_version = 3

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("GarminSummaryDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        GarminSummaryDB.Base.metadata.create_all(self.engine)
        self.version = SummaryDB.DbVersion()
        self.version.version_check(self, self.db_version)


class Summary(GarminSummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'


class MonthsSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'

    first_day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])


class WeeksSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'

    first_day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])


class DaysSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])


class RestingHeartRate(GarminSummaryDB.Base, DBObject):
    __tablename__ = 'resting_hr'

    day = Column(Date, primary_key=True)
    resting_heart_rate = Column(Float)

    time_col = synonym("day")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.day == values_dict['day'])

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'rhr_avg' : cls.get_col_avg(db, cls.resting_heart_rate, start_ts, end_ts, True),
            'rhr_min' : cls.get_col_min(db, cls.resting_heart_rate, start_ts, end_ts, True),
            'rhr_max' : cls.get_col_max(db, cls.resting_heart_rate, start_ts, end_ts),
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


class SleepEvents(GarminSummaryDB.Base, DBObject):
    __tablename__ = 'sleep_events'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, unique=True)
    event = Column(String)
    duration = Column(Time)

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_wake_time(cls, db, day_date):
        day_start_ts = datetime.datetime.combine(day_date, datetime.time.min)
        day_stop_ts = datetime.datetime.combine(day_date, datetime.time.max)
        values = cls.get_col_values(db, cls.timestamp, cls.event, 'wake_time', day_start_ts, day_stop_ts)
        if len(values) > 0:
            return values[0][0]


class Sleep(GarminSummaryDB.Base, DBObject):
    __tablename__ = 'sleep'

    day = Column(Date, primary_key=True)
    duration = Column(Time)

    time_col = synonym("day")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.day == values_dict['day'])

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        return {
            'sleep_avg' : cls.get_time_col_avg(db, cls.duration, start_ts, end_ts),
            'sleep_min' : cls.get_time_col_min(db, cls.duration, start_ts, end_ts),
            'sleep_max' : cls.get_time_col_max(db, cls.duration, start_ts, end_ts),
        }

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
