#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, calendar

import HealthDB
import GarminDB
from Fit import Conversions
from Fit import FieldEnums


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
        self.garmin_db = GarminDB.GarminDB(db_params_dict, debug)
        self.garmin_mon_db = GarminDB.MonitoringDB(db_params_dict, debug)
        self.garmin_sum_db = GarminDB.GarminSummaryDB(db_params_dict, debug)
        self.sum_db = HealthDB.SummaryDB(db_params_dict, debug)
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, debug)
        self.english_units = (GarminDB.Attributes.measurements_type_metric(self.garmin_db) == False)

    def set_sleep_period(self, sleep_period_start, sleep_period_stop):
        GarminDB.Attributes.set_if_unset(self.garmin_db, 'sleep_time', sleep_period_start)
        GarminDB.Attributes.set_if_unset(self.garmin_db, 'wake_time', sleep_period_stop)

    def report_file_type(self, file_type):
        records = GarminDB.File.row_count(self.garmin_db, GarminDB.File.type, file_type)
        logger.info("%s files: %d", file_type, records)
        GarminDB.Summary.set(self.garmin_sum_db, file_type + '_files', records)

    def get_files_stats(self):
        records = GarminDB.File.row_count(self.garmin_db)
        logger.info("File records: %d" % records)
        GarminDB.Summary.set(self.garmin_sum_db, 'files', records)
        self.report_file_type('tcx')
        self.report_file_type('activity')
        self.report_file_type('monitoring_b')

    def report_sport(self, sport_col, sport):
        records = GarminDB.Activities.row_count(self.garmin_act_db, sport_col, sport.lower())
        total_distance = GarminDB.Activities.get_col_sum_for_value(self.garmin_act_db, GarminDB.Activities.distance, sport_col, sport.lower())
        if total_distance is None:
            total_distance = 0
        logger.info("%s activities: %d - total distance %d miles", sport, records, total_distance)
        GarminDB.Summary.set(self.garmin_sum_db, sport + '_Activities', records)
        GarminDB.Summary.set(self.garmin_sum_db, sport + '_Miles', total_distance)

    def get_activities_stats(self):
        logger.info("___Activities Statistics___")
        activities = GarminDB.Activities.row_count(self.garmin_act_db)
        logger.info("Activity summary records: %d", activities)
        GarminDB.Summary.set(self.garmin_sum_db, 'Activities', activities)
        laps = GarminDB.ActivityLaps.row_count(self.garmin_act_db)
        logger.info("Activities lap records: %d", laps)
        GarminDB.Summary.set(self.garmin_sum_db, 'Activity_laps', laps)
        records = GarminDB.ActivityRecords.row_count(self.garmin_act_db)
        logger.info("Activity records: %d", records)
        GarminDB.Summary.set(self.garmin_sum_db, 'Activity_records', records)
        years = GarminDB.Activities.get_years(self.garmin_act_db)
        logger.info("Activities years: %d: %s", len(years), str(years))
        GarminDB.Summary.set(self.garmin_sum_db, 'Activity_Years', len(years))
        fitness_activities = GarminDB.Activities.row_count(self.garmin_act_db, GarminDB.Activities.type, 'fitness')
        logger.info("Fitness activities: %d", fitness_activities)
        GarminDB.Summary.set(self.garmin_sum_db, 'Fitness_activities', fitness_activities)
        recreation_activities = GarminDB.Activities.row_count(self.garmin_act_db, GarminDB.Activities.type, 'recreation')
        logger.info("Recreation activities: %d", recreation_activities)
        GarminDB.Summary.set(self.garmin_sum_db, 'Recreation_activities', recreation_activities)
        sports = GarminDB.Activities.get_col_distinct(self.garmin_act_db, GarminDB.Activities.sport)
        logger.info("Sports: %s", str(sports))
        sub_sports = GarminDB.Activities.get_col_distinct(self.garmin_act_db, GarminDB.Activities.sub_sport)
        logger.info("SubSports: %s", str(sub_sports))
        self.report_sport(GarminDB.Activities.sport, 'Running')
        self.report_sport(GarminDB.Activities.sport, 'Walking')
        self.report_sport(GarminDB.Activities.sport, 'Cycling')
        self.report_sport(GarminDB.Activities.sub_sport, 'Mountain_Biking')
        self.report_sport(GarminDB.Activities.sport, 'Hiking')
        self.report_sport(GarminDB.Activities.sub_sport, 'Elliptical')
        self.report_sport(GarminDB.Activities.sub_sport, 'Treadmill_Running')
        self.report_sport(GarminDB.Activities.sub_sport, 'Paddling')
        self.report_sport(GarminDB.Activities.sub_sport, 'Resort_Skiing_Snowboarding')

    def get_col_stats(self, table, col, name, ignore_le_zero=False, time_col=False):
        records = table.row_count(self.garmin_db)
        logger.info("%s records: %d", name, records)
        GarminDB.Summary.set(self.garmin_sum_db, '%s_Records' % name, records)
        if time_col:
            maximum = table.get_time_col_max(self.garmin_db, col)
        else:
            maximum = table.get_col_max(self.garmin_db, col)
        logger.info("Max %s: %s", name, str(maximum))
        GarminDB.Summary.set(self.garmin_sum_db, 'Max_%s' % name, maximum)
        if time_col:
            minimum = table.get_time_col_min(self.garmin_db, col, None, None, ignore_le_zero)
        else:
            minimum = table.get_col_min(self.garmin_db, col, None, None, ignore_le_zero)
        logger.info("Min %s: %s", name, str(minimum))
        GarminDB.Summary.set(self.garmin_sum_db, 'Min_%s' % name, minimum)
        if time_col:
            average = table.get_time_col_avg(self.garmin_db, col, None, None, ignore_le_zero)
        else:
            average = table.get_col_avg(self.garmin_db, col, None, None, ignore_le_zero)
        logger.info("Avg %s: %s", name, str(average))
        GarminDB.Summary.set(self.garmin_sum_db, 'Avg_%s' % name, average)
        latest = table.get_col_latest(self.garmin_db, col)
        logger.info("Latest %s: %s", name, str(latest))

    def get_monitoring_stats(self):
        logger.info("___Monitoring Statistics___")
        self.get_col_stats(GarminDB.Weight, GarminDB.Weight.weight, 'Weight')
        self.get_col_stats(GarminDB.Stress, GarminDB.Stress.stress, 'Stress', True)
        self.get_col_stats(GarminDB.RestingHeartRate, GarminDB.RestingHeartRate.resting_heart_rate, 'RHR', True)
        self.get_col_stats(GarminDB.Sleep, GarminDB.Sleep.total_sleep, 'Sleep', True, True)
        self.get_col_stats(GarminDB.Sleep, GarminDB.Sleep.rem_sleep, 'REM Sleep', True, True)

    def get_monitoring_years(self):
        logger.info("___Monitoring Records Coverage___")
        logger.info("This shows periods that data has been downloaded for.")
        logger.info("Not seeing data for days you know Garmin has data? Change the starting day and the number of days your passing to the dowloader.")
        years = GarminDB.Monitoring.get_years(self.garmin_mon_db)
        GarminDB.Summary.set(self.garmin_sum_db, 'Monitoring_Years', len(years))
        logger.info("Monitoring records: %d", GarminDB.Monitoring.row_count(self.garmin_mon_db))
        logger.info("Monitoring Years (%d): %s", len(years), str(years))
        total_days = 0
        for year in years:
            self.get_monitoring_months(year)
            total_days += self.get_monitoring_days(year)
        logger.info("Total monitoring days: %d", total_days)

    def get_monitoring_months(self, year):
        months = GarminDB.Monitoring.get_month_names(self.garmin_mon_db, year)
        GarminDB.Summary.set(self.garmin_sum_db, str(year) + '_months', len(months))
        logger.info("%s Months (%s): %s", year, len(months) , str(months))

    def get_monitoring_days(self, year):
        days = GarminDB.Monitoring.get_days(self.garmin_mon_db, year)
        days_count = len(days)
        if days_count > 0:
            first_day = days[0]
            last_day = days[-1]
            span = last_day - first_day + 1
        else:
            span = 0
        GarminDB.Summary.set(self.garmin_sum_db, str(year) + '_days', days_count)
        GarminDB.Summary.set(self.garmin_sum_db, str(year) + '_days_span', span)
        logger.info("%d Days (%d count vs %d span): %s", year, days_count, span, str(days))
        for index in xrange(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(Conversions.day_of_the_year_to_datetime(year, day))
                next_day_str = str(Conversions.day_of_the_year_to_datetime(year, next_day))
                logger.info("Days gap between %d (%s) and %d (%s)", day, day_str, next_day, next_day_str)
        return days_count

    def get_stats(self):
        self.get_files_stats()
        self.get_activities_stats()
        self.get_monitoring_stats()
        self.get_monitoring_years()

    def populate_hr_intensity(self, day_date, overwrite=False):
        if GarminDB.IntensityHR.row_count_for_day(self.garmin_sum_db, day_date) == 0 or overwrite:
            monitoring_rows = GarminDB.Monitoring.get_for_day(self.garmin_mon_db, GarminDB.Monitoring, day_date)
            previous_ts = None
            for monitoring in monitoring_rows:
                if monitoring.intensity is not None:
                    if previous_ts is not None:
                        hr_rows = GarminDB.MonitoringHeartRate.get_for_period(self.garmin_mon_db, GarminDB.MonitoringHeartRate, previous_ts, monitoring.timestamp)
                        for hr in hr_rows:
                            if hr.heart_rate > 0:
                                entry = {
                                    'timestamp'     : hr.timestamp,
                                    'intensity'     : monitoring.intensity,
                                    'heart_rate'    : hr.heart_rate
                                }
                                GarminDB.IntensityHR.create_or_update_not_none(self.garmin_sum_db, entry)
                    previous_ts = monitoring.timestamp + datetime.timedelta(0, 1)

    def combine_stats(self, stats, stat1_name, stat2_name):
        stat1 = stats.get(stat1_name, 0)
        stat2 = stats.get(stat2_name, 0)
        if stat1 is  None:
            return stat2
        if stat2 is  None:
            return stat1
        return stat1 + stat2

    def calculate_day_stats(self, day_date):
        self.populate_hr_intensity(day_date)
        stats = GarminDB.MonitoringHeartRate.get_daily_stats(self.garmin_mon_db, day_date)
        stats.update(GarminDB.RestingHeartRate.get_daily_stats(self.garmin_db, day_date))
        stats.update(GarminDB.IntensityHR.get_daily_stats(self.garmin_sum_db, day_date))
        stats.update(GarminDB.Weight.get_daily_stats(self.garmin_db, day_date))
        stats.update(GarminDB.Stress.get_daily_stats(self.garmin_db, day_date))
        stats.update(GarminDB.MonitoringClimb.get_daily_stats(self.garmin_mon_db, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_daily_stats(self.garmin_mon_db, day_date))
        stats.update(GarminDB.Monitoring.get_daily_stats(self.garmin_mon_db, day_date))
        stats.update(GarminDB.Sleep.get_daily_stats(self.garmin_db, day_date))
        stats.update(GarminDB.Stress.get_daily_stats(self.garmin_db, day_date))
        stats.update(GarminDB.MonitoringInfo.get_daily_stats(self.garmin_mon_db, day_date))
        stats.update(GarminDB.Activities.get_daily_stats(self.garmin_act_db, day_date))
        stats['calories_avg'] = self.combine_stats(stats, 'calories_bmr_avg', 'calories_active_avg')
        # calculate hr for inactive periods
        GarminDB.Monitoring.get_daily_stats(self.garmin_mon_db, day_date)
        # save it to the db
        GarminDB.DaysSummary.create_or_update_not_none(self.garmin_sum_db, stats)
        HealthDB.DaysSummary.create_or_update_not_none(self.sumdb, stats)

    def calculate_week_stats(self, day_date):
        stats = GarminDB.MonitoringHeartRate.get_weekly_stats(self.garmin_mon_db, day_date)
        stats.update(GarminDB.RestingHeartRate.get_weekly_stats(self.garmin_db, day_date))
        stats.update(GarminDB.IntensityHR.get_weekly_stats(self.garmin_sum_db, day_date))
        stats.update(GarminDB.Weight.get_weekly_stats(self.garmin_db, day_date))
        stats.update(GarminDB.Stress.get_weekly_stats(self.garmin_db, day_date))
        stats.update(GarminDB.MonitoringClimb.get_weekly_stats(self.garmin_mon_db, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_weekly_stats(self.garmin_mon_db, day_date))
        stats.update(GarminDB.Monitoring.get_weekly_stats(self.garmin_mon_db, day_date))
        stats.update(GarminDB.Sleep.get_weekly_stats(self.garmin_db, day_date))
        stats.update(GarminDB.Stress.get_weekly_stats(self.garmin_db, day_date))
        stats.update(GarminDB.MonitoringInfo.get_weekly_stats(self.garmin_mon_db, day_date))
        stats.update(GarminDB.Activities.get_weekly_stats(self.garmin_act_db, day_date))
        stats['calories_avg'] = self.combine_stats(stats, 'calories_bmr_avg', 'calories_active_avg')
        GarminDB.WeeksSummary.create_or_update_not_none(self.garmin_sum_db, stats)
        HealthDB.WeeksSummary.create_or_update_not_none(self.sumdb, stats)

    def calculate_month_stats(self, start_day_date, end_day_date):
        stats = GarminDB.MonitoringHeartRate.get_monthly_stats(self.garmin_mon_db, start_day_date, end_day_date)
        stats.update(GarminDB.RestingHeartRate.get_monthly_stats(self.garmin_db, start_day_date, end_day_date))
        stats.update(GarminDB.IntensityHR.get_monthly_stats(self.garmin_sum_db, start_day_date, end_day_date))
        stats.update(GarminDB.Weight.get_monthly_stats(self.garmin_db, start_day_date, end_day_date))
        stats.update(GarminDB.Stress.get_monthly_stats(self.garmin_db, start_day_date, end_day_date))
        stats.update(GarminDB.MonitoringClimb.get_monthly_stats(self.garmin_mon_db, start_day_date, end_day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_monthly_stats(self.garmin_mon_db, start_day_date, end_day_date))
        stats.update(GarminDB.Monitoring.get_monthly_stats(self.garmin_mon_db, start_day_date, end_day_date))
        stats.update(GarminDB.Sleep.get_monthly_stats(self.garmin_db, start_day_date, end_day_date))
        stats.update(GarminDB.Stress.get_monthly_stats(self.garmin_db, start_day_date, end_day_date))
        stats.update(GarminDB.MonitoringInfo.get_monthly_stats(self.garmin_mon_db, start_day_date, end_day_date))
        stats.update(GarminDB.Activities.get_monthly_stats(self.garmin_act_db, start_day_date, end_day_date))
        stats['calories_avg'] = self.combine_stats(stats, 'calories_bmr_avg', 'calories_active_avg')
        GarminDB.MonthsSummary.create_or_update_not_none(self.garmin_sum_db, stats)
        HealthDB.MonthsSummary.create_or_update_not_none(self.sumdb, stats)

    def summary(self):
        logger.info("___Summary Table Generation___")
        sleep_period_start = GarminDB.Attributes.get_time(self.garmin_db, 'sleep_time')
        sleep_period_stop = GarminDB.Attributes.get_time(self.garmin_db, 'wake_time')

        years = GarminDB.Monitoring.get_years(self.garmin_mon_db)
        for year in years:
            days = GarminDB.Monitoring.get_days(self.garmin_mon_db, year)
            for day in days:
                day_date = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                self.calculate_day_stats(day_date)

            for week_starting_day in xrange(1, 365, 7):
                day_date = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                self.calculate_week_stats(day_date)

            months = GarminDB.Monitoring.get_months(self.garmin_mon_db, year)
            for month in months:
                start_day_date = datetime.date(year, month, 1)
                end_day_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
                self.calculate_month_stats(start_day_date, end_day_date)

    def calculate_year(self, year):
        days = GarminDB.Monitoring.get_days(self.garmin_mon_db, year)
        for day in days:
            day_date = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
            self.calculate_day_stats(day_date)

        for week_starting_day in xrange(1, 365, 7):
            day_date = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
            self.calculate_week_stats(day_date)

        months = GarminDB.Monitoring.get_months(self.garmin_mon_db, year)
        for month in months:
            start_day_date = datetime.date(year, month, 1)
            end_day_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
            self.calculate_month_stats(start_day_date, end_day_date)

    def summary(self):
        logger.info("___Summary Table Generation___")
        sleep_period_start = GarminDB.Attributes.get_time(self.garmin_db, 'sleep_time')
        sleep_period_stop = GarminDB.Attributes.get_time(self.garmin_db, 'wake_time')

        years = GarminDB.Monitoring.get_years(self.garmin_mon_db)
        for year in years:
            self.calculate_year(year)


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
        analyze.get_stats()

    if summary:
        analyze.summary()

if __name__ == "__main__":
    main(sys.argv[1:])


