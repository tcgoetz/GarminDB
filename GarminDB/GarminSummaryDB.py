#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class GarminSummaryDB(DB):
    Base = declarative_base()
    db_name = 'garmin_summary'

    def __init__(self, db_params_dict, debug=False):
        logger.info("GarminSummaryDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        GarminSummaryDB.Base.metadata.create_all(self.engine)


class Summary(GarminSummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'


class SummaryBase(DBObject):
    hr_avg = Column(Float)
    hr_min = Column(Float)
    hr_max = Column(Float)
    weight_avg = Column(Float)
    weight_min = Column(Float)
    weight_max = Column(Float)
    intensity_mins = Column(Integer)
    moderate_activity_mins = Column(Integer)
    vigorous_activity_mins = Column(Integer)
    steps = Column(Integer)
    floors = Column(Float)

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


