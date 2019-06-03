#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class GarminSummaryDB(DB):
    Base = declarative_base()
    db_name = 'garmin_summary'
    db_version = 7

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        super(GarminSummaryDB, self).__init__(db_params_dict, debug)
        GarminSummaryDB.Base.metadata.create_all(self.engine)
        version = SummaryDB.DbVersion()
        version.version_check(self, self.db_version)
        #
        self.tables = [Summary, MonthsSummary, WeeksSummary, DaysSummary, IntensityHR]
        for table in self.tables:
            version.table_version_check(self, table)
            if not version.view_version_check(self, table):
                table.delete_view(self)
        #
        MonthsSummary.create_months_view(self)
        WeeksSummary.create_weeks_view(self)
        DaysSummary.create_days_view(self)


class Summary(GarminSummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'
    table_version = 1


class MonthsSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'
    table_version = 1
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    time_col_name = 'first_day'


class WeeksSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'
    table_version = 1
    view_version = SummaryBase.view_version

    first_day = Column(Date, primary_key=True)

    time_col_name = 'first_day'


class DaysSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'
    table_version = 1
    view_version = SummaryBase.view_version

    day = Column(Date, primary_key=True)

    time_col_name = 'day'


#
# Monitoring heart rate values that fall within a intensity period.
#
class IntensityHR(GarminSummaryDB.Base, DBObject):
    __tablename__ = 'intensity_hr'
    table_version = 1

    timestamp = Column(DateTime, primary_key=True)
    intensity = Column(Integer, nullable=False)
    heart_rate = Column(Integer, nullable=False)

    time_col_name = 'timestamp'

    @classmethod
    def get_stats(cls, db, start_ts, end_ts):
        stats = {
            'inactive_hr_avg' : cls.get_col_avg_for_value(db, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_min' : cls.get_col_min_for_value(db, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
            'inactive_hr_max' : cls.get_col_max_for_value(db, cls.heart_rate, cls.intensity, 0, start_ts, end_ts, True),
        }
        return stats
