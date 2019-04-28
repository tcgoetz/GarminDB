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
        super(SummaryDB, self).__init__(db_params_dict, debug)
        SummaryDB.Base.metadata.create_all(self.engine)
        # Init all table objects after SqlAlchemy's meta data create, but before using any tables.
        SummaryDB.DbVersion.setup()
        Summary.setup()
        MonthsSummary.setup()
        WeeksSummary.setup()
        DaysSummary.setup()
        #
        self.version = SummaryDB.DbVersion()
        self.version.version_check(self, self.db_version)


class Summary(SummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'


class MonthsSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'

    first_day = Column(Date, primary_key=True)
    time_col_name = 'first_day'


class WeeksSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'

    first_day = Column(Date, primary_key=True)
    time_col_name = 'first_day'


class DaysSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)
    time_col_name = 'day'

