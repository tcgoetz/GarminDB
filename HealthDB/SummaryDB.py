#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class SummaryDB(DB):
    Base = declarative_base()
    db_name = 'summary'

    def __init__(self, db_params_dict, debug=False):
        logger.info("SummaryDB: %s debug: %s " % (repr(db_params_dict), str(debug)))
        DB.__init__(self, db_params_dict, debug)
        SummaryDB.Base.metadata.create_all(self.engine)


class Summary(SummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'


class SummaryBase(DBObject):
    hr_avg = Column(Float)
    hr_min = Column(Float)
    hr_max = Column(Float)
    weight_avg = Column(Float)
    weight_min = Column(Float)
    weight_max = Column(Float)
    stress_avg = Column(Float)
    stress_min = Column(Float)
    stress_max = Column(Float)
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


