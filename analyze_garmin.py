"""Objects for analyzing health data from Garmin devices and genrating summary tables."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import logging
import datetime
import calendar
import progressbar

import Fit
import Fit.conversions
import HealthDB
import GarminDB


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
stat_logger = logging.getLogger('stats')
stat_logger.addHandler(logging.FileHandler('stats.txt', 'w'))


class Analyze(object):
    """Object for analyzing health data from Garmin devices."""

    def __init__(self, db_params_dict, debug):
        """Return an instance of the Analyze class."""
        self.garmin_db = GarminDB.GarminDB(db_params_dict, debug)
        self.garmin_mon_db = GarminDB.MonitoringDB(db_params_dict, debug)
        self.garmin_sum_db = GarminDB.GarminSummaryDB(db_params_dict, debug)
        self.sum_db = HealthDB.SummaryDB(db_params_dict, debug)
        self.garmin_act_db = GarminDB.ActivitiesDB(db_params_dict, debug)
        self.measurement_system = GarminDB.Attributes.measurements_type(self.garmin_db)
        self.unit_strings = Fit.units.unit_strings[self.measurement_system]

    def __save_summary_stat(self, name, value):
        GarminDB.Summary.set(self.garmin_sum_db, name, value)
        HealthDB.Summary.set(self.sum_db, name, value)

    def __report_file_type(self, file_type):
        records = GarminDB.File.row_count(self.garmin_db, GarminDB.File.type, file_type)
        if records > 0:
            stat_logger.info("%s files: %d", file_type, records)
            self.__save_summary_stat(file_type + '_files', records)

    def __get_files_stats(self):
        records = GarminDB.File.row_count(self.garmin_db)
        stat_logger.info("File records: %d" % records)
        self.__save_summary_stat('files', records)
        for file_type_name in [file_type.name for file_type in GarminDB.File.FileType]:
            self.__report_file_type(file_type_name)

    def __report_sport(self, sport_col, sport):
        Fit.units.unit_strings[self.measurement_system]
        records = GarminDB.Activities.row_count(self.garmin_act_db, sport_col, sport)
        if records > 0:
            sport_title = sport.title().replace('_', ' ')
            total_distance = GarminDB.Activities.get_col_sum_for_value(self.garmin_act_db, GarminDB.Activities.distance, sport_col, sport)
            if total_distance is None:
                total_distance = 0
                average_distance = 0
            else:
                average_distance = total_distance / records
            distance_units = self.unit_strings[Fit.units.UnitTypes.distance_long]
            stat_logger.info("%s activities: %d - total distance %d %s average distance %d %s",
                             sport_title, records, total_distance, distance_units, average_distance, distance_units)
            self.__save_summary_stat(sport + '_Activities', records)
            self.__save_summary_stat(sport + '_Miles', total_distance)

    def __get_activities_stats(self):
        stat_logger.info("___Activities Statistics___")
        activities = GarminDB.Activities.row_count(self.garmin_act_db)
        stat_logger.info("Total activities: %d", activities)
        self.__save_summary_stat('Activities', activities)
        laps = GarminDB.ActivityLaps.row_count(self.garmin_act_db)
        stat_logger.info("Activities lap records: %d", laps)
        self.__save_summary_stat('Activity_laps', laps)
        records = GarminDB.ActivityRecords.row_count(self.garmin_act_db)
        stat_logger.info("Activity records: %d", records)
        self.__save_summary_stat('Activity_records', records)
        years = GarminDB.Activities.get_years(self.garmin_act_db)
        stat_logger.info("Years with activities: %d: %s", len(years), years)
        self.__save_summary_stat('Activity_Years', len(years))
        fitness_activities = GarminDB.Activities.row_count(self.garmin_act_db, GarminDB.Activities.type, 'fitness')
        stat_logger.info("Fitness activities: %d", fitness_activities)
        self.__save_summary_stat('Fitness_activities', fitness_activities)
        recreation_activities = GarminDB.Activities.row_count(self.garmin_act_db, GarminDB.Activities.type, 'recreation')
        stat_logger.info("Recreation activities: %d", recreation_activities)
        self.__save_summary_stat('Recreation_activities', recreation_activities)
        sports = GarminDB.Activities.get_col_distinct(self.garmin_act_db, GarminDB.Activities.sport)
        stat_logger.info("Sports: %s", ', '.join(sports))
        sub_sports = GarminDB.Activities.get_col_distinct(self.garmin_act_db, GarminDB.Activities.sub_sport)
        stat_logger.info("SubSports: %s", ', '.join(sub_sports))
        for sport_name in [sport.name for sport in Fit.field_enums.Sport]:
            self.__report_sport(GarminDB.Activities.sport, sport_name)

    def __get_col_stats(self, table, col, name, ignore_le_zero=False, time_col=False):
        records = table.row_count(self.garmin_db)
        self.__save_summary_stat('%s_Records' % name, records)
        if time_col:
            maximum = table.get_time_col_max(self.garmin_db, col)
        else:
            maximum = table.get_col_max(self.garmin_db, col)
        self.__save_summary_stat('Max_%s' % name, maximum)
        if time_col:
            minimum = table.get_time_col_min(self.garmin_db, col)
        else:
            minimum = table.get_col_min(self.garmin_db, col, None, None, ignore_le_zero)
        self.__save_summary_stat('Min_%s' % name, minimum)
        if time_col:
            average = table.get_time_col_avg(self.garmin_db, col)
        else:
            average = table.get_col_avg(self.garmin_db, col, None, None, ignore_le_zero)
        self.__save_summary_stat('Avg_%s' % name, average)
        latest = table.get_col_latest(self.garmin_db, col)
        stat_logger.info("%s records: %s max: %s min: %s avg: %s latest: %s", name, records, maximum, minimum, average, latest)

    def __get_monitoring_stats(self):
        stat_logger.info("___Monitoring Statistics___")
        self.__get_col_stats(GarminDB.Weight, GarminDB.Weight.weight, 'Weight')
        self.__get_col_stats(GarminDB.Stress, GarminDB.Stress.stress, 'Stress', True)
        self.__get_col_stats(GarminDB.RestingHeartRate, GarminDB.RestingHeartRate.resting_heart_rate, 'RHR', True)
        self.__get_col_stats(GarminDB.Sleep, GarminDB.Sleep.total_sleep, 'Sleep', True, True)
        self.__get_col_stats(GarminDB.Sleep, GarminDB.Sleep.rem_sleep, 'REM Sleep', True, True)

    def __get_monitoring_days(self, year):
        days = GarminDB.Monitoring.get_days(self.garmin_mon_db, year)
        days_count = len(days)
        if days_count > 0:
            first_day = days[0]
            last_day = days[-1]
            span = last_day - first_day + 1
        else:
            span = 0
        self.__save_summary_stat(str(year) + '_days', days_count)
        self.__save_summary_stat(str(year) + '_days_span', span)
        stat_logger.info("%d Days with data (%d count vs %d span): %s", year, days_count, span, days)
        for index in xrange(days_count - 1):
            day = int(days[index])
            next_day = int(days[index + 1])
            if next_day != day + 1:
                day_str = str(Fit.conversions.day_of_the_year_to_datetime(year, day))
                next_day_str = str(Fit.conversions.day_of_the_year_to_datetime(year, next_day))
                stat_logger.info("Days gap between %d (%s) and %d (%s)", day, day_str, next_day, next_day_str)
        return days_count

    def __get_monitoring_months(self, year):
        months = GarminDB.Monitoring.get_month_names(self.garmin_mon_db, year)
        self.__save_summary_stat(str(year) + '_months', len(months))
        stat_logger.info("%s Months with data (%s): %s", year, len(months), months)

    def __get_monitoring_years(self):
        stat_logger.info("___Monitoring Records Coverage___")
        stat_logger.info("This shows periods that data has been downloaded for. "
                         "Not seeing data for days you know Garmin has data? "
                         "Change the starting day and the number of days in GarminConnectConfig.json and do a full download.")
        years = GarminDB.Monitoring.get_years(self.garmin_mon_db)
        self.__save_summary_stat('Monitoring_Years', len(years))
        stat_logger.info("Monitoring records: %d", GarminDB.Monitoring.row_count(self.garmin_mon_db))
        stat_logger.info("Monitoring Years with data (%d): %s", len(years), years)
        total_days = 0
        for year in years:
            self.__get_monitoring_months(year)
            total_days += self.__get_monitoring_days(year)
        stat_logger.info("Total days with monitoring data: %d", total_days)

    def get_stats(self):
        """Calculate summary statistics."""
        self.__get_files_stats()
        self.__get_activities_stats()
        self.__get_monitoring_stats()
        self.__get_monitoring_years()

    def __populate_hr_intensity(self, day_date, garmin_mon_session, garmin_sum_session, overwrite=False):
        if GarminDB.IntensityHR.s_row_count_for_day(garmin_sum_session, day_date) == 0 or overwrite:
            monitoring_rows = GarminDB.Monitoring._get_for_day(garmin_mon_session, day_date, not_none_col=GarminDB.Monitoring.intensity)
            previous_ts = None
            for monitoring in monitoring_rows:
                # Heart rate value is for one minute, reported at the end of the minute. Only take HR values where the
                # measurement period falls within the activity period.
                if previous_ts is not None and (monitoring.timestamp - previous_ts).total_seconds() > 60:
                    hr_rows = GarminDB.MonitoringHeartRate.s_get_for_period(garmin_mon_session, previous_ts, previous_ts + datetime.timedelta(seconds=60),
                                                                            not_none_col=monitoring.timestamp)
                    for hr in hr_rows:
                        entry = {
                            'timestamp'     : hr.timestamp,
                            'intensity'     : monitoring.intensity,
                            'heart_rate'    : hr.heart_rate
                        }
                        GarminDB.IntensityHR.s_create_or_update(garmin_sum_session, entry, ignore_none=True)
                previous_ts = monitoring.timestamp

    def __calculate_day_stats(self, day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        stats = GarminDB.DailySummary.get_daily_stats(garmin_session, day_date)
        # prefer getting stats from the daily summary.
        if stats.get('rhr_avg') is None:
            stats.update(GarminDB.RestingHeartRate.get_daily_stats(garmin_session, day_date))
        if stats.get('stress_avg') is None:
            stats.update(GarminDB.Stress.get_daily_stats(garmin_session, day_date))
        if stats.get('intensity_time') is None:
            stats.update(GarminDB.MonitoringIntensity.get_daily_stats(garmin_mon_session, day_date))
        if stats.get('floors') is None:
            stats.update(GarminDB.MonitoringClimb.get_daily_stats(garmin_mon_session, day_date, self.measurement_system))
        if stats.get('steps') is None:
            stats.update(GarminDB.Monitoring.get_daily_stats(garmin_mon_session, day_date))
        stats.update(GarminDB.MonitoringHeartRate.get_daily_stats(garmin_mon_session, day_date))
        stats.update(GarminDB.IntensityHR.get_daily_stats(garmin_sum_session, day_date))
        stats.update(GarminDB.Weight.get_daily_stats(garmin_session, day_date))
        stats.update(GarminDB.Sleep.get_daily_stats(garmin_session, day_date))
        stats.update(GarminDB.Activities.get_daily_stats(garmin_act_session, day_date))
        # save it to the db
        GarminDB.DaysSummary.s_create_or_update(garmin_sum_session, stats)
        HealthDB.DaysSummary.s_create_or_update(sum_session, stats)

    def __calculate_days(self, year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        days = GarminDB.Monitoring.s_get_days(garmin_mon_session, year)
        for day in progressbar.progressbar(days):
            day_date = datetime.date(year, 1, 1) + datetime.timedelta(day - 1)
            self.__populate_hr_intensity(day_date, garmin_mon_session, garmin_sum_session)
            self.__calculate_day_stats(day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def __calculate_week_stats(self, day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        stats = GarminDB.DailySummary.get_weekly_stats(garmin_session, day_date)
        # prefer getting stats from the daily summary.
        if stats.get('rhr_avg') is None:
            stats.update(GarminDB.RestingHeartRate.get_weekly_stats(garmin_session, day_date))
        if stats.get('stress_avg') is None:
            stats.update(GarminDB.Stress.get_weekly_stats(garmin_session, day_date))
        if stats.get('intensity_time') is None:
            stats.update(GarminDB.MonitoringIntensity.get_weekly_stats(garmin_mon_session, day_date))
        if stats.get('floors') is None:
            stats.update(GarminDB.MonitoringClimb.get_weekly_stats(garmin_mon_session, day_date, self.measurement_system))
        if stats.get('steps') is None:
            stats.update(GarminDB.Monitoring.get_weekly_stats(garmin_mon_session, day_date))
        stats.update(GarminDB.MonitoringHeartRate.get_weekly_stats(garmin_mon_session, day_date))
        stats.update(GarminDB.IntensityHR.get_weekly_stats(garmin_sum_session, day_date))
        stats.update(GarminDB.Weight.get_weekly_stats(garmin_session, day_date))
        stats.update(GarminDB.Sleep.get_weekly_stats(garmin_session, day_date))
        stats.update(GarminDB.Activities.get_weekly_stats(garmin_act_session, day_date))
        # save it to the db
        GarminDB.WeeksSummary.s_create_or_update(garmin_sum_session, stats)
        HealthDB.WeeksSummary.s_create_or_update(sum_session, stats)

    def __calculate_weeks(self, year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        for week_starting_day in progressbar.progressbar(xrange(1, 365, 7)):
            day_date = datetime.date(year, 1, 1) + datetime.timedelta(week_starting_day - 1)
            if day_date < datetime.datetime.now().date():
                self.__calculate_week_stats(day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def __calculate_month_stats(self, start_day_date, end_day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        stats = GarminDB.DailySummary.get_monthly_stats(garmin_session, start_day_date, end_day_date)
        # prefer getting stats from the daily summary.
        if stats.get('rhr_avg') is None:
            stats.update(GarminDB.RestingHeartRate.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        if stats.get('stress_avg') is None:
            stats.update(GarminDB.Stress.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        if stats.get('intensity_time') is None:
            stats.update(GarminDB.MonitoringIntensity.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date))
        if stats.get('floors') is None:
            stats.update(GarminDB.MonitoringClimb.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date, self.measurement_system))
        if stats.get('steps') is None:
            stats.update(GarminDB.Monitoring.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date))
        stats.update(GarminDB.MonitoringHeartRate.get_monthly_stats(garmin_mon_session, start_day_date, end_day_date))
        stats.update(GarminDB.IntensityHR.get_monthly_stats(garmin_sum_session, start_day_date, end_day_date))
        stats.update(GarminDB.Weight.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        stats.update(GarminDB.Sleep.get_monthly_stats(garmin_session, start_day_date, end_day_date))
        stats.update(GarminDB.Activities.get_monthly_stats(garmin_act_session, start_day_date, end_day_date))
        # save it to the db
        GarminDB.MonthsSummary.s_create_or_update(garmin_sum_session, stats)
        HealthDB.MonthsSummary.s_create_or_update(sum_session, stats)

    def __calculate_months(self, year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session):
        months = GarminDB.Monitoring._get_months(garmin_mon_session, year)
        for month in progressbar.progressbar(months):
            start_day_date = datetime.date(year, month, 1)
            end_day_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
            self.__calculate_month_stats(start_day_date, end_day_date, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def __calculate_year(self, year):
        with self.garmin_db.managed_session() as garmin_session:
            with self.garmin_mon_db.managed_session() as garmin_mon_session:
                with self.garmin_act_db.managed_session() as garmin_act_session:
                    with self.garmin_sum_db.managed_session() as garmin_sum_session:
                        with self.sum_db.managed_session() as sum_session:
                            self.__calculate_days(year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)
                            self.__calculate_weeks(year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)
                            self.__calculate_months(year, garmin_session, garmin_mon_session, garmin_act_session, garmin_sum_session, sum_session)

    def summary(self):
        """Summarize Garmin health data. Daily, weekly, and monthly, tables will be generated."""
        logger.info("___Summary Table Generation___")
        years = GarminDB.Monitoring.get_years(self.garmin_mon_db)
        for year in years:
            logger.info("Generating %s", year)
            self.__calculate_year(year)
