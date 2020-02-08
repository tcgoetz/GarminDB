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
        """Stores version information for this databse and it's tables."""


class Summary(SummaryDB.Base, key_value.KeyValueObject):
    """Object representing health data statistics."""

    __tablename__ = 'summary'

    db = SummaryDB
    table_version = 1


class YearsSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized monthly health data."""

    __tablename__ = 'years_summary'

    db = SummaryDB
    table_version = 3
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_years_view(db)


class MonthsSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized monthly health data."""

    __tablename__ = 'months_summary'

    db = SummaryDB
    table_version = 3
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_months_view(db)


class WeeksSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized weekly health data."""

    __tablename__ = 'weeks_summary'

    db = SummaryDB
    table_version = 3
    view_version = sb.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_weeks_view(db)


class DaysSummary(SummaryDB.Base, sb.SummaryBase):
    """Object representing summarized daily health data."""

    __tablename__ = 'days_summary'

    db = SummaryDB
    table_version = 3
    view_version = sb.SummaryBase.view_version

    day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_days_view(db)
