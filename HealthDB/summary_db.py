"""Objects representing a database and database objects summarizing health data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from sqlalchemy import Column, Date
from sqlalchemy.ext.declarative import declarative_base

import db
import summary_base as sb
import db_version as dbv
import key_value


logger = logging.getLogger(__name__)


class SummaryDB(db.DB):
    """Objects representing a database summarizing health data."""

    Base = declarative_base()
    db_name = 'summary'
    db_version = 6

    class DbVersion(Base, dbv.DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
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


class Summary(SummaryDB.Base, key_value.KeyValueObject):
    """Object representing health data statistics."""

    __tablename__ = 'summary'
    table_version = 1


class MonthsSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized monthly health data."""

    __tablename__ = 'months_summary'
    table_version = 1
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)
    time_col_name = 'first_day'


class WeeksSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized weekly health data."""

    __tablename__ = 'weeks_summary'
    table_version = 1
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)
    time_col_name = 'first_day'


class DaysSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized daily health data."""

    __tablename__ = 'days_summary'
    table_version = 1
    view_version = sb.SummaryBase.view_version

    day = Column(Date, primary_key=True)
    time_col_name = 'day'
