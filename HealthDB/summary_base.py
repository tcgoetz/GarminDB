"""Object for implementing summary databse objects."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import datetime
from sqlalchemy import Column, Float, Time, Integer, func
from sqlalchemy.ext.hybrid import hybrid_property

import Fit.conversions as conversions
from utilities import db


class SummaryBase(db.DBObject):
    """Base class for implementing summary databse objects."""

    view_version = 9

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
    intensity_time_goal = Column(Time, nullable=False, default=datetime.time.min)
    steps = Column(Integer)
    steps_goal = Column(Integer)
    floors = Column(Float)
    floors_goal = Column(Float)
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
    calories_goal = Column(Integer)
    activities = Column(Integer)
    activities_calories = Column(Integer)
    activities_distance = Column(Integer)
    hydration_goal = Column(Integer)
    hydration_avg = Column(Integer)
    hydration_intake = Column(Integer)
    spo2_avg = Column(Float)
    spo2_min = Column(Float)
    rr_waking_avg = Column(Float)
    rr_max = Column(Float)
    rr_min = Column(Float)

    @hybrid_property
    def intensity_time_mins(self):
        """Return intensity time as minutes."""
        return (conversions.time_to_secs(self.intensity_time) / 60) if self.intensity_time is not None else 0

    @intensity_time_mins.expression
    def intensity_time_mins(cls):
        """Return intensity time as minutes."""
        return (cls._secs_from_time(cls.intensity_time) / 60)

    @hybrid_property
    def intensity_time_goal_mins(self):
        """Return intensity time as minutes."""
        return (conversions.time_to_secs(self.intensity_time_goal) / 60) if self.intensity_time_goal is not None else 0

    @intensity_time_goal_mins.expression
    def intensity_time_goal_mins(cls):
        """Return intensity time as minutes."""
        return (cls._secs_from_time(cls.intensity_time_goal) / 60)

    @hybrid_property
    def intensity_time_goal_percent(self):
        """Return the percentage of intensity time goal achieved."""
        if self.intensity_time and self.intensity_time_goal:
            intensity_time = conversions.time_to_secs(self.intensity_time)
            intensity_time_goal = conversions.time_to_secs(self.intensity_time_goal)
            if intensity_time and intensity_time_goal:
                return (intensity_time * 100) / intensity_time_goal
        return 0.0

    @intensity_time_goal_percent.expression
    def intensity_time_goal_percent(cls):
        """Return the percentage of intensity time goal achieved."""
        return func.round((cls._secs_from_time(cls.intensity_time) * 100) / cls._secs_from_time(cls.intensity_time_goal))

    @hybrid_property
    def steps_goal_percent(self):
        """Return the percentage of steps goal achieved."""
        return (self.steps * 100) / self.steps_goal if self.steps and self.steps_goal else 0.0

    @steps_goal_percent.expression
    def steps_goal_percent(cls):
        """Return the percentage of steps goal achieved."""
        return func.round((cls.steps * 100) / cls.steps_goal)

    @hybrid_property
    def floors_goal_percent(self):
        """Return the percentage of floors goal achieved."""
        return (self.floors * 100) / self.floors_goal if self.floors and self.floors_goal else 0.0

    @floors_goal_percent.expression
    def floors_goal_percent(cls):
        """Return the percentage of floors goal achieved."""
        return func.round((cls.floors * 100) / cls.floors_goal)

    @classmethod
    def create_summary_view(cls, db, selectable):
        """Create a view in the database from the passed in selectable."""
        cls._create_view(db, cls._get_default_view_name(), selectable, cls.time_col.desc())

    @classmethod
    def create_months_view(cls, db):
        """Create a monthly summary view in the database."""
        cols = [
            cls.time_col.label('first_day'),
            cls.round_col(cls.__tablename__ + '.rhr_avg', 'rhr'),
            cls.round_col(cls.__tablename__ + '.inactive_hr_avg', 'inactive_hr'),
            cls.round_col(cls.__tablename__ + '.weight_avg', 'weight'),
            cls.intensity_time.label('intensity_time'), cls.moderate_activity_time.label('moderate_activity_time'), cls.vigorous_activity_time.label('vigorous_activity_time'),
            cls.steps.label('steps'),
            # cls.steps_goal_percent,
            cls.round_col('round((steps * 100) / steps_goal)', 'steps_goal_percent'),
            cls.round_col(cls.__tablename__ + '.floors', 'floors'),
            # cls.floors_goal_percent,
            cls.round_col('round((floors * 100) / floors_goal)', 'floors_goal_percent'),
            cls.sleep_avg.label('sleep_avg'), cls.rem_sleep_avg.label('rem_sleep_avg'),
            cls.round_col(cls.__tablename__ + '.stress_avg', 'stress_avg'),
            cls.round_col(cls.__tablename__ + '.calories_avg', 'calories_avg'),
            cls.round_col(cls.__tablename__ + '.calories_bmr_avg', 'calories_bmr_avg'),
            cls.round_col(cls.__tablename__ + '.calories_active_avg', 'calories_active_avg'),
            cls.round_col(cls.__tablename__ + '.calories_goal', 'calories_goal'),
            cls.activities.label('activities'), cls.activities_calories.label('activities_calories'),
            cls.round_col(cls.__tablename__ + '.activities_distance', 'activities_distance'),
            cls.round_col(cls.__tablename__ + '.hydration_goal', 'hydration_goal'),
            cls.round_col(cls.__tablename__ + '.hydration_avg', 'hydration_avg'),
            cls.round_col(cls.__tablename__ + '.spo2_avg', 'spo2_avg'),
            cls.round_col(cls.__tablename__ + '.spo2_min', 'spo2_min'),
            cls.round_col(cls.__tablename__ + '.rr_waking_avg', 'rr_waking_avg')
        ]
        cls.create_summary_view(db, cols)

    @classmethod
    def create_weeks_view(cls, db):
        """Create a weekly summary view in the database."""
        cols = [
            cls.time_col.label('first_day'),
            cls.round_col(cls.__tablename__ + '.rhr_avg', 'rhr'),
            cls.round_col(cls.__tablename__ + '.inactive_hr_avg', 'inactive_hr'),
            cls.round_col(cls.__tablename__ + '.weight_avg', 'weight'),
            cls.intensity_time.label('intensity_time'), cls.moderate_activity_time.label('moderate_activity_time'), cls.vigorous_activity_time.label('vigorous_activity_time'),
            cls.steps.label('steps'),
            # cls.steps_goal_percent,
            cls.round_col('round((steps * 100) / steps_goal)', 'steps_goal_percent'),
            cls.round_col(cls.__tablename__ + '.floors', 'floors'),
            # cls.floors_goal_percent,
            cls.round_col('round((floors * 100) / floors_goal)', 'floors_goal_percent'),
            cls.sleep_avg.label('sleep_avg'), cls.rem_sleep_avg.label('rem_sleep_avg'),
            cls.round_col(cls.__tablename__ + '.stress_avg', 'stress_avg'),
            cls.round_col(cls.__tablename__ + '.calories_avg', 'calories_avg'),
            cls.round_col(cls.__tablename__ + '.calories_bmr_avg', 'calories_bmr_avg'),
            cls.round_col(cls.__tablename__ + '.calories_active_avg', 'calories_active_avg'),
            cls.round_col(cls.__tablename__ + '.calories_goal', 'calories_goal'),
            cls.activities.label('activities'), cls.activities_calories.label('activities_calories'),
            cls.round_col(cls.__tablename__ + '.activities_distance', 'activities_distance'),
            cls.round_col(cls.__tablename__ + '.hydration_goal', 'hydration_goal'),
            cls.round_col(cls.__tablename__ + '.hydration_avg', 'hydration_avg'),
            cls.round_col(cls.__tablename__ + '.spo2_avg', 'spo2_avg'),
            cls.round_col(cls.__tablename__ + '.spo2_min', 'spo2_min'),
            cls.round_col(cls.__tablename__ + '.rr_waking_avg', 'rr_waking_avg')
        ]
        cls.create_summary_view(db, cols)

    @classmethod
    def create_days_view(cls, db):
        """Create a daily summary view in the database."""
        cols = [
            cls.time_col.label('day'),
            cls.round_col(cls.__tablename__ + '.hr_avg', 'hr_avg'),
            cls.round_col(cls.__tablename__ + '.hr_min', 'hr_min'),
            cls.round_col(cls.__tablename__ + '.hr_max', 'hr_max'),
            cls.round_col(cls.__tablename__ + '.rhr_avg', 'rhr'),
            cls.round_col(cls.__tablename__ + '.inactive_hr_avg', 'inactive_hr'),
            cls.round_col(cls.__tablename__ + '.weight_avg', 'weight'),
            cls.intensity_time.label('intensity_time'), cls.moderate_activity_time.label('moderate_activity_time'), cls.vigorous_activity_time.label('vigorous_activity_time'),
            cls.steps.label('steps'),
            # cls.steps_goal_percent,
            cls.round_col('round((steps * 100) / steps_goal)', 'steps_goal_percent'),
            cls.round_col(cls.__tablename__ + '.floors', 'floors'),
            # cls.floors_goal_percent,
            cls.round_col('round((floors * 100) / floors_goal)', 'floors_goal_percent'),
            cls.sleep_avg.label('sleep_avg'), cls.rem_sleep_avg.label('rem_sleep_avg'),
            cls.round_col(cls.__tablename__ + '.stress_avg', 'stress_avg'),
            cls.round_col(cls.__tablename__ + '.calories_avg', 'calories_avg'),
            cls.round_col(cls.__tablename__ + '.calories_bmr_avg', 'calories_bmr_avg'),
            cls.round_col(cls.__tablename__ + '.calories_active_avg', 'calories_active_avg'),
            cls.round_col(cls.__tablename__ + '.calories_goal', 'calories_goal'),
            cls.activities.label('activities'), cls.activities_calories.label('activities_calories'),
            cls.round_col(cls.__tablename__ + '.activities_distance', 'activities_distance'),
            cls.round_col(cls.__tablename__ + '.hydration_goal', 'hydration_goal'),
            cls.round_col(cls.__tablename__ + '.hydration_avg', 'hydration_avg'),
            cls.round_col(cls.__tablename__ + '.spo2_avg', 'spo2_avg'),
            cls.round_col(cls.__tablename__ + '.spo2_min', 'spo2_min'),
            cls.round_col(cls.__tablename__ + '.rr_waking_avg', 'rr_waking_avg'),
            cls.round_col(cls.__tablename__ + '.rr_max', 'rr_max'),
            cls.round_col(cls.__tablename__ + '.rr_min', 'rr_min')
        ]
        cls.create_summary_view(db, cols)
