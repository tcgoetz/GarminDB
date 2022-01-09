"""Objects for analyzing MS Health data exports."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import datetime
import calendar

import fitfile.conversions as conversions

from ..summarydb import SummaryDb, DaysSummary, WeeksSummary, MonthsSummary, YearsSummary
from .mshealth_db import MSHealthDb, MSVaultWeight, DaysSummary as MshDaysSummary


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
stat_logger = logging.getLogger('stats')
stat_logger.addHandler(logging.FileHandler('ms_stats.txt', 'w'))


class Analyze(object):
    """Object for analyzing health data from Microsoft Health."""

    def __init__(self, db_params):
        """Return an instance of the Analyze class."""
        self.mshealthdb = MSHealthDb(db_params)
        self.sumdb = SummaryDb(db_params)

    def __days_from_years(self, year):
        sum_days = DaysSummary.get_days(self.mshealthdb, year)
        weight_days = MSVaultWeight.get_days(self.mshealthdb, year)
        return sum_days + list(set(weight_days) - set(sum_days))

    def __get_days(self, year):
        year_int = int(year)
        days = self.__days_from_years(year)
        days_count = len(days)
        if days_count > 0:
            first_day = days[0]
            last_day = days[-1]
            span = last_day - first_day + 1
        else:
            span = 0
        stat_logger.info("%d Days (%d vs %d): %s", year_int, days_count, span, days)
        for index in range(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(conversions.day_of_the_year_to_datetime(year_int, day))
                next_day_str = str(conversions.day_of_the_year_to_datetime(year_int, next_day))
                stat_logger.info("Days gap between %d (%s) and %d (%s)", day, day_str, next_day, next_day_str)

    def __get_months(self, year):
        months = MshDaysSummary.get_month_names(self.mshealthdb, year)
        stat_logger.info("%s Months (%d): %s", year, len(months), months)

    def get_years(self):
        years = MshDaysSummary.get_years(self.mshealthdb)
        stat_logger.info("Years (%d): %s", len(years), years)
        for year in years:
            self.__get_months(year)
            self.__get_days(year)

    def summary(self):
        years = MshDaysSummary.get_years(self.mshealthdb)
        for year in years:
            days = self.__days_from_years(year)
            for day in days:
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                stats = MshDaysSummary.get_daily_stats(self.mshealthdb, day_ts)
                stats.update(MSVaultWeight.get_daily_stats(self.mshealthdb, day_ts))
                DaysSummary.insert_or_update(self.sumdb, stats, ignore_none=True)
            for week_starting_day in range(1, 365, 7):
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                stats = MshDaysSummary.get_weekly_stats(self.mshealthdb, day_ts)
                stats.update(MSVaultWeight.get_weekly_stats(self.mshealthdb, day_ts))
                WeeksSummary.insert_or_update(self.sumdb, stats, ignore_none=True)
            months = MshDaysSummary.get_months(self.mshealthdb, year)
            for month in months:
                start_day_ts = datetime.date(year, month, 1)
                end_day_ts = datetime.date(year, month, calendar.monthrange(year, month)[1])
                stats = MshDaysSummary.get_monthly_stats(self.mshealthdb, start_day_ts, end_day_ts)
                stats.update(MSVaultWeight.get_monthly_stats(self.mshealthdb, start_day_ts, end_day_ts))
                MonthsSummary.insert_or_update(self.sumdb, stats, ignore_none=True)
            stats.update(MSVaultWeight.get_yearly_stats(self.mshealthdb, year))
            YearsSummary.insert_or_update(self.sumdb, stats, ignore_none=True)
