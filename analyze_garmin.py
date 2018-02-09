#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, calendar

import HealthDB
import GarminDB


logger = logging.getLogger(__file__)


class Analyze():

    def __init__(self, db_params_dict):
        self.garmindb = GarminDB.GarminDB(db_params_dict)
        self.mondb = GarminDB.MonitoringDB(db_params_dict)
        self.garminsumdb = GarminDB.GarminSummaryDB(db_params_dict)
        self.sumdb = HealthDB.SummaryDB(db_params_dict)
        units = GarminDB.Attributes.get(self.garmindb, 'units')
        if units.value == 'english':
            self.english_units = True
        else:
            self.english_units = False

    def get_years(self):
        years = GarminDB.Monitoring.get_years(self.mondb)
        GarminDB.Summary.set(self.garminsumdb, 'years', len(years))
        print "Years (%d): %s" % (len(years), str(years))

    def get_months(self, year):
        months = GarminDB.Monitoring.get_month_names(self.mondb, year)
        GarminDB.Summary.set(self.garminsumdb, year + '_months', len(months))
        print "%s Months (%d): %s" % (year, len(months) , str(months))

    def get_days(self, year):
        year_int = int(year)
        days = GarminDB.Monitoring.get_days(self.mondb, year)
        days_count = len(days)
        if days_count > 0:
            first_day = days[0]
            last_day = days[-1]
            span = last_day - first_day + 1
        else:
            span = 0
        GarminDB.Summary.set(self.garminsumdb, year + '_days', days_count)
        GarminDB.Summary.set(self.garminsumdb, year + '_days_span', span)
        print "%d Days (%d vs %d): %s" % (year_int, days_count, span, str(days))
        for index in xrange(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(HealthDB.day_of_the_year_to_datetime(year_int, day))
                next_day_str = str(HealthDB.day_of_the_year_to_datetime(year_int, next_day))
                print "Days gap between %d (%s) and %d (%s)" % (day, day_str, next_day, next_day_str)

    def summary(self):
        years = GarminDB.Monitoring.get_years(self.mondb)
        for year in years:
            days = GarminDB.Monitoring.get_days(self.mondb, year)
            for day in days:
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                stats = GarminDB.MonitoringHeartRate.get_daily_stats(self.mondb, day_ts)
                stats.update(GarminDB.Weight.get_daily_stats(self.garmindb, day_ts))
                stats.update(GarminDB.Stress.get_daily_stats(self.garmindb, day_ts))
                stats.update(GarminDB.MonitoringClimb.get_daily_stats(self.mondb, day_ts, self.english_units))
                stats.update(GarminDB.MonitoringIntensityMins.get_daily_stats(self.mondb, day_ts))
                stats.update(GarminDB.Monitoring.get_daily_stats(self.mondb, day_ts))
                GarminDB.DaysSummary.create_or_update(self.garminsumdb, stats)
                HealthDB.DaysSummary.create_or_update(self.sumdb, stats)
            for week_starting_day in xrange(1, 365, 7):
                day_ts = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                stats = GarminDB.MonitoringHeartRate.get_weekly_stats(self.mondb, day_ts)
                stats.update(GarminDB.Weight.get_weekly_stats(self.garmindb, day_ts))
                stats.update(GarminDB.Stress.get_weekly_stats(self.garmindb, day_ts))
                stats.update(GarminDB.MonitoringClimb.get_weekly_stats(self.mondb, day_ts, self.english_units))
                stats.update(GarminDB.MonitoringIntensityMins.get_weekly_stats(self.mondb, day_ts))
                stats.update(GarminDB.Monitoring.get_weekly_stats(self.mondb, day_ts))
                GarminDB.WeeksSummary.create_or_update(self.garminsumdb, stats)
                HealthDB.WeeksSummary.create_or_update(self.sumdb, stats)
            for month in xrange(1, 12):
                start_day_ts = datetime.date(year, month, 1)
                end_day_ts = datetime.date(year, month, calendar.monthrange(year, month)[1])
                stats = GarminDB.MonitoringHeartRate.get_monthly_stats(self.mondb, start_day_ts, end_day_ts)
                stats.update(GarminDB.Weight.get_monthly_stats(self.garmindb, start_day_ts, end_day_ts))
                stats.update(GarminDB.Stress.get_monthly_stats(self.garmindb, start_day_ts, end_day_ts))
                stats.update(GarminDB.MonitoringClimb.get_monthly_stats(self.mondb, start_day_ts, end_day_ts, self.english_units))
                stats.update(GarminDB.MonitoringIntensityMins.get_monthly_stats(self.mondb, start_day_ts, end_day_ts))
                stats.update(GarminDB.Monitoring.get_monthly_stats(self.mondb, start_day_ts, end_day_ts))
                GarminDB.MonthsSummary.create_or_update(self.garminsumdb, stats)
                HealthDB.MonthsSummary.create_or_update(self.sumdb, stats)


def usage(program):
    print '%s -s <sqlite db path> -m ...' % program
    sys.exit()

def main(argv):
    debug = False
    db_params_dict = {}
    years = False
    months = None
    days = None

    try:
        opts, args = getopt.getopt(argv,"d:i:m:ts:y", ["debug", "days=", "months=", "mysql=", "years", "sqlite="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-t", "--debug"):
            logging.debug("debug: True")
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
        elif opt in ("-s", "--summary"):
            logging.debug("Summary")
            summary = True
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


