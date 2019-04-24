#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class GarminSummaryDB(DB):
    Base = declarative_base()
    db_name = 'garmin_summary'
    db_version = 5

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("GarminSummaryDB: %s debug: %s ", repr(db_params_dict), str(debug))
        super(GarminSummaryDB, self).__init__(db_params_dict, debug)
        GarminSummaryDB.Base.metadata.create_all(self.engine)
        self.version = SummaryDB.DbVersion()
        self.version.version_check(self, self.db_version)
        MonthsSummary.create_view(self)
        WeeksSummary.create_view(self)
        DaysSummary.create_view(self)

class Summary(GarminSummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'


class MonthsSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'

    first_day = Column(Date, primary_key=True)

    time_col = synonym("first_day")

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'first_day,' +
                'rhr_avg, rhr_min, rhr_max,' +
                'inactive_hr_avg,' +
                'weight_avg, weight_min, weight_max,' +
                'intensity_time, moderate_activity_time, vigorous_activity_time,' +
                'steps, floors,' +
                'sleep_avg,' +
                'rem_sleep_avg,' +
                'stress_avg,' +
                'calories_avg,' +
                'calories_bmr_avg,' +
                'calories_active_avg,' +
                'activities, activities_calories, activities_distance '
            'FROM %s ORDER BY first_day DESC' % cls.__tablename__
        )
        cls._create_view(db, view_name, query_str)


class WeeksSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'

    first_day = Column(Date, primary_key=True)

    time_col = synonym("first_day")

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'first_day,' +
                'rhr_avg, rhr_min, rhr_max,' +
                'inactive_hr_avg,' +
                'weight_avg, weight_min, weight_max,' +
                'intensity_time, moderate_activity_time, vigorous_activity_time,' +
                'steps, floors,' +
                'sleep_avg,' +
                'rem_sleep_avg,' +
                'stress_avg,' +
                'calories_avg,' +
                'calories_bmr_avg,' +
                'calories_active_avg,' +
                'activities, activities_calories, activities_distance '
            'FROM %s ORDER BY first_day DESC' % cls.__tablename__
        )
        cls._create_view(db, view_name, query_str)


class DaysSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)

    time_col = synonym("day")

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])

    @classmethod
    def create_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'day,' +
                'hr_avg, hr_min, hr_max,' +
                'rhr_avg as rhr,' +
                'inactive_hr_avg,' +
                'weight_avg as weight,' +
                'intensity_time, moderate_activity_time, vigorous_activity_time,' +
                'steps, floors,' +
                'sleep_avg as sleep,' +
                'rem_sleep_avg as rem_sleep,' +
                'stress_avg,' +
                'calories_avg as calories,' +
                'calories_bmr_avg as calories_bmr,' +
                'calories_active_avg as calories_active,' +
                'activities, activities_calories, activities_distance '
            'FROM %s ORDER BY day DESC' % cls.__tablename__
        )
        cls._create_view(db, view_name, query_str)


class IntensityHR(GarminSummaryDB.Base, DBObject):
    __tablename__ = 'intensity_hr'

    timestamp = Column(DateTime, primary_key=True)
    intensity = Column(Integer, nullable=False)
    heart_rate = Column(Integer, nullable=False)

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'inactive_hr_avg' : cls.get_col_avg_for_value(db, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_min' : cls.get_col_min_for_value(db, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_max' : cls.get_col_max_for_value(db, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
        }
        return stats
