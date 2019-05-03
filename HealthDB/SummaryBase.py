#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class SummaryBase(DBObject):
    view_version = 2

    hr_avg = Column(Float)
    hr_min = Column(Float)
    hr_max = Column(Float)
    rhr_avg = Column(Float)
    rhr_min = Column(Float)
    rhr_max = Column(Float)
    inactive_hr_avg = Column(Float)
    inactive_hr_min = Column(Float)
    inactive_hr_max = Column(Float)
    weight_avg = Column(Float)
    weight_min = Column(Float)
    weight_max = Column(Float)
    intensity_time = Column(Time, nullable=False, default=datetime.time.min)
    moderate_activity_time = Column(Time, nullable=False, default=datetime.time.min)
    vigorous_activity_time = Column(Time, nullable=False, default=datetime.time.min)
    steps = Column(Integer)
    floors = Column(Float)
    sleep_avg = Column(Time, nullable=False, default=datetime.time.min)
    sleep_min = Column(Time, nullable=False, default=datetime.time.min)
    sleep_max = Column(Time, nullable=False, default=datetime.time.min)
    rem_sleep_avg = Column(Time, nullable=False, default=datetime.time.min)
    rem_sleep_min = Column(Time, nullable=False, default=datetime.time.min)
    rem_sleep_max = Column(Time, nullable=False, default=datetime.time.min)
    stress_avg = Column(Integer)
    calories_avg = Column(Integer)
    calories_bmr_avg = Column(Integer)
    calories_active_avg = Column(Integer)
    activities = Column(Integer)
    activities_calories = Column(Integer)
    activities_distance = Column(Integer)

    @classmethod
    def create_months_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'first_day, ' +
                cls.round_col_text('rhr_avg') +
                'rhr_min, rhr_max, ' +
                cls.round_col_text('inactive_hr_avg') +
                cls.round_col_text('weight_avg') +
                cls.round_col_text('weight_min') +
                cls.round_col_text('weight_max') +
                'intensity_time, moderate_activity_time, vigorous_activity_time, ' +
                'steps, ' +
                cls.round_col_text('floors', places=0) +
                'sleep_avg, rem_sleep_avg, ' +
                cls.round_col_text('stress_avg') +
                cls.round_col_text('calories_avg', places=0) +
                cls.round_col_text('calories_bmr_avg', places=0) +
                cls.round_col_text('calories_active_avg', places=0) +
                'activities, activities_calories, ' +
                cls.round_col_text('activities_distance', seperator='') +
            'FROM %s ORDER BY first_day DESC' % cls.__tablename__
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)

    @classmethod
    def create_weeks_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'first_day, ' +
                cls.round_col_text('rhr_avg') +
                'rhr_min, rhr_max, ' +
                cls.round_col_text('inactive_hr_avg') +
                cls.round_col_text('weight_avg') +
                cls.round_col_text('weight_min') +
                cls.round_col_text('weight_max') +
                'intensity_time, moderate_activity_time, vigorous_activity_time, ' +
                'steps, ' +
                cls.round_col_text('floors', places=0) +
                'sleep_avg, rem_sleep_avg, ' +
                cls.round_col_text('stress_avg') +
                cls.round_col_text('calories_avg', places=0) +
                cls.round_col_text('calories_bmr_avg', places=0) +
                cls.round_col_text('calories_active_avg', places=0) +
                'activities, activities_calories, ' +
                cls.round_col_text('activities_distance', seperator='') +
            'FROM %s ORDER BY first_day DESC' % cls.__tablename__
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)

    @classmethod
    def create_days_view(cls, db):
        view_name = cls.__tablename__ + '_view'
        query_str = (
            'SELECT ' +
                'day, ' +
                cls.round_col_text('hr_avg') +
                'hr_min, hr_max, ' +
                cls.round_col_text('rhr_avg', 'rhr') +
                cls.round_col_text('inactive_hr_avg', 'inactive_hr') +
                cls.round_col_text('weight_avg', 'weight') +
                'intensity_time, moderate_activity_time, vigorous_activity_time, ' +
                'steps, ' +
                cls.round_col_text('floors', places=0) +
                'sleep_avg as sleep, ' +
                'rem_sleep_avg as rem_sleep, ' +
                cls.round_col_text('stress_avg', 'stress', places=0) +
                cls.round_col_text('calories_avg', 'calories', places=0) +
                cls.round_col_text('calories_avg', 'calories', places=0) +
                cls.round_col_text('calories_bmr_avg', 'calories_bmr', places=0) +
                cls.round_col_text('calories_active_avg', 'calories_active', places=0) +
                'activities, activities_calories, ' +
                cls.round_col_text('activities_distance', seperator='') +
            'FROM %s ORDER BY day DESC' % cls.__tablename__
        )
        cls.create_view_if_doesnt_exist(db, view_name, query_str)
