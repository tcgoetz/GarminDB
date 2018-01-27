#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


class SummaryDB(DB):
    Base = declarative_base()
    db_name = 'summary.db'

    def __init__(self, db_path, debug=False):
        logger.info("DB path %s debug %s " % (db_path, str(debug)))
        DB.__init__(self, db_path + "/" + SummaryDB.db_name, debug)
        SummaryDB.Base.metadata.create_all(self.engine)


class Summary(SummaryDB.Base, DBObject):
    __tablename__ = 'summary'

    name = Column(String, primary_key=True)
    value = Column(String)

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

    min_row_values = 1


class MonthsSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'

    first_day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])


class WeeksSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'

    first_day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.first_day == values_dict['first_day'])


class DaysSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)

    @classmethod
    def _find_query(cls, session, values_dict):
        return  session.query(cls).filter(cls.day == values_dict['day'])


