#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, string, logging, datetime, calendar

import HealthDB
import GarminDB


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
    def __init__(self, db_params_dict):
        self.garmindb = GarminDB.GarminDB(db_params_dict)
        self.mondb = GarminDB.MonitoringDB(db_params_dict)
        self.garminsumdb = GarminDB.GarminSummaryDB(db_params_dict)
        self.sumdb = HealthDB.SummaryDB(db_params_dict)
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict)
        units = GarminDB.Attributes.get(self.garmindb, 'dist_setting')
        self.english_units = (units == 'statute')

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
        self.report_sport(GarminDB.Activities.sub_sport, 'Treadmill')
        self.report_sport(GarminDB.Activities.sport, 'Stand_Up_Paddleboarding')
        self.report_sport(GarminDB.Activities.sport, 'Alpine_Skiing')

    def get_weight_stats(self):
        records = GarminDB.Weight.row_count(self.garmindb)
        logger.info("Weight records: %d" % records)
        GarminDB.Summary.set(self.garminsumdb, 'Weight_Records', records)
        max_weight = GarminDB.Weight.get_col_max(self.garmindb, GarminDB.Weight.weight)
        logger.info("Max weight: %f" % max_weight)
        GarminDB.Summary.set(self.garminsumdb, 'Max_Weight', max_weight)
        min_weight = GarminDB.Weight.get_col_min(self.garmindb, GarminDB.Weight.weight)
        logger.info("Min weight: %f" % min_weight)
        GarminDB.Summary.set(self.garminsumdb, 'Min_Weight', min_weight)
        avg_weight = GarminDB.Weight.get_col_avg(self.garmindb, GarminDB.Weight.weight)
        logger.info("Avg weight: %f" % avg_weight)
        GarminDB.Summary.set(self.garminsumdb, 'Avg_Weight', avg_weight)

    def get_stress_stats(self):
        records = GarminDB.Stress.row_count(self.garmindb)
        logger.info("Stress records: %d" % records)
        GarminDB.Summary.set(self.garminsumdb, 'Stress_Records', records)
        max_stress = GarminDB.Stress.get_col_max(self.garmindb, GarminDB.Stress.stress)
        logger.info("Max stress: %f" % max_stress)
        GarminDB.Summary.set(self.garminsumdb, 'Max_Stress', max_stress)
        min_stress = GarminDB.Stress.get_col_min(self.garmindb, GarminDB.Stress.stress)
        logger.info("Min stress: %f" % min_stress)
        GarminDB.Summary.set(self.garminsumdb, 'Min_Stress', min_stress)
        avg_stress = GarminDB.Stress.get_col_avg(self.garmindb, GarminDB.Stress.stress)
        logger.info("Avg stress: %f" % avg_stress)
        GarminDB.Summary.set(self.garminsumdb, 'Avg_Stress', avg_stress)

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
                day_str = str(HealthDB.day_of_the_year_to_datetime(year, day))
                next_day_str = str(HealthDB.day_of_the_year_to_datetime(year, next_day))
                logger.info("Days gap between %d (%s) and %d (%s)" % (day, day_str, next_day, next_day_str))

    base_awake_intensity = 3
    base_active_intensity = 10

    sleep_state = {
        0 : 'deep_sleep',
        1 : 'light_sleep',
        2 : 'light_sleep',
        3 : 'awake',
        4 : 'awake',
        5 : 'awake',
        6 : 'awake',
        7 : 'awake',
        8 : 'awake',
        9 : 'active',
        10 : 'active',
        11 : 'active',
        12 : 'moderately_active',
        13 : 'moderately_active',
        14 : 'moderately_active',
        15 : 'very_active',
        16 : 'very_active',
        17 : 'very_active',
        18 : 'extremely_active',
        18 : 'extremely_active',
        19 : 'extremely_active',
    }

    sleep_state_index = {
        'deep_sleep' : 0,
        'light_sleep' : 1,
        'awake' : 2,
        'active' : 3,
        'moderately_active' : 4,
        'very_active' : 5,
        'extremely_active' : 6
    }

    sleep_state_latch_time = {
        'deep_sleep' : 300,
        'light_sleep' : 120,
        'awake' : 60,
        'active' : 60,
        'moderately_active' : 60,
        'very_active' : 60,
        'extremely_active' : 60
    }

    def awake(self, sleep_state):
        return self.sleep_state_index[sleep_state] >= 2

    def asleep(self, sleep_state):
        return self.sleep_state_index[sleep_state] <= 1

    def sleep_state_change(self, sleep_state_ts, sleep_state, sleep_state_duration):
        GarminDB.Sleep.create_or_update(self.garminsumdb, {'timestamp' : sleep_state_ts, 'event' : sleep_state, 'duration' : sleep_state_duration})
        if self.bedtime_ts is None:
            if self.asleep(sleep_state) and self.mins_asleep >= 10:
                self.bedtime_ts = sleep_state_ts - datetime.timedelta(0, 1)
        elif self.awake(sleep_state) and self.mins_awake >= 30 and (sleep_state_ts - self.bedtime_ts).total_seconds() < 3600:
            self.bedtime_ts = None
            self.wake_ts = None
        elif self.wake_ts is None:
            if self.awake(sleep_state) and self.mins_awake >= 10:
                self.wake_ts = sleep_state_ts + datetime.timedelta(0, 1)
        elif self.asleep(sleep_state) and self.mins_asleep >= 30:
            self.wake_ts = None

    def calculate_sleep(self, day_date, sleep_period_start, sleep_period_stop):
        generic_act_id = GarminDB.ActivityType.get_id(self.mondb, 'generic')
        stop_act_id = GarminDB.ActivityType.get_id(self.mondb, 'stop_disable')

        sleep_search_start_ts = datetime.datetime.combine(day_date, sleep_period_start) - datetime.timedelta(0, 0, 0, 0, 0, 1)
        sleep_search_stop_ts = datetime.datetime.combine(day_date + datetime.timedelta(1), sleep_period_stop) + datetime.timedelta(0, 0, 0, 0, 0, 1)

        activity = GarminDB.Monitoring.get_activity(self.mondb, sleep_search_start_ts, sleep_search_stop_ts)

        initial_intensity = self.base_awake_intensity
        last_intensity = initial_intensity
        last_sample_ts = sleep_search_stop_ts
        activity_periods = []
        for index in xrange(len(activity) - 1, 0, -1):
            (timestamp, activity_type_id, intensity) = activity[index]
            duration = int((last_sample_ts - timestamp).total_seconds())
            if activity_type_id != stop_act_id:
                if intensity is None:
                    intensity = self.base_active_intensity
                else:
                    intensity = self.base_active_intensity + (intensity * 2)
            activity_periods.insert(0, (timestamp, last_intensity, duration))
            last_intensity = intensity
            last_sample_ts = timestamp

        self.bedtime_ts = None
        self.mins_asleep = 0
        self.wake_ts = None
        self.mins_awake = 0
        prev_sleep_state = self.sleep_state[initial_intensity]
        prev_sleep_state_ts = sleep_search_start_ts
        duration = None
        mov_avg_flt = MovingAverageFilter(0.85, initial_intensity)
        for period_index, (timestamp, intensity, duration) in enumerate(activity_periods):
            for sec_index in xrange(0, duration, 60):
                filtered_intensity = mov_avg_flt.filter(intensity)
                sleep_state = self.sleep_state[filtered_intensity]
                if self.awake(sleep_state):
                    self.mins_asleep = 0
                    self.mins_awake += 1
                else:
                    self.mins_asleep += 1
                    self.mins_awake = 0
                current_ts = timestamp + datetime.timedelta(0, sec_index)
                duration = int((current_ts - prev_sleep_state_ts).total_seconds())
                if sleep_state != prev_sleep_state and duration >= self.sleep_state_latch_time[prev_sleep_state]:
                    self.sleep_state_change(prev_sleep_state_ts, prev_sleep_state, duration)
                    prev_sleep_state = sleep_state
                    prev_sleep_state_ts = current_ts
        self.sleep_state_change(prev_sleep_state_ts, prev_sleep_state, duration)
        if self.bedtime_ts is not None:
            GarminDB.Sleep.create_or_update(self.garminsumdb, {'timestamp' : self.bedtime_ts, 'event' : 'bed_time', 'duration' : 1})
        if self.wake_ts is not None:
            GarminDB.Sleep.create_or_update(self.garminsumdb, {'timestamp' : self.wake_ts, 'event' : 'wake_time', 'duration' : 1})

    def calculate_resting_heartrate(self, day_date, sleep_period_stop):
        wake_ts = GarminDB.Sleep.get_wake_time(self.garminsumdb, day_date)
        if wake_ts is None:
            wake_ts = datetime.datetime.combine(day_date, sleep_period_stop)
        rhr = GarminDB.MonitoringHeartRate.get_resting_heartrate(self.mondb, wake_ts)
        if rhr:
            GarminDB.RestingHeartRate.create_or_update(self.garminsumdb, {'day' : day_date, 'resting_heart_rate' : rhr})
        else:
            logger.debug("No RHR for %s)" % str(day_date))

    def calculate_day_stats(self, day_date):
        stats = GarminDB.MonitoringHeartRate.get_daily_stats(self.mondb, day_date)
        stats.update(GarminDB.RestingHeartRate.get_daily_stats(self.garminsumdb, day_date))
        stats.update(GarminDB.Weight.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.Stress.get_daily_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringClimb.get_daily_stats(self.mondb, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_daily_stats(self.mondb, day_date))
        stats.update(GarminDB.Monitoring.get_daily_stats(self.mondb, day_date))
        GarminDB.DaysSummary.create_or_update_not_none(self.garminsumdb, stats)
        HealthDB.DaysSummary.create_or_update_not_none(self.sumdb, stats)

    def calculate_week_stats(self, day_date):
        stats = GarminDB.MonitoringHeartRate.get_weekly_stats(self.mondb, day_date)
        stats.update(GarminDB.RestingHeartRate.get_weekly_stats(self.garminsumdb, day_date))
        stats.update(GarminDB.Weight.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.Stress.get_weekly_stats(self.garmindb, day_date))
        stats.update(GarminDB.MonitoringClimb.get_weekly_stats(self.mondb, day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_weekly_stats(self.mondb, day_date))
        stats.update(GarminDB.Monitoring.get_weekly_stats(self.mondb, day_date))
        GarminDB.WeeksSummary.create_or_update_not_none(self.garminsumdb, stats)
        HealthDB.WeeksSummary.create_or_update_not_none(self.sumdb, stats)

    def calculate_month_stats(self, start_day_date, end_day_date):
        stats = GarminDB.MonitoringHeartRate.get_monthly_stats(self.mondb, start_day_date, end_day_date)
        stats.update(GarminDB.RestingHeartRate.get_monthly_stats(self.garminsumdb, start_day_date, end_day_date))
        stats.update(GarminDB.Weight.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.Stress.get_monthly_stats(self.garmindb, start_day_date, end_day_date))
        stats.update(GarminDB.MonitoringClimb.get_monthly_stats(self.mondb, start_day_date, end_day_date, self.english_units))
        stats.update(GarminDB.MonitoringIntensity.get_monthly_stats(self.mondb, start_day_date, end_day_date))
        stats.update(GarminDB.Monitoring.get_monthly_stats(self.mondb, start_day_date, end_day_date))
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
    summary = False
    debug = False
    db_params_dict = {}
    dates = False
    sleep_period_start = None
    sleep_period_stop = None

    try:
        opts, args = getopt.getopt(argv,"adi:tS:s:", ["analyze", "debug", "dates", "mysql=", "sleep=", "sqlite="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-a", "--analyze"):
            logging.debug("analyze: True")
            summary = True
        elif opt in ("-t", "--debug"):
            logging.debug("debug: True")
            debug = True
        elif opt in ("-d", "--dates"):
            logging.debug("Dates")
            dates = True
        elif opt in ("-S", "--sleep"):
            logging.debug("Sleep: " + arg)
            sleep_args = arg.split(',')
            sleep_period_start = datetime.datetime.strptime(sleep_args[0], "%H:%M").time()
            sleep_period_stop = datetime.datetime.strptime(sleep_args[1], "%H:%M").time()
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
    if dates:
        analyze.get_files_stats()
        analyze.get_weight_stats()
        analyze.get_stress_stats()
        analyze.get_activities_stats()
        analyze.get_monitoring_years()
    if summary:
        analyze.summary()

if __name__ == "__main__":
    main(sys.argv[1:])


