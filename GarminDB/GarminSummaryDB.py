#!/usr/bin/env python

#
# copyright Tom Goetz
#

from HealthDB import *


logger = logging.getLogger(__name__)


class GarminSummaryDB(DB):
    Base = declarative_base()
    db_name = 'garmin_summary'
    db_version = 5
    view_version = SummaryBase.view_version

    class DbVersion(Base, DbVersionObject):
        pass

    def __init__(self, db_params_dict, debug=False):
        logger.info("GarminSummaryDB: %s debug: %s ", repr(db_params_dict), str(debug))
        super(GarminSummaryDB, self).__init__(db_params_dict, debug)
        GarminSummaryDB.Base.metadata.create_all(self.engine)
        version = SummaryDB.DbVersion()
        version.version_check(self, self.db_version)
        #
        db_view_version = version.version_check_key(self, 'view_version', self.view_version)
        if db_view_version != self.view_version:
            MonthsSummary.delete_view(self)
            WeeksSummary.delete_view(self)
            DaysSummary.delete_view(self)
            version.update_version(self, 'view_version', self.view_version)
        MonthsSummary.create_months_view(self)
        WeeksSummary.create_weeks_view(self)
        DaysSummary.create_days_view(self)


class Summary(GarminSummaryDB.Base, KeyValueObject):
    __tablename__ = 'summary'


class MonthsSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'months_summary'

    first_day = Column(Date, primary_key=True)

    time_col_name = 'first_day'


class WeeksSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'weeks_summary'

    first_day = Column(Date, primary_key=True)

    time_col_name = 'first_day'


class DaysSummary(GarminSummaryDB.Base, SummaryBase):
    __tablename__ = 'days_summary'

    day = Column(Date, primary_key=True)

    time_col_name = 'day'


#
# Monitoring heart rate values that fall within a intensity period.
#
class IntensityHR(GarminSummaryDB.Base, DBObject):
    __tablename__ = 'intensity_hr'

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
