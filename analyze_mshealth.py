"""Objects for analyzing MS Health data exports."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import datetime
import calendar

import Fit.conversions as conversions
import HealthDB
import MSHealthDB


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
stat_logger = logging.getLogger('stats')
stat_logger.addHandler(logging.FileHandler('ms_stats.txt', 'w'))


class Analyze(object):
    """Object for analyzing health data from Microsoft Health."""

    def __init__(self, db_params_dict):
        """Return an instance of the Analyze class."""
        self.mshealthdb = MSHealthDB.MSHealthDB(db_params_dict)
        self.sumdb = HealthDB.SummaryDB(db_params_dict)

    def __days_from_years(self, year):
        sum_days = MSHealthDB.DaysSummary.get_days(self.mshealthdb, year)
        weight_days = MSHealthDB.MSVaultWeight.get_days(self.mshealthdb, year)
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
        for index in xrange(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(conversions.day_of_the_year_to_datetime(year_int, day))
                next_day_str = str(conversions.day_of_the_year_to_datetime(year_int, next_day))
                stat_logger.info("Days gap between %d (%s) and %d (%s)", day, day_str, next_day, next_day_str)

    def __get_months(self, year):
        months = MSHealthDB.DaysSummary.get_month_names(self.mshealthdb, year)
        stat_logger.info("%s Months (%d): %s", year, len(months), months)

    def get_years(self):
        years = MSHealthDB.DaysSummary.get_years(self.mshealthdb)
        stat_logger.info("Years (%d): %s", len(years), years)
        for year in years:
            self.__get_months(year)
            self.__get_days(year)

    def summary(self):
        years = MSHealthDB.DaysSummary.get_years(self.mshealthdb)
        for year in years:
            days = self.__days_from_years(year)
            for day in days:
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                stats = MSHealthDB.DaysSummary.get_daily_stats(self.mshealthdb, day_ts)
                stats.update(MSHealthDB.MSVaultWeight.get_daily_stats(self.mshealthdb, day_ts))
                HealthDB.DaysSummary.create_or_update_not_none(self.sumdb, stats)
            for week_starting_day in xrange(1, 365, 7):
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                stats = MSHealthDB.DaysSummary.get_weekly_stats(self.mshealthdb, day_ts)
                stats.update(MSHealthDB.MSVaultWeight.get_weekly_stats(self.mshealthdb, day_ts))
                HealthDB.WeeksSummary.create_or_update_not_none(self.sumdb, stats)
            months = MSHealthDB.DaysSummary.get_months(self.mshealthdb, year)
            for month in months:
                start_day_ts = datetime.date(year, month, 1)
                end_day_ts = datetime.date(year, month, calendar.monthrange(year, month)[1])
                stats = MSHealthDB.DaysSummary.get_monthly_stats(self.mshealthdb, start_day_ts, end_day_ts)
                stats.update(MSHealthDB.MSVaultWeight.get_monthly_stats(self.mshealthdb, start_day_ts, end_day_ts))
                HealthDB.MonthsSummary.create_or_update_not_none(self.sumdb, stats)
