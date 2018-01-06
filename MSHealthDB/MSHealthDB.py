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
    def find_query(cls, session, values_dict):
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
    miles_moved = Column(Integer)
    sleep_events = Column(Integer)
    sleep_calories = Column(Integer)
    sleep_secs = Column(Integer)
    walk_events = Column(Integer)
    walk_secs = Column(Integer)
    workout_calories = Column(Integer)
    miles_walked = Column(Integer)
    run_ewvents = Column(Integer)
    run_calories = Column(Integer)
    run_secs = Column(Integer)
    miles_run = Column(Integer)
    miles_golfed = Column(Integer)
    golf_calories = Column(Integer)
    golf_events = Column(Integer)
    golf_secs = Column(Integer)
    miles_biked = Column(Integer)
    uv_mins = Column(Integer)
    bike_secs = Column(Integer)
    bike_calories = Column(Integer)
    bike_events = Column(Integer)
    guided_workout_events = Column(Integer)
    guided_workout_calories = Column(Integer)
    guided_workout_secs = Column(Integer)

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 1

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])
