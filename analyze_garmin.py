#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, calendar

import HealthDB
import GarminDB
from Fit import Conversions


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


class MovingAverageFilter():
    def __init__(self, factor, initial_value):
        self.factor1 = factor
        self.factor2 = 1.0 - factor
        self.value = initial_value

    def filter(self, input_value):
        self.value = (self.value * self.factor1) + (input_value * self.factor2)
        return round(self.value)


class Analyze():
    def __init__(self, db_params_dict, debug):
        self.garmindb = GarminDB.GarminDB(db_params_dict, debug)
        self.mondb = GarminDB.MonitoringDB(db_params_dict, debug)
        self.garminsumdb = GarminDB.GarminSummaryDB(db_params_dict, debug)
        self.sumdb = HealthDB.SummaryDB(db_params_dict, debug)
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, debug)
        self.english_units = (GarminDB.Attributes.get(self.garmindb, 'dist_setting') == 'statute')

    def set_sleep_period(self, sleep_period_start, sleep_period_stop):
        GarminDB.Attributes.set_if_unset(self.garmindb, 'sleep_time', sleep_period_start)
        GarminDB.Attributes.set_if_unset(self.garmindb, 'wake_time', sleep_period_stop)

    def report_file_type(self, file_type):
        records = GarminDB.File.row_count(self.garmindb, GarminDB.File.type, file_type)
        logger.info("%s files: %d" % (file_type, records))
        GarminDB.Summary.set(self.garminsumdb, file_type + '_files', records)

    def get_files_stats(self):
        records = GarminDB.File.row_count(self.garmindb)
        logger.info("File records: %d" % records)
        GarminDB.Summary.set(self.garminsumdb, 'files', records)
        self.report_file_type('tcx')
        self.report_file_type('activity')
        self.report_file_type('monitoring_b')

    def report_sport(self, sport_col, sport):
        records = GarminDB.Activities.row_count(self.garmin_act_db, sport_col, sport.lower())
        logger.info("%s activities: %d" % (sport, records))
        GarminDB.Summary.set(self.garminsumdb, sport + '_Activities', records)

    def get_activities_stats(self):
        activities = GarminDB.Activities.row_count(self.garmin_act_db)
        logger.info("Activity summary records: %d" % activities)
        GarminDB.Summary.set(self.garminsumdb, 'Activities', activities)
        laps = GarminDB.ActivityLaps.row_count(self.garmin_act_db)
        logger.info("Activities lap records: %d" % laps)
        GarminDB.Summary.set(self.garminsumdb, 'Activity_laps', laps)
        records = GarminDB.ActivityRecords.row_count(self.garmin_act_db)
        logger.info("Activity records: %d" % records)
        GarminDB.Summary.set(self.garminsumdb, 'Activity_records', records)
        years = GarminDB.Activities.get_years(self.garmin_act_db)
        logger.info("Activities years: %d (%s)" % (len(years), str(years)))
        GarminDB.Summary.set(self.garminsumdb, 'Activity_Years', len(years))
        self.report_sport(GarminDB.Activities.sport, 'Running')
        self.report_sport(GarminDB.Activities.sport, 'Walking')
        self.report_sport(GarminDB.Activities.sport, 'Cycling')
        self.report_sport(GarminDB.Activities.sub_sport, 'Mountain_Biking')
        self.report_sport(GarminDB.Activities.sport, 'Hiking')
        self.report_sport(GarminDB.Activities.sub_sport, 'Elliptical')
        self.report_sport(GarminDB.Activities.sub_sport, 'Treadmill_Running')
        self.report_sport(GarminDB.Activities.sub_sport, 'Paddling')
        self.report_sport(GarminDB.Activities.sub_sport, 'Resort_Skiing_Snowboarding')

    def get_col_stats(self, table, col, name, ignore_le_zero=False):
        records = table.row_count(self.garmindb)
        logger.info("%s records: %d" % (name, records))
        GarminDB.Summary.set(self.garminsumdb, '%s_Records' % name, records)
        maximum = table.get_col_max(self.garmindb, col)
        logger.info("Max %s: %s" % (name, str(maximum)))
        GarminDB.Summary.set(self.garminsumdb, 'Max_%s' % name, maximum)
        minimum = table.get_col_min(self.garmindb, col, ignore_le_zero=ignore_le_zero)
        logger.info("Min %s: %s" % (name, str(minimum)))
        GarminDB.Summary.set(self.garminsumdb, 'Min_%s' % name, minimum)
        average = table.get_col_avg(self.garmindb, col)
        logger.info("Avg %s: %s" % (name, str(average)))
        GarminDB.Summary.set(self.garminsumdb, 'Avg_%s' % name, average)
        latest = table.get_col_latest(self.garmindb, col)
        logger.info("Latest %s: %s" % (name, str(latest)))

    def get_weight_stats(self):
        self.get_col_stats(GarminDB.Weight, GarminDB.Weight.weight, 'Weight')

    def get_stress_stats(self):
        self.get_col_stats(GarminDB.Stress, GarminDB.Stress.stress, 'Stress', True)

    def get_rhr_stats(self):
        self.get_col_stats(GarminDB.RestingHeartRate, GarminDB.RestingHeartRate.resting_heart_rate, 'RHR', True)

    def get_sleep_stats(self):
        self.get_col_stats(GarminDB.Sleep, GarminDB.Sleep.total_sleep, 'Sleep', True)

    def get_monitoring_years(self):
        years = GarminDB.Monitoring.get_years(self.mondb)
        GarminDB.Summary.set(self.garminsumdb, 'Monitoring_Years', len(years))
        logger.info("Monitoring records: %d" % GarminDB.Monitoring.row_count(self.mondb))
        logger.info("Monitoring Years (%d): %s" % (len(years), str(years)))
        for year in years:
            self.get_monitoring_months(year)
            self.get_monitoring_days(year)

    def get_monitoring_months(self, year):
        months = GarminDB.Monitoring.get_month_names(self.mondb, year)
        GarminDB.Summary.set(self.garminsumdb, str(year) + '_months', len(months))
        logger.info("%s Months (%s): %s" % (year, len(months) , str(months)))

    def get_monitoring_days(self, year):
        days = GarminDB.Monitoring.get_days(self.mondb, year)
        days_count = len(days)
        if days_count > 0:
            first_day = days[0]
            last_day = days[-1]
            span = last_day - first_day + 1
        else:
            span = 0
        GarminDB.Summary.set(self.garminsumdb, str(year) + '_days', days_count)
        GarminDB.Summary.set(self.garminsumdb, str(year) + '_days_span', span)
        logger.info("%d Days (%d count vs %d span): %s" % (year, days_count, span, str(days)))
        for index in xrange(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(Conversions.day_of_the_year_to_datetime(year, day))
                next_day_str = str(Conversions.day_of_the_year_to_datetime(year, next_day))
                logger.info("Days gap between %d (%s) and %d (%s)" % (day, day_str, next_day, next_day_str))

    def combine_stats(self, stats, stat1_name, stat2_name):
        stat1 = stats.get(stat1_name, 0)
        stat2 = stats.get(stat2_name, 0)
        if stat1 is not None and stat2 is not None:
            return stat1 + stat2
        if stat1 is not None:
            return stat1
        if stat2 is not None:
            return stat2

    def calculate_day_stats(self, day_date):
        stats = GarminDB.MonitoringHeartRate.get_daily_stats(self.mondb, day_date)
        stats.update(GarminDB.RestingHeartRate.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.Weight.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.Stress.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringClimb.get_daily_stats(self.mondb, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_daily_stats(self.mondb, day_date))
        stats.update(GarminDB.Monitoring.get_daily_stats(self.mondb, day_date))
        stats.update(GarminDB.Sleep.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringInfo.get_daily_stats(self.mondb, day_date))
        stats['calories_avg'] = self.combine_stats(stats, 'calories_bmr_avg', 'calories_active_avg')
        GarminDB.DaysSummary.create_or_update_not_none(self.garminsumdb, stats)
        HealthDB.DaysSummary.create_or_update_not_none(self.sumdb, stats)

    def calculate_week_stats(self, day_date):
        stats = GarminDB.MonitoringHeartRate.get_weekly_stats(self.mondb, day_date)
        stats.update(GarminDB.RestingHeartRate.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.Weight.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.Stress.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringClimb.get_weekly_stats(self.mondb, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_weekly_stats(self.mondb, day_date))
        stats.update(GarminDB.Monitoring.get_weekly_stats(self.mondb, day_date))
        stats.update(GarminDB.Sleep.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringInfo.get_weekly_stats(self.mondb, day_date))
        stats['calories_avg'] = self.combine_stats(stats, 'calories_bmr_avg', 'calories_active_avg')
        GarminDB.WeeksSummary.create_or_update_not_none(self.garminsumdb, stats)
        HealthDB.WeeksSummary.create_or_update_not_none(self.sumdb, stats)

    def calculate_month_stats(self, start_day_date, end_day_date):
        stats = GarminDB.MonitoringHeartRate.get_monthly_stats(self.mondb, start_day_date, end_day_date)
        stats.update(GarminDB.RestingHeartRate.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.Weight.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.Stress.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.MonitoringClimb.get_monthly_stats(self.mondb, start_day_date, end_day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_monthly_stats(self.mondb, start_day_date, end_day_date))
        stats.update(GarminDB.Monitoring.get_monthly_stats(self.mondb, start_day_date, end_day_date))
        stats.update(GarminDB.Sleep.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.MonitoringInfo.get_monthly_stats(self.mondb, start_day_date, end_day_date))
        stats['calories_avg'] = self.combine_stats(stats, 'calories_bmr_avg', 'calories_active_avg')
        GarminDB.MonthsSummary.create_or_update_not_none(self.garminsumdb, stats)
        HealthDB.MonthsSummary.create_or_update_not_none(self.sumdb, stats)

    def summary(self):
        sleep_period_start = GarminDB.Attributes.get_time(self.garmindb, 'sleep_time')
        sleep_period_stop = GarminDB.Attributes.get_time(self.garmindb, 'wake_time')

        years = GarminDB.Monitoring.get_years(self.mondb)
        for year in years:
            days = GarminDB.Monitoring.get_days(self.mondb, year)
            for day in days:
                day_date = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                self.calculate_day_stats(day_date)

            for week_starting_day in xrange(1, 365, 7):
                day_date = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                self.calculate_week_stats(day_date)

            months = GarminDB.Monitoring.get_months(self.mondb, year)
            for month in months:
                start_day_date = datetime.date(year, month, 1)
                end_day_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
                self.calculate_month_stats(start_day_date, end_day_date)

def usage(program):
    print '%s -s <sqlite db path> -m ...' % program
    sys.exit()

def main(argv):
    summary = False
    debug = 0
    db_params_dict = {}
    dates = False
    sleep_period_start = None
    sleep_period_stop = None

    logger.setLevel(logging.INFO)
    root_logger.setLevel(logging.INFO)

    try:
        opts, args = getopt.getopt(argv,"adi:t:s:", ["analyze", "debug=", "dates", "mysql=", "sqlite="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-a", "--analyze"):
            logging.debug("analyze: True")
            summary = True
        elif opt in ("-t", "--debug"):
            debug = int(arg)
            if debug > 0:
                logger.setLevel(logging.DEBUG)
            if debug > 1:
                root_logger.setLevel(logging.DEBUG)
            logging.debug("debug: %d" % debug)
        elif opt in ("-d", "--dates"):
            logging.debug("Dates")
            dates = True
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

    if len(db_params_dict) == 0:
        print "Missing arguments:"
        usage(sys.argv[0])

    analyze = Analyze(db_params_dict, debug - 1)
    if dates:
        analyze.get_files_stats()
        analyze.get_weight_stats()
        analyze.get_stress_stats()
        analyze.get_rhr_stats()
        analyze.get_sleep_stats()
        analyze.get_activities_stats()
        analyze.get_monitoring_years()
    if summary:
        analyze.summary()

if __name__ == "__main__":
    main(sys.argv[1:])


