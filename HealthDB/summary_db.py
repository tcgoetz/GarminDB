"""Objects representing a database and database objects summarizing health data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from sqlalchemy import Column, Date
from sqlalchemy.ext.declarative import declarative_base

from utilities import db
import HealthDB.summary_base as sb
from utilities import db_version as dbv
from utilities import key_value


logger = logging.getLogger(__name__)


class SummaryDB(db.DB):
    """Objects representing a database summarizing health data."""

    Base = declarative_base()

    db_tables = []
    db_name = 'summary'
    db_version = 6

    class _DbVersion(Base, dbv.DbVersionObject):
        pass

    def __init__(self, db_params, debug=False):
        """
        Return an instance of SummaryDB.

        Paramters:
            db_params (dict): Config data for accessing the database
            debug (Boolean): enable debug logging
        """
        super().__init__(db_params, debug)
        SummaryDB.Base.metadata.create_all(self.engine)
        version = SummaryDB._DbVersion()
        version.version_check(self, self.db_version)
        #
        for table in self.db_tables:
            version.table_version_check(self, table)
            if not version.view_version_check(self, table):
                table.delete_view(self)


class Summary(SummaryDB.Base, key_value.KeyValueObject):
    """Object representing health data statistics."""

    __tablename__ = 'summary'

    db = SummaryDB
    table_version = 1


class YearsSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized monthly health data."""

    __tablename__ = 'years_summary'

    db = SummaryDB
    table_version = 2
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        cls.create_years_view(db)


class MonthsSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized monthly health data."""

    __tablename__ = 'months_summary'

    db = SummaryDB
    table_version = 2
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        cls.create_months_view(db)


class WeeksSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized weekly health data."""

    __tablename__ = 'weeks_summary'

    db = SummaryDB
    table_version = 2
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        cls.create_weeks_view(db)


class DaysSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized daily health data."""

    __tablename__ = 'days_summary'

    db = SummaryDB
    table_version = 2
    view_version = sb.SummaryBase.view_version

    day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        cls.create_days_view(db)
