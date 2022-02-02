"""Objects representing a database and database objects for storing health summary data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import datetime
from sqlalchemy import Column, Integer, Date, DateTime

import idbutils

from ..summarydb import SummaryBase


logger = logging.getLogger(__name__)

GarminSummaryDb = idbutils.DB.create('garmin_summary', 8, "Database for storing health summary data from a Garmin device.")
Summary = idbutils.DbObject.create('summary', GarminSummaryDb, 1, base=idbutils.KeyValueObject)


class YearsSummary(GarminSummaryDb.Base, SummaryBase):
    """A table holding summarized data with one row per year."""

    __tablename__ = 'years_summary'

    db = GarminSummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def get_year(cls, db, year):
        """Return record for a given year."""
        with db.managed_session() as session:
            return session.query(cls).filter(cls.first_day == datetime.date(day=1, month=1, year=year)).one_or_none()

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_years_view(db)


class MonthsSummary(GarminSummaryDb.Base, SummaryBase):
    """A table holding summarized data with one row per month."""

    __tablename__ = 'months_summary'

    db = GarminSummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_months_view(db)


class WeeksSummary(GarminSummaryDb.Base, SummaryBase):
    """A table holding summarizzed data with one row per week."""

    __tablename__ = 'weeks_summary'

    db = GarminSummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_weeks_view(db)


class DaysSummary(GarminSummaryDb.Base, SummaryBase):
    """A table holding summarized data with one row per day."""

    __tablename__ = 'days_summary'

    db = GarminSummaryDb
    table_version = SummaryBase._table_version
    view_version = SummaryBase.view_version

    day = Column(Date, primary_key=True)

    @classmethod
    def get_day(cls, db, day):
        """Return record for a given day."""
        with db.managed_session() as session:
            return session.query(cls).filter(cls.day == day).one_or_none()

    @classmethod
    def create_view(cls, db):
        """Create the default database view for the table."""
        cls.create_days_view(db)


class IntensityHR(GarminSummaryDb.Base, idbutils.DbObject):
    """Monitoring heart rate values that fall within a intensity period."""

    __tablename__ = 'intensity_hr'

    db = GarminSummaryDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    intensity = Column(Integer, nullable=False)
    heart_rate = Column(Integer, nullable=False)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'inactive_hr_avg' : cls.s_get_col_avg_for_value(session, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_min' : cls.s_get_col_min_for_value(session, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_max' : cls.s_get_col_max_for_value(session, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
        }
