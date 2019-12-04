"""Objects representing a database and database objects for storing health summary data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, DateTime

import HealthDB
import utilities


logger = logging.getLogger(__name__)


class GarminSummaryDB(utilities.DB):
    """Object representing a database for storing health summary data from a Garmin device."""

    Base = declarative_base()
    db_name = 'garmin_summary'
    db_version = 7

    class _DbVersion(Base, utilities.DbVersionObject):
        pass

    def __init__(self, db_params, debug=False):
        """
        Return an instance of GarminSummaryDB.

        Paramters:
            db_params (dict): Config data for accessing the database
            debug (Boolean): enable debug logging
        """
        super().__init__(db_params, debug)
        GarminSummaryDB.Base.metadata.create_all(self.engine)
        self.version = GarminSummaryDB._DbVersion()
        self.version.version_check(self, self.db_version)
        #
        self.tables = [Summary, MonthsSummary, WeeksSummary, DaysSummary, IntensityHR]
        for table in self.tables:
            self.version.table_version_check(self, table)
            if not self.version.view_version_check(self, table):
                table.delete_view(self)
        #
        MonthsSummary.create_months_view(self)
        WeeksSummary.create_weeks_view(self)
        DaysSummary.create_days_view(self)


class Summary(GarminSummaryDB.Base, utilities.KeyValueObject):
    """A table holding statistics about health data as key-value pairs."""

    __tablename__ = 'summary'
    table_version = 1


class MonthsSummary(GarminSummaryDB.Base, HealthDB.SummaryBase):
    """A table holding summarizzed data with one row per month."""

    __tablename__ = 'months_summary'
    table_version = 2
    view_version = HealthDB.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    time_col_name = 'first_day'


class WeeksSummary(GarminSummaryDB.Base, HealthDB.SummaryBase):
    """A table holding summarizzed data with one row per week."""

    __tablename__ = 'weeks_summary'
    table_version = 2
    view_version = HealthDB.SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    time_col_name = 'first_day'


class DaysSummary(GarminSummaryDB.Base, HealthDB.SummaryBase):
    """A table holding summarizzed data with one row per day."""

    __tablename__ = 'days_summary'
    table_version = 2
    view_version = HealthDB.SummaryBase.view_version

    day = Column(Date, primary_key=True)

    time_col_name = 'day'


class IntensityHR(GarminSummaryDB.Base, utilities.DBObject):
    """Monitoring heart rate values that fall within a intensity period."""

    __tablename__ = 'intensity_hr'
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    intensity = Column(Integer, nullable=False)
    heart_rate = Column(Integer, nullable=False)

    time_col_name = 'timestamp'

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'inactive_hr_avg' : cls.s_get_col_avg_for_value(session, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_min' : cls.s_get_col_min_for_value(session, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_max' : cls.s_get_col_max_for_value(session, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
        }
