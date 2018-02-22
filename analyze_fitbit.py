#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, calendar

import HealthDB
import FitBitDB
import Fit.Conversions


logger = logging.getLogger(__file__)



class Analyze():

    def __init__(self, db_params_dict):
        self.fitbitdb = FitBitDB.FitBitDB(db_params_dict)
        self.sumdb = HealthDB.SummaryDB(db_params_dict)

    def get_years(self):
        years = FitBitDB.DaysSummary.get_years(self.fitbitdb)
        print "Years (%d): %s" % (len(years), str(years))

    def get_months(self, year):
        months = FitBitDB.DaysSummary.get_month_names(self.fitbitdb, year)
        print "%s Months (%d): %s" % (year, len(months) , str(months))

    def get_days(self, year):
        year_int = int(year)
        days = FitBitDB.DaysSummary.get_days(self.fitbitdb, year)
        days_count = len(days)
        if days_count > 0:
            first_day = days[0]
            last_day = days[-1]
            span = last_day - first_day + 1
        else:
            span = 0
        print "%d Days (%d vs %d): %s" % (year_int, days_count, span, str(days))
        for index in xrange(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(Fit.Conversions.day_of_the_year_to_datetime(year_int, day))
                next_day_str = str(Fit.Conversions.day_of_the_year_to_datetime(year_int, next_day))
                print "Days gap between %d (%s) and %d (%s)" % (day, day_str, next_day, next_day_str)

    def summary(self):
        years = FitBitDB.DaysSummary.get_years(self.fitbitdb)
        for year in years:
            days = FitBitDB.DaysSummary.get_days(self.fitbitdb, year)
            for day in days:
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                stats = FitBitDB.DaysSummary.get_daily_stats(self.fitbitdb, day_ts)
                HealthDB.DaysSummary.create_or_update_not_none(self.sumdb, stats)
            for week_starting_day in xrange(1, 365, 7):
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                stats = FitBitDB.DaysSummary.get_weekly_stats(self.fitbitdb, day_ts)
                HealthDB.WeeksSummary.create_or_update_not_none(self.sumdb, stats)
            for month in xrange(1, 12):
                start_day_ts = datetime.date(year, month, 1)
                end_day_ts = datetime.date(year, month, calendar.monthrange(year, month)[1])
                stats = FitBitDB.DaysSummary.get_monthly_stats(self.fitbitdb, start_day_ts, end_day_ts)
                HealthDB.MonthsSummary.create_or_update_not_none(self.sumdb, stats)


def usage(program):
    print '%s --sqlite <sqlite db path> -m ...' % program
    sys.exit()

def main(argv):
    debug = False
    years = False
    months = None
    days = None
    db_params_dict = {}

    try:
        opts, args = getopt.getopt(argv,"di:m:s:y", ["debug", "sqlite=", "days=", "mysql=", "months=", "years"])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-d", "--debug"):
            logging.debug("debug True")
            debug = True
        elif opt in ("-y", "--years"):
            logging.debug("Years")
            years = True
        elif opt in ("-m", "--months"):
            logging.debug("Months")
            months = arg
        elif opt in ("-d", "--days"):
            logging.debug("Days")
            days = arg
        elif opt in ("-s", "--sqlite"):
            logging.debug("Sqlite DB path: %s" % arg)
            db_params_dict['db_type'] = 'sqlite'
            db_params_dict['db_path'] = arg
        elif opt in ("--mysql"):
            logging.debug("Mysql DB string: %s" % arg)
            db_args = arg.split(',')
            db_params_dict['db_type'] = 'mysql'
            db_params_dict['db_username'] = db_args[0]
            db_params_dict['db_password'] = db_args[1]
            db_params_dict['db_host'] = db_args[2]

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if len(db_params_dict) == 0:
        print "Missing arguments:"
        usage(sys.argv[0])

    analyze = Analyze(db_params_dict)
    if years:
        analyze.get_years()
    if months:
        analyze.get_months(months)
    if days:
        analyze.get_days(days)
    analyze.summary()

if __name__ == "__main__":
    main(sys.argv[1:])


