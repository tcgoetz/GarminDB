"""Objects representing a database and database objects for storing health data from a FitBit device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import datetime
from sqlalchemy import Column, Integer, Date, Float, Time

import fitfile
import idbutils


logger = logging.getLogger(__name__)

FitBitDb = idbutils.DB.create('fitbit', 2, "Database for storing health data from FitBit.")
Attributes = idbutils.DbObject.create('attributes', FitBitDb, 1, base=idbutils.KeyValueObject, doc="key-value data from a FitBit device.")


class DaysSummary(FitBitDb.Base, idbutils.DbObject):
    """A table that holds summarized information about a day with one row per day."""

    __tablename__ = 'days_summary'

    db = FitBitDb
    table_version = 1

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

    @classmethod
    def __get_activity_mins_stats(cls, db, func, start_ts, end_ts):
        moderate_activity_time = fitfile.conversions.min_to_dt_time(func(db, cls.fairly_active_mins, start_ts, end_ts))
        vigorous_activity_time = fitfile.conversions.min_to_dt_time(func(db, cls.very_active_mins, start_ts, end_ts))
        intensity_time = datetime.time.min
        if moderate_activity_time:
            intensity_time = fitfile.conversions.add_time(intensity_time, moderate_activity_time)
        if vigorous_activity_time:
            intensity_time = fitfile.conversions.add_time(intensity_time, vigorous_activity_time, 2)
        stats = {
            'intensity_time': intensity_time,
            'moderate_activity_time': moderate_activity_time,
            'vigorous_activity_time': vigorous_activity_time,
        }
        return stats

    @classmethod
    def __get_floors_stats(cls, db, func, start_ts, end_ts):
        return {'floors': func(db, cls.floors, start_ts, end_ts)}

    @classmethod
    def __get_steps_stats(cls, db, func, start_ts, end_ts):
        return {'steps': func(db, cls.steps, start_ts, end_ts)}

    @classmethod
    def __get_weight_stats(cls, db, start_ts, end_ts):
        stats = {
            'weight_avg': cls.get_col_avg(db, cls.weight, start_ts, end_ts, True),
            'weight_min': cls.get_col_min(db, cls.weight, start_ts, end_ts, True),
            'weight_max': cls.get_col_max(db, cls.weight, start_ts, end_ts),
        }
        return stats

    @classmethod
    def __get_sleep_stats(cls, db, start_ts, end_ts):
        return {
            'sleep_avg': fitfile.conversions.min_to_dt_time(cls.get_col_avg(db, cls.asleep_mins, start_ts, end_ts, True)),
            'sleep_min': fitfile.conversions.min_to_dt_time(cls.get_col_min(db, cls.asleep_mins, start_ts, end_ts, True)),
            'sleep_max': fitfile.conversions.min_to_dt_time(cls.get_col_max(db, cls.asleep_mins, start_ts, end_ts)),
        }

    @classmethod
    def __get_calories_stats(cls, db, start_ts, end_ts):
        calories_bmr_avg = cls.get_col_avg(db, cls.calories_bmr, start_ts, end_ts)
        calories_active_avg = cls.get_col_avg(db, cls.activities_calories, start_ts, end_ts)
        if calories_bmr_avg is not None and calories_active_avg is not None:
            calories_avg = calories_bmr_avg + calories_active_avg
        else:
            calories_avg = None
        return {
            'calories_avg': calories_avg,
            'calories_bmr_avg': calories_bmr_avg,
            'calories_active_avg': calories_active_avg,
        }

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        """Return a dictionary of aggregate statistics for the given day."""
        stats = cls.__get_activity_mins_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1))
        stats.update(cls.__get_floors_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.__get_steps_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.__get_weight_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.__get_sleep_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.__get_calories_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        """Return a dictionary of aggregate statistics for the given week."""
        stats = cls.__get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats.update(cls.__get_floors_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.__get_steps_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.__get_weight_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.__get_sleep_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.__get_calories_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        """Return a dictionary of aggregate statistics for the given month."""
        stats = cls.__get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, last_day_ts)
        stats.update(cls.__get_floors_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.__get_steps_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.__get_weight_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.__get_sleep_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.__get_calories_stats(db, first_day_ts, last_day_ts))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_yearly_stats(cls, db, year):
        """Return a dictionary of aggregate statistics for the given year."""
        first_day_ts = datetime.datetime(year, 1, 1)
        last_day_ts = first_day_ts + datetime.timedelta(365)
        stats = cls.__get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, last_day_ts)
        stats.update(cls.__get_floors_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.__get_steps_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.__get_weight_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.__get_sleep_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.__get_calories_stats(db, first_day_ts, last_day_ts))
        stats['first_day'] = first_day_ts
        return stats
