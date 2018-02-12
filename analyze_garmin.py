#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, calendar

import HealthDB
import GarminDB


root_logger = logging.getLogger()
logger = logging.getLogger(__file__)


class Analyze():


    def __init__(self, db_params_dict):
        self.garmindb = GarminDB.GarminDB(db_params_dict)
        self.mondb = GarminDB.MonitoringDB(db_params_dict)
        self.garminsumdb = GarminDB.GarminSummaryDB(db_params_dict)
        self.sumdb = HealthDB.SummaryDB(db_params_dict)
        units = GarminDB.Attributes.get(self.garmindb, 'units')
        if units == 'english':
            self.english_units = True
        else:
            self.english_units = False

    def set_sleep_period(self, sleep_period_start, sleep_period_stop):
        GarminDB.Attributes.set(self.garmindb, 'sleep_period_start', sleep_period_start)
        GarminDB.Attributes.set(self.garmindb, 'sleep_period_stop', sleep_period_stop)

    def get_years(self):
        years = GarminDB.Monitoring.get_years(self.mondb)
        GarminDB.Summary.set(self.garminsumdb, 'years', len(years))
        logger.info("Years (%d): %s" % (len(years), str(years)))

    def get_months(self, year):
        months = GarminDB.Monitoring.get_month_names(self.mondb, year)
        GarminDB.Summary.set(self.garminsumdb, year + '_months', len(months))
        logger.info("%s Months (%d): %s" % (year, len(months) , str(months)))

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
        logger.info("%d Days (%d vs %d): %s" % (year_int, days_count, span, str(days)))
        for index in xrange(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(HealthDB.day_of_the_year_to_datetime(year_int, day))
                next_day_str = str(HealthDB.day_of_the_year_to_datetime(year_int, next_day))
                logger.info("Days gap between %d (%s) and %d (%s)" % (day, day_str, next_day, next_day_str))

    sleep_state = {
        0 : {'level' : 0, 'name' : 'deep_sleep', 'threshold' : 900},
        1 : {'level' : 1, 'name' : 'light_sleep', 'threshold' : 300},
        2 : {'level' : 1, 'name' : 'light_sleep', 'threshold' : 450},
        3 : {'level' : 2, 'name' : 'awake', 'threshold' : 120},
        4 : {'level' : 2, 'name' : 'awake', 'threshold' : 60},
        5 : {'level' : 2, 'name' : 'awake', 'threshold' : 60},
        6 : {'level' : 2, 'name' : 'awake', 'threshold' : 60},
        7 : {'level' : 2, 'name' : 'awake', 'threshold' : 60},
    }

    def is_same_sleep_state(self, intensity1, intensity2):
        return self.sleep_state[intensity1]['level'] == self.sleep_state[intensity2]['level']

    def calculate_sleep(self, day_date, sleep_period_start, sleep_period_stop):
        stop_act_id = GarminDB.ActivityType.get_id(self.mondb, 'stop_disable')

        sleep_search_start_ts = datetime.datetime.combine(day_date, sleep_period_start) - datetime.timedelta(0, 0, 0, 0, 0, 2)
        next_day_date = day_date + datetime.timedelta(1)
        sleep_search_stop_ts = datetime.datetime.combine(next_day_date, sleep_period_stop) + datetime.timedelta(0, 0, 0, 0, 0, 2)
        activity = GarminDB.Monitoring.get_activity(self.mondb, sleep_search_start_ts, sleep_search_stop_ts)

        prev_intensity = 3
        prev_sleep_state = self.sleep_state[prev_intensity]['name']
        prev_sleep_state_ts = sleep_search_stop_ts
        for index in xrange(len(activity) - 1, 0, -1):
            (timestamp, activity_type_id, intensity) = activity[index]
            if activity_type_id != stop_act_id:
                #print "Activity: " + str(timestamp) + " was " + str(prev_intensity)
                intensity = 7
            sleep_state = self.sleep_state[intensity]['name']
            if sleep_state != prev_sleep_state:
                #print "Sleep state change: " + str(timestamp) + " : " + str(intensity)
                duration = (prev_sleep_state_ts - timestamp).total_seconds()
                if duration >= self.sleep_state[prev_intensity]['threshold']:
                    #print "Record: " + str(timestamp) + " : " + str(prev_intensity)
                    GarminDB.Sleep.create_or_update(self.garminsumdb, {'timestamp' : timestamp, 'event' : prev_sleep_state, 'duration' : duration})
                    prev_sleep_state = sleep_state
                    prev_sleep_state_ts = timestamp
                    prev_intensity = intensity
                else:
                    prev_intensity = round((intensity + prev_intensity) / 2)
                    #print "Average changed: " + str(prev_intensity)
            else:
                prev_intensity = round((intensity + prev_intensity) / 2)
                #print "Average same: " + str(prev_intensity)
        #sys.exit()

    def calculate_resting_heartrate(self, day_date, sleep_period_stop):
        start_ts = datetime.datetime.combine(day_date, sleep_period_stop)
        rhr = GarminDB.MonitoringHeartRate.get_resting_heartrate(self.mondb, start_ts)
        if rhr:
            GarminDB.RestingHeartRate.create_or_update(self.garminsumdb, {'day' : day_date, 'resting_heart_rate' : rhr})

    def calculate_day_stats(self, day_date):
        stats = GarminDB.MonitoringHeartRate.get_daily_stats(self.mondb, day_date)
        stats.update(GarminDB.RestingHeartRate.get_daily_stats(self.garminsumdb, day_date))
        stats.update(GarminDB.Weight.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.Stress.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringClimb.get_daily_stats(self.mondb, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensityMins.get_daily_stats(self.mondb, day_date))
        stats.update(GarminDB.Monitoring.get_daily_stats(self.mondb, day_date))
        GarminDB.DaysSummary.create_or_update(self.garminsumdb, stats)

    def calculate_week_stats(self, day_date):
        stats = GarminDB.MonitoringHeartRate.get_weekly_stats(self.mondb, day_date)
        stats.update(GarminDB.RestingHeartRate.get_weekly_stats(self.garminsumdb, day_date))
        stats.update(GarminDB.Weight.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.Stress.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringClimb.get_weekly_stats(self.mondb, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensityMins.get_weekly_stats(self.mondb, day_date))
        stats.update(GarminDB.Monitoring.get_weekly_stats(self.mondb, day_date))
        GarminDB.WeeksSummary.create_or_update(self.garminsumdb, stats)
        HealthDB.WeeksSummary.create_or_update(self.sumdb, stats)

    def calculate_month_stats(self, start_day_date, end_day_date):
        stats = GarminDB.MonitoringHeartRate.get_monthly_stats(self.mondb, start_day_date, end_day_date)
        stats.update(GarminDB.RestingHeartRate.get_monthly_stats(self.garminsumdb, start_day_date, end_day_date))
        stats.update(GarminDB.Weight.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.Stress.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.MonitoringClimb.get_monthly_stats(self.mondb, start_day_date, end_day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensityMins.get_monthly_stats(self.mondb, start_day_date, end_day_date))
        stats.update(GarminDB.Monitoring.get_monthly_stats(self.mondb, start_day_date, end_day_date))
        GarminDB.MonthsSummary.create_or_update(self.garminsumdb, stats)
        HealthDB.MonthsSummary.create_or_update(self.sumdb, stats)

    def summary(self):
        sleep_period_start = GarminDB.Attributes.get_time(self.garmindb, 'sleep_period_start')
        sleep_period_stop = GarminDB.Attributes.get_time(self.garmindb, 'sleep_period_stop')

        years = GarminDB.Monitoring.get_years(self.mondb)
        for year in years:
            days = GarminDB.Monitoring.get_days(self.mondb, year)
            for day in days:
                day_date = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
                self.calculate_sleep(day_date, sleep_period_start, sleep_period_stop)
                self.calculate_resting_heartrate(day_date, sleep_period_stop)
                self.calculate_day_stats(day_date)

            for week_starting_day in xrange(1, 365, 7):
                day_date = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
                self.calculate_week_stats(day_date)

            for month in xrange(1, 12):
                start_day_date = datetime.date(year, month, 1)
                end_day_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
                self.calculate_month_stats(start_day_date, end_day_date)

def usage(program):
    print '%s -s <sqlite db path> -m ...' % program
    sys.exit()

def main(argv):
    debug = False
    db_params_dict = {}
    years = False
    months = None
    days = None
    sleep_period_start = None
    sleep_period_stop = None

    try:
        opts, args = getopt.getopt(argv,"d:i:m:ts:y", ["debug", "days=", "months=", "mysql=", "years", "sleep=", "sqlite="])
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
        elif opt in ("-S", "--sleep"):
            logging.debug("Sleep: " + arg)
            sleep_args = arg.split(',')
            sleep_period_start = datetime.datetime.strptime(sleep_args[0], "%H:%M").time()
            sleep_period_stop = datetime.datetime.strptime(sleep_args[1], "%H:%M").time()
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
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    if len(db_params_dict) == 0:
        print "Missing arguments:"
        usage(sys.argv[0])

    analyze = Analyze(db_params_dict)
    if sleep_period_start and sleep_period_stop:
        analyze.set_sleep_period(sleep_period_start, sleep_period_stop)
    if years:
        analyze.get_years()
    if months:
        analyze.get_months(months)
    if days:
        analyze.get_days(days)
    analyze.summary()

if __name__ == "__main__":
    main(sys.argv[1:])


