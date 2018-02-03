#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class MSHealthDB(DB):
    Base = declarative_base()
    db_name = 'mshealth' + DB.file_suffix

    def __init__(self, db_path, debug=False):
        DB.__init__(self, db_path + "/" + MSHealthDB.db_name, debug)
        MSHealthDB.Base.metadata.create_all(self.engine)


class Attributes(MSHealthDB.Base, DBObject):
    __tablename__ = 'attributes'

    name = Column(String, primary_key=True)
    value = Column(String)

    _relational_mappings = {}
    col_translations = {
        'value' : str,
    }
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.name == values_dict['name'])


class DaysSummary(MSHealthDB.Base, DBObject):
    __tablename__ = 'days_summary'

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

    time_col = synonym("day")
    min_row_values = 1

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])

    @classmethod
    def get_hr_stats(cls, db, start_ts, end_ts):
        stats = {
            'hr_avg' : cls.get_col_avg(db, cls.hr_avg, start_ts, end_ts, True),
            'hr_min' : cls.get_col_min(db, cls.hr_min, start_ts, end_ts, True),
            'hr_max' : cls.get_col_max(db, cls.hr_max, start_ts, end_ts),
        }
        return stats

    @classmethod
    def get_activity_mins_stats(cls, db, func, start_ts, end_ts):
        active_hours = func(db, cls.active_hours, start_ts, end_ts)
        if active_hours is not None:
            intensity_mins = active_hours * 60
        else:
            intensity_mins = 0
        stats = {
            'intensity_mins' : intensity_mins,
            'moderate_activity_mins' : intensity_mins,
            'vigorous_activity_mins' : 0,
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
    def get_daily_stats(cls, db, day_ts):
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1))
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, day_ts, day_ts + datetime.timedelta(1)))
        stats.update(cls.get_hr_stats(db, day_ts, day_ts + datetime.timedelta(1)))
        stats['day'] = day_ts
        return stats

    @classmethod
    def get_weekly_stats(cls, db, first_day_ts):
        stats = cls.get_activity_mins_stats(db,cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7))
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats.update(cls.get_hr_stats(db, first_day_ts, first_day_ts + datetime.timedelta(7)))
        stats['first_day'] = first_day_ts
        return stats

    @classmethod
    def get_monthly_stats(cls, db, first_day_ts, last_day_ts):
        stats = cls.get_activity_mins_stats(db, cls.get_col_sum, first_day_ts, last_day_ts)
        stats.update(cls.get_floors_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_steps_stats(db, cls.get_col_sum, first_day_ts, last_day_ts))
        stats.update(cls.get_hr_stats(db, first_day_ts, last_day_ts))
        stats['first_day'] = first_day_ts
        return stats



class MSVaultWeight(MSHealthDB.Base, DBObject):
    __tablename__ = 'weight'

    timestamp = Column(DateTime, primary_key=True, unique=True)
    weight = Column(Float)

    time_col = synonym("timestamp")
    min_row_values = 2

    @classmethod
    def _find_query(cls, session, values_dict):
        return session.query(cls).filter(cls.timestamp == values_dict['timestamp'])

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'weight_avg' : cls.get_col_avg(db, cls.weight, start_ts, end_ts, True),
            'weight_min' : cls.get_col_min(db, cls.weight, start_ts, end_ts, True),
            'weight_max' : cls.get_col_max(db, cls.weight, start_ts, end_ts),
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

