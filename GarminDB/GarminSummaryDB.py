#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class GarminSummaryDB(DB):
    Base = declarative_base()
    db_name = 'garmin_summary.db'

    def __init__(self, db_path, debug=False):
        logger.info("DB path %s debug %s " % (db_path, str(debug)))
        DB.__init__(self, db_path + "/" + GarminSummaryDB.db_name, debug)
        GarminSummaryDB.Base.metadata.create_all(self.engine)


class Summary(GarminSummaryDB.Base, DBObject):
    __tablename__ = 'summary'

    name = Column(String, primary_key=True)
    value = Column(String)

    _relational_mappings = {}
    col_translations = {
        'value' : str,
    }
    min_row_values = 2
    _updateable_fields = []

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.name == values_dict['name'])


class SummaryBase(DBObject):
    hr_avg = Column(Integer)
    hr_min = Column(Integer)
    hr_max = Column(Integer)
    weight_avg = Column(Integer)
    weight_min = Column(Integer)
    weight_max = Column(Integer)
    intensity_mins = Column(Integer)
    moderate_activity_mins = Column(Integer)
    vigorous_activity_mins = Column(Integer)
    steps = Column(Integer)
    floors = Column(Integer)

    _relational_mappings = {}
    col_translations = {}
    min_row_values = 1
    _updateable_fields = [
        'hr_avg', 'hr_min', 'hr_max',
        'weight_avg', 'weight_min', 'weight_max',
        'intensity_mins', 'moderate_activity_mins', 'vigorous_activity_mins',
        'steps', 'floors'
    ]


class MonthsSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'

    first_day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])


class WeeksSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'

    first_day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])


class DaysSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])


