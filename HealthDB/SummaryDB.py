#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class SummaryDB(DB):
    Base = declarative_base()
    db_name = 'summary'
    db_version = 6

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("SummaryDB: %s debug: %s ", repr(db_params_dict), str(debug))
        super(SummaryDB, self).__init__(db_params_dict, debug)
        SummaryDB.Base.metadata.create_all(self.engine)
        version = SummaryDB.DbVersion()
        version.version_check(self, self.db_version)
        #
        self.tables = [Summary, MonthsSummary, WeeksSummary, DaysSummary]
        for table in self.tables:
            version.table_version_check(self, table)
            if not version.view_version_check(self, table):
                table.delete_view(self)
        #
        MonthsSummary.create_months_view(self)
        WeeksSummary.create_weeks_view(self)
        DaysSummary.create_days_view(self)


class Summary(SummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'
    table_version = 1


class MonthsSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'
    table_version = 1
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)
    time_col_name = 'first_day'


class WeeksSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'
    table_version = 1
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)
    time_col_name = 'first_day'


class DaysSummary(SummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'
    table_version = 1
    view_version = SummaryBase.view_version

    day = Column(Date, primary_key=True)
    time_col_name = 'day'

