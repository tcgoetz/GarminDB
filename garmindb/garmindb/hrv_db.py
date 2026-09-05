"""Objects representing a database and database objects for storing sleep data from a Garmin device."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
from sqlalchemy import Column, Integer, DateTime, Float, Enum

import fitfile
import idbutils


logger = logging.getLogger(__name__)


HrvDb = idbutils.DB.create('hrv', 1, "Database for storing hrv data from a Garmin device.")


class HrvValue(HrvDb.Base, idbutils.DbObject):
    """Table that stores events recorded during sleep."""

    __tablename__ = 'hrv_value'

    db = HrvDb
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    hrv_value = Column(Integer)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'hrv_avg'         : cls.s_get_col_avg(session, cls.hrv_value, start_ts, end_ts),
            'grv_min'         : cls.s_get_col_min(session, cls.hrv_value, start_ts, end_ts),
            'hrv_max'         : cls.s_get_col_max(session, cls.hrv_value, start_ts, end_ts),
        }


class HrvStatusSummary(HrvDb.Base, idbutils.DbObject):
    """Class representing a sleep session. Data in this table comes for FIT files"""

    __tablename__ = 'hrv_status_summary'

    db = HrvDb
    table_version = 1

    day = Column(DateTime, primary_key=True)
    weekly_average = Column(Float)
    last_night = Column(Float)
    last_night_average = Column(Float)
    baseline_high = Column(Float)
    baseline_low = Column(Float)
    baseline_balanced_high = Column(Float)
    baseline_balanced_low = Column(Float)
    hrv_status = Column(Enum(fitfile.fields.HeartRateVarianceStatus))
    reading_count = Column(Integer)

    @classmethod
    def get_stats(cls, session, start_ts, end_ts):
        """Return a dictionary of aggregate statistics for the given time period."""
        return {
            'hrv_avg'         : cls.s_get_col_avg(session, cls.last_night, start_ts, end_ts),
            'hrv_min'         : cls.s_get_col_min(session, cls.last_night, start_ts, end_ts),
            'hrv_max'         : cls.s_get_col_max(session, cls.last_night, start_ts, end_ts),
        }
