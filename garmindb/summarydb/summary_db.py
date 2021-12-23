"""Objects representing a database and database objects summarizing health data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from sqlalchemy import Column, Date

import idbutils

from .summary_base import SummaryBase


logger = logging.getLogger(__name__)

SummaryDb = idbutils.DB.create('summary', 7, "Database for storing summarizing health data.")
Summary = idbutils.DbObject.create('summary', SummaryDb, 1, base=idbutils.KeyValueObject)


class YearsSummary(SummaryDb.Base, SummaryBase):
    """Object representing summarized monthly health data."""

    __tablename__ = 'years_summary'

    db = SummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_years_view(db)


class MonthsSummary(SummaryDb.Base, SummaryBase):
    """Object representing summarized monthly health data."""

    __tablename__ = 'months_summary'

    db = SummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_months_view(db)


class WeeksSummary(SummaryDb.Base, SummaryBase):
    """Object representing summarized weekly health data."""

    __tablename__ = 'weeks_summary'

    db = SummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_weeks_view(db)


class DaysSummary(SummaryDb.Base, SummaryBase):
    """Object representing summarized daily health data."""

    __tablename__ = 'days_summary'

    db = SummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_days_view(db)
