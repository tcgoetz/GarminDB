#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class FitBitDB(DB):
    Base = declarative_base()
    db_name = 'fitbit.db'

    def __init__(self, db_path, debug=False):
        DB.__init__(self, db_path + "/" + FitBitDB.db_name, debug)
        FitBitDB.Base.metadata.create_all(self.engine)


class Attributes(FitBitDB.Base, DBObject):
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


class DaysSummary(FitBitDB.Base, DBObject):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)
    calories_in = Column(Integer)
    log_water = Column(Integer)
    calories = Column(Integer)
    calories_bmr = Column(Integer)
    steps = Column(Integer)
    distance = Column(Integer)
    floors = Column(Integer)
    elevation = Column(Integer)
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
    weight = Column(Integer)
    bmi = Column(Integer)

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 1

    @classmethod
    def find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])
