#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *

logger = logging.getLogger(__name__)


class FitBitDB(DB):
    Base = declarative_base()
    db_name = 'fitbit'

    def __init__(self, db_params_dict, debug=False):
        logger.info("FitBitDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        FitBitDB.Base.metadata.create_all(self.engine)


class Attributes(FitBitDB.Base, KeyValueObject):
    __tablename__ = 'attributes'


class DaysSummary(FitBitDB.Base, DBObject):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)
    calories_in = Column(Integer)
    log_water = Column(Float)
    calories = Column(Integer)
    calories_bmr = Column(Integer)
    steps = Column(Integer)
    distance = Column(Float)
    floors = Column(Integer)
    elevation = Column(Float)
    sedentary_mins = Column(Integer)
    lightly_active_mins = Column(Integer)
    fairly_active_mins = Column(Integer)
    very_active_mins = Column(Integer)
    activities_calories = Column(Integer)
    sleep_start = Column(Time)
    in_bed_mins = Column(Integer)
    asleep_mins = Column(Integer)
    awakenings_count = Column(Integer)
    awake_mins = Column(Integer)
    to_fall_asleep_mins = Column(Integer)
    after_wakeup_mins = Column(Integer)
    sleep_efficiency = Column(Integer)
    weight = Column(Float)
    bmi = Column(Float)

    time_col = synonym("day")
    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])

    @classmethod
    def get_activity_mins_stats(cls, db, func, start_ts, end_ts):
        moderate_activity_mins = func(db, cls.fairly_active_mins, start_ts, end_ts)
        vigorous_activity_mins = func(db, cls.very_active_mins, start_ts, end_ts)
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
    def get_floors_stats(cls, db, func, start_ts, end_ts):
        floors = func(db, cls.floors, start_ts, end_ts)
        return { 'floors' : floors }

    @classmethod
    def get_steps_stats(cls, db, func, start_ts, end_ts):
        return { 'steps' : func(db, cls.steps, start_ts, end_ts) }

    @classmethod
    def get_weight_stats(cls, db, start_ts, end_ts):
        stats = {
            'weight_avg' : cls.get_col_avg(db, cls.weight, start_ts, end_ts, True),
            'weight_min' : cls.get_col_min(db, cls.weight, start_ts, end_ts, True),
            'weight_max' : cls.get_col_max(db, cls.weight, start_ts, end_ts),
        }
        return stats

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1))
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_weight_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_activity_mins_stats(db,cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_weight_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, last_day_ts)
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_weight_stats(db, first_day_ts, last_day_ts))
        stats['first_day'] = first_day_ts
        return stats

