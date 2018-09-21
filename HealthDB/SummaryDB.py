#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class SummaryDB(DB):
    Base = declarative_base()
    db_name = 'summary'
    db_version = 4

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("SummaryDB: %s debug: %s ", repr(db_params_dict), str(debug))
        DB.__init__(self, db_params_dict, debug)
        SummaryDB.Base.metadata.create_all(self.engine)
        self.version = SummaryDB.DbVersion()
        self.version.version_check(self, self.db_version)


class Summary(SummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'


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


