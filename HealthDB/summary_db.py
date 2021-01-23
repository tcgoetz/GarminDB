"""Objects representing a database and database objects summarizing health data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from sqlalchemy import Column, Date

import utilities
import HealthDB.summary_base as sb


logger = logging.getLogger(__name__)

SummaryDB = utilities.DB.create('summary', 7, "Database for storing summarizing health data.")
Summary = utilities.DbObject.create('summary', SummaryDB, 1, base=utilities.KeyValueObject)


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
