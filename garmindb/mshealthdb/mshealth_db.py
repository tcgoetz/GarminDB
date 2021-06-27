"""Objects representing a database and database objects for storing health data from a Microsoft Health."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
import logging
from sqlalchemy import Column, Integer, Date, DateTime, Float

import fitfile.conversions as conversions
import idbutils


logger = logging.getLogger(__name__)

MSHealthDb = idbutils.DB.create('mshealth', 2, "Database for storing health data from Microsoft Health.")
Attributes = idbutils.DbObject.create('attributes', MSHealthDb, 1, base=idbutils.KeyValueObject, doc="key-value data from a Microsoft Health device.")


class DaysSummary(MSHealthDb.Base, idbutils.DbObject):
    """A table that holds summarized information about a day with one row per day."""

    __tablename__ = 'days_summary'

    db = MSHealthDb
    table_version = 1

    day = Column(Date, primary_key=True)
    calories = Column(Integer)
    steps = Column(Integer)
    floors = Column(Integer)
    hr_max = Column(Integer)
    hr_min = Column(Integer)
    hr_avg = Column(Integer)
    active_hours = Column(Integer)
    activity_secs = Column(Integer)
    activity_calories = Column(Integer)
    exercise_events = Column(Integer)
    exercise_calories = Column(Integer)
    exercise_secs = Column(Integer)
    miles_moved = Column(Float)
    sleep_events = Column(Integer)
    sleep_calories = Column(Integer)
    sleep_secs = Column(Integer)
    walk_events = Column(Integer)
    walk_secs = Column(Integer)
    workout_calories = Column(Integer)
    miles_walked = Column(Float)
    run_ewvents = Column(Integer)
    run_calories = Column(Integer)
    run_secs = Column(Integer)
    miles_run = Column(Float)
    miles_golfed = Column(Integer)
    golf_calories = Column(Integer)
    golf_events = Column(Integer)
    golf_secs = Column(Integer)
    miles_biked = Column(Float)
    uv_mins = Column(Integer)
    bike_secs = Column(Integer)
    bike_calories = Column(Integer)
    bike_events = Column(Integer)
    guided_workout_events = Column(Integer)
    guided_workout_calories = Column(Integer)
    guided_workout_secs = Column(Integer)

    @classmethod
    def get_hr_stats(cls, db, start_ts, end_ts):
        """Return a dictionary of aggregate heart rate statistics for the given time period."""
        return {
            'hr_avg' : cls.get_col_avg(db, cls.hr_avg, start_ts, end_ts, True),
            'hr_min' : cls.get_col_min(db, cls.hr_min, start_ts, end_ts, True),
            'hr_max' : cls.get_col_max(db, cls.hr_max, start_ts, end_ts),
        }

    @classmethod
    def get_activity_mins_stats(cls, db, func, start_ts, end_ts):
        """Return a dictionary of aggregate activity mins statistics for the given time period."""
        active_hours = func(db, cls.active_hours, start_ts, end_ts)
        if active_hours is not None:
            intensity_time = conversions.hours_to_dt_time(active_hours)
            stats = {
                'intensity_time' : intensity_time,
                'moderate_activity_time' : intensity_time,
                # 'vigorous_activity_time' : None,      Don't write where we have no data, may overwrite good data
            }
        else:
            stats = {}
        return stats

    @classmethod
    def get_floors_stats(cls, db, func, start_ts, end_ts):
        """Return a dictionary of aggregate floors statistics for the given time period."""
        return {'floors' : func(db, cls.floors, start_ts, end_ts)}

    @classmethod
    def get_steps_stats(cls, db, func, start_ts, end_ts):
        """Return a dictionary of aggregate steps statistics for the given time period."""
        return {'steps' : func(db, cls.steps, start_ts, end_ts)}

    @classmethod
    def get_sleep_stats(cls, db, start_ts, end_ts):
        """Return a dictionary of aggregate sleep statistics for the given time period."""
        return {
            'sleep_avg' : conversions.secs_to_dt_time(cls.get_col_avg(db, cls.sleep_secs, start_ts, end_ts, True)),
            'sleep_min' : conversions.secs_to_dt_time(cls.get_col_min(db, cls.sleep_secs, start_ts, end_ts, True)),
            'sleep_max' : conversions.secs_to_dt_time(cls.get_col_max(db, cls.sleep_secs, start_ts, end_ts)),
        }

    @classmethod
    def get_calories_stats(cls, db, start_ts, end_ts):
        """Return a dictionary of aggregate calorie statistics for the given time period."""
        calories_avg = cls.get_col_avg(db, cls.calories, start_ts, end_ts)
        calories_active_avg = cls.get_col_avg(db, cls.activity_calories, start_ts, end_ts)
        if calories_active_avg is not None:
            calories_bmr_avg = calories_avg - calories_active_avg
        else:
            calories_bmr_avg = calories_avg
        return {
            'calories_avg'          : calories_avg,
            'calories_bmr_avg'      : calories_bmr_avg,
            'calories_active_avg'   : calories_active_avg,
        }

    @classmethod
    def get_daily_stats(cls, db, day_ts):
        """Return a dictionary of aggregate statistics for the given day."""
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1))
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_hr_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_sleep_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_calories_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        """Return a dictionary of aggregate statistics for the given week."""
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_hr_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_sleep_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_calories_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        """Return a dictionary of aggregate statistics for the given month."""
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, last_day_ts)
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_hr_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.get_sleep_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.get_calories_stats(db, first_day_ts, last_day_ts))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_yearly_stats(cls, db, year):
        """Return a dictionary of aggregate statistics for the given year."""
        first_day_ts = datetime.datetime(year, 1, 1)
        last_day_ts = first_day_ts + datetime.timedelta(365)
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, last_day_ts)
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_hr_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.get_sleep_stats(db, first_day_ts, last_day_ts))
        stats.update(cls.get_calories_stats(db, first_day_ts, last_day_ts))
        stats['first_day'] = first_day_ts
        return stats


class MSVaultWeight(MSHealthDb.Base, idbutils.DbObject):
    """Class for a databse table holding weight data from Microsoft Health Vault."""

    __tablename__ = 'weight'

    db = MSHealthDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True, unique=True)
    weight = Column(Float)

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        stats = {
            'weight_avg' : cls.get_col_avg(db, cls.weight, start_ts, end_ts, True),
            'weight_min' : cls.get_col_min(db, cls.weight, start_ts, end_ts, True),
            'weight_max' : cls.get_col_max(db, cls.weight, start_ts, end_ts),
        }
        return stats
