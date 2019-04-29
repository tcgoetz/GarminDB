#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class SummaryBase(DBObject):
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
    intensity_time = Column(Time)
    moderate_activity_time = Column(Time)
    vigorous_activity_time = Column(Time)
    steps = Column(Integer)
    floors = Column(Float)
    sleep_avg = Column(Time)
    sleep_min = Column(Time)
    sleep_max = Column(Time)
    rem_sleep_avg = Column(Time)
    rem_sleep_min = Column(Time)
    rem_sleep_max = Column(Time)
    stress_avg = Column(Integer)
    calories_avg = Column(Integer)
    calories_bmr_avg = Column(Integer)
    calories_active_avg = Column(Integer)
    activities = Column(Integer)
    activities_calories = Column(Integer)
    activities_distance = Column(Integer)
