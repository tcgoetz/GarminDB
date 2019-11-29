"""Objects for analyzing FitBit data from FitBit CSV exported data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import sys
import logging
import datetime
import calendar

import HealthDB
import FitBitDB
import Fit.conversions as conversions


logging.basicConfig(filename='analyze_fitbit.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Analyze(object):
    """Object for analyzing FitBit data from FitBit CSV exported data."""

    def __init__(self, db_params):
        """Return an instance of the Analyze class."""
        self.fitbitdb = FitBitDB.FitBitDB(db_params)
        self.sumdb = HealthDB.SummaryDB(db_params)

    def __get_days(self, year):
        year_int = int(year)
        days = FitBitDB.DaysSummary.get_days(self.fitbitdb, year)
        days_count = len(days)
        if days_count > 0:
            first_day = days[0]
            last_day = days[-1]
            span = last_day - first_day + 1
        else:
            span = 0
        print("%d Days (%d vs %d): %s" % (year_int, days_count, span, days))
        for index in range(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(conversions.day_of_the_year_to_datetime(year_int, day))
                next_day_str = str(conversions.day_of_the_year_to_datetime(year_int, next_day))
                print("Days gap between %d (%s) and %d (%s)" % (day, day_str, next_day, next_day_str))

    def __get_months(self, year):
        months = FitBitDB.DaysSummary.get_month_names(self.fitbitdb, year)
        print("%s Months (%d): %s" % (year, len(months), months))

    def get_years(self):
        years = FitBitDB.DaysSummary.get_years(self.fitbitdb)
        print("Years (%d): %s" % (len(years), years))
        for year in years:
            self.__get_months(year)
            self.__get_days(year)

    def summary(self):
        years = FitBitDB.DaysSummary.get_years(self.fitbitdb)
        for year in years:
            days = FitBitDB.DaysSummary.get_days(self.fitbitdb, year)
            for day in days:
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                stats = FitBitDB.DaysSummary.get_daily_stats(self.fitbitdb, day_ts)
                HealthDB.DaysSummary.create_or_update(self.sumdb, stats, ignore_none=True)
            for week_starting_day in range(1, 365, 7):
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                stats = FitBitDB.DaysSummary.get_weekly_stats(self.fitbitdb, day_ts)
                HealthDB.WeeksSummary.create_or_update(self.sumdb, stats, ignore_none=True)
            months = FitBitDB.DaysSummary.get_months(self.fitbitdb, year)
            for month in months:
                start_day_ts = datetime.date(year, month, 1)
                end_day_ts = datetime.date(year, month, calendar.monthrange(year, month)[1])
                stats = FitBitDB.DaysSummary.get_monthly_stats(self.fitbitdb, start_day_ts, end_day_ts)
                HealthDB.MonthsSummary.create_or_update(self.sumdb, stats, ignore_none=True)
