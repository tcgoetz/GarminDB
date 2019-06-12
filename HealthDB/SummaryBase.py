#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class SummaryBase(DBObject):
    view_version = 6

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

    @hybrid_property
    def intensity_time_goal_percent(self):
        if self.intensity_time is not None and self.intensity_time_goal is not None:
            return (Conversions.time_to_secs(self.intensity_time) * 100) / Conversions.time_to_secs(self.intensity_time_goal)
        return 0.0

    @intensity_time_goal_percent.expression
    def intensity_time_goal_percent(cls):
        return func.round((cls.secs_from_time(cls.intensity_time) * 100) / cls.secs_from_time(cls.intensity_time_goal))

    @hybrid_property
    def steps_goal_percent(self):
        if self.steps is not None and self.steps_goal is not None:
            return (self.steps * 100) / self.steps_goal
        return 0.0

    @steps_goal_percent.expression
    def steps_goal_percent(cls):
        return func.round((cls.steps * 100) / cls.steps_goal)

    @hybrid_property
    def floors_goal_percent(self):
        if self.floors is not None and self.floors_goal is not None:
            return (self.floors * 100) / self.floors_goal
        return 0.0

    @floors_goal_percent.expression
    def floors_goal_percent(cls):
        return func.round((cls.floors * 100) / cls.floors_goal)

    @classmethod
    def create_summary_view(cls, db, selectable):
        cls._create_view(db, cls.get_default_view_name(), selectable, cls.time_col.desc())

    @classmethod
    def create_months_view(cls, db):
        cls.create_summary_view(db,
            [
                cls.time_col.label('first_day'),
                cls.round_col(cls.__tablename__ + '.rhr_avg', 'rhr_avg'),
                cls.round_col(cls.__tablename__ + '.rhr_min', 'rhr_min'),
                cls.round_col(cls.__tablename__ + '.rhr_max', 'rhr_max'),
                cls.round_col(cls.__tablename__ + '.inactive_hr_avg', 'inactive_hr_avg'),
                cls.round_col(cls.__tablename__ + '.weight_avg', 'weight_avg'),
                cls.round_col(cls.__tablename__ + '.weight_min', 'weight_min'),
                cls.round_col(cls.__tablename__ + '.weight_max', 'weight_max'),
                cls.intensity_time.label('intensity_time'), cls.moderate_activity_time.label('moderate_activity_time'), cls.vigorous_activity_time.label('vigorous_activity_time'),
                cls.steps.label('steps'),
                # cls.steps_goal_percent,
                'round((steps * 100) / steps_goal) AS steps_goal_percent',
                cls.round_col(cls.__tablename__ + '.floors', 'floors'),
                # cls.floors_goal_percent,
                'round((floors * 100) / floors_goal) AS floors_goal_percent',
                cls.sleep_avg.label('sleep_avg'), cls.rem_sleep_avg.label('rem_sleep_avg'),
                cls.round_col(cls.__tablename__ + '.stress_avg', 'stress_avg'),
                cls.round_col(cls.__tablename__ + '.calories_avg', 'calories_avg'),
                cls.round_col(cls.__tablename__ + '.calories_bmr_avg', 'calories_bmr_avg'),
                cls.round_col(cls.__tablename__ + '.calories_active_avg', 'calories_active_avg'),
                cls.round_col(cls.__tablename__ + '.calories_goal', 'calories_goal'),
                cls.activities.label('activities'), cls.activities_calories.label('activities_calories'),
                cls.round_col(cls.__tablename__ + '.activities_distance', 'activities_distance')
            ]
        )

    @classmethod
    def create_weeks_view(cls, db):
        cls.create_summary_view(db,
            [
                cls.time_col.label('first_day'),
                cls.round_col(cls.__tablename__ + '.rhr_avg', 'rhr_avg'),
                cls.round_col(cls.__tablename__ + '.rhr_min', 'rhr_min'),
                cls.round_col(cls.__tablename__ + '.rhr_max', 'rhr_max'),
                cls.round_col(cls.__tablename__ + '.inactive_hr_avg', 'inactive_hr_avg'),
                cls.round_col(cls.__tablename__ + '.weight_avg', 'weight_avg'),
                cls.round_col(cls.__tablename__ + '.weight_min', 'weight_min'),
                cls.round_col(cls.__tablename__ + '.weight_max', 'weight_max'),
                cls.intensity_time.label('intensity_time'), cls.moderate_activity_time.label('moderate_activity_time'), cls.vigorous_activity_time.label('vigorous_activity_time'),
                cls.steps.label('steps'),
                # cls.steps_goal_percent,
                'round((steps * 100) / steps_goal) AS steps_goal_percent',
                cls.round_col(cls.__tablename__ + '.floors', 'floors'),
                #cls.floors_goal_percent,
                'round((floors * 100) / floors_goal) AS floors_goal_percent',
                cls.sleep_avg.label('sleep_avg'), cls.rem_sleep_avg.label('rem_sleep_avg'),
                cls.round_col(cls.__tablename__ + '.stress_avg', 'stress_avg'),
                cls.round_col(cls.__tablename__ + '.calories_avg', 'calories_avg'),
                cls.round_col(cls.__tablename__ + '.calories_bmr_avg', 'calories_bmr_avg'),
                cls.round_col(cls.__tablename__ + '.calories_active_avg', 'calories_active_avg'),
                cls.round_col(cls.__tablename__ + '.calories_goal', 'calories_goal'),
                cls.activities.label('activities'), cls.activities_calories.label('activities_calories'),
                cls.round_col(cls.__tablename__ + '.activities_distance', 'activities_distance')
            ]
        )

    @classmethod
    def create_days_view(cls, db):
        cls.create_summary_view(db,
            [
                cls.time_col.label('day'),
                cls.round_col(cls.__tablename__ + '.hr_avg', 'hr_avg'),
                cls.round_col(cls.__tablename__ + '.hr_min', 'hr_min'),
                cls.round_col(cls.__tablename__ + '.hr_max', 'hr_max'),
                cls.round_col(cls.__tablename__ + '.rhr_avg', 'rhr_avg'),
                cls.round_col(cls.__tablename__ + '.inactive_hr_avg', 'inactive_hr_avg'),
                cls.round_col(cls.__tablename__ + '.weight_avg', 'weight_avg'),
                cls.intensity_time.label('intensity_time'), cls.moderate_activity_time.label('moderate_activity_time'), cls.vigorous_activity_time.label('vigorous_activity_time'),
                cls.steps.label('steps'),
                #cls.steps_goal_percent,
                'round((steps * 100) / steps_goal) AS steps_goal_percent',
                cls.round_col(cls.__tablename__ + '.floors', 'floors'),
                #cls.floors_goal_percent,
                'round((floors * 100) / floors_goal) AS floors_goal_percent',
                cls.sleep_avg.label('sleep_avg'), cls.rem_sleep_avg.label('rem_sleep_avg'),
                cls.round_col(cls.__tablename__ + '.stress_avg', 'stress_avg'),
                cls.round_col(cls.__tablename__ + '.calories_avg', 'calories_avg'),
                cls.round_col(cls.__tablename__ + '.calories_bmr_avg', 'calories_bmr_avg'),
                cls.round_col(cls.__tablename__ + '.calories_active_avg', 'calories_active_avg'),
                cls.round_col(cls.__tablename__ + '.calories_goal', 'calories_goal'),
                cls.activities.label('activities'), cls.activities_calories.label('activities_calories'),
                cls.round_col(cls.__tablename__ + '.activities_distance', 'activities_distance')
            ]
        )
